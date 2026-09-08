import asyncio
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_JSON = BASE_DIR / "info.json"
DEFAULT_OUTPUT_JSON = BASE_DIR / "douyin.json"
DEFAULT_STICKER_DIR = BASE_DIR / "static"
DEFAULT_CONCURRENCY = min(32, (os.cpu_count() or 1) * 4)


def log(level: str, *args: object) -> None:
    print(f"[{level}]", *args, file=sys.stderr)


def sticker_name(display_name: str) -> str:
    if not isinstance(display_name, str):
        raise ValueError("display_name must be a string")
    if not (display_name.startswith("[") and display_name.endswith("]")):
        raise ValueError(f"invalid display_name: {display_name!r}")

    name = display_name[1:-1].strip()
    if (
        not name
        or Path(name).name != name
        or any(char in name for char in '<>:"/\\|?*')
    ):
        raise ValueError(f"unsafe sticker name: {name!r}")
    return name


def prepare(
    data: dict[str, Any], sticker_dir: Path
) -> tuple[dict[str, dict[str, str]], dict[Path, list[Path]], list[str]]:
    stickers = data.get("stickers")
    if not isinstance(stickers, list):
        raise ValueError("input JSON must contain a 'stickers' list")

    index: dict[str, dict[str, str]] = {}
    jobs: dict[Path, list[Path]] = defaultdict(list)
    target_sources: dict[Path, Path] = {}
    target_names: dict[Path, str] = {}
    errors: list[str] = []

    for position, sticker in enumerate(stickers, start=1):
        try:
            uri = sticker["uri"]
            name = sticker_name(sticker["display_name"])
            description = sticker["show_name"]
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"invalid sticker at position {position}: {error}"
            ) from error

        if not all(isinstance(value, str) for value in (uri, description)):
            raise ValueError(
                f"invalid sticker at position {position}: fields must be strings"
            )

        source = sticker_dir / uri
        try:
            source.resolve(strict=False).relative_to(sticker_dir.resolve())
        except ValueError as error:
            raise ValueError(f"unsafe sticker uri: {uri!r}") from error
        target = sticker_dir / f"{name}{source.suffix.lower()}"
        previous_name = target_names.setdefault(target, name)
        if previous_name != name:
            errors.append(
                f"target name collision: {previous_name!r} and {name!r} "
                f"both resolve to {target.name!r} (source: {source.name})"
            )
            continue
        previous_source = target_sources.setdefault(target, source)
        if previous_source != source:
            errors.append(
                f"multiple sources map to {target.name!r}: "
                f"{previous_source.name}, {source.name}"
            )
            continue

        if target not in jobs[source]:
            jobs[source].append(target)
        index[name] = {
            "desc": description,
            "url": f"/assets/douyin/{name}.webp",
        }

    normalized_jobs = dict(jobs)
    source_paths = set(normalized_jobs)
    for source, targets in normalized_jobs.items():
        errors.extend(
            f"rename collision: {source.name} -> {target.name}; the target is also a source file"
            for target in targets
            if target != source and target in source_paths
        )
    return index, normalized_jobs, errors


def process_source(
    source: Path, targets: list[Path], keep_source: bool
) -> tuple[int, int]:
    missing_targets = [target for target in targets if not target.exists()]

    if not source.exists():
        if missing_targets:
            names = ", ".join(target.name for target in missing_targets)
            raise FileNotFoundError(
                f"{source.name}: source and target missing ({names})"
            )
        return 0, len(targets)

    copied = 0
    unchanged = 0
    for target in targets:
        if target == source:
            unchanged += 1
            continue
        shutil.copy2(source, target)
        copied += 1

    if not keep_source and source not in targets:
        source.unlink()
    return copied, unchanged


async def process_all(
    jobs: dict[Path, list[Path]], concurrency: int, keep_source: bool
) -> tuple[int, int, list[str], set[Path]]:
    semaphore = asyncio.Semaphore(concurrency)
    total = len(jobs)
    progress_step = max(1, total // 20)

    async def run_one(
        source: Path, targets: list[Path]
    ) -> tuple[int, int, Path, str | None]:
        async with semaphore:
            try:
                copied, unchanged = await asyncio.to_thread(
                    process_source, source, targets, keep_source
                )
                return copied, unchanged, source, None
            except OSError as error:
                message = f"{source}: {error}"
                return 0, 0, source, message

    copied = unchanged = completed = 0
    errors: list[str] = []
    failed_sources: set[Path] = set()
    tasks = [run_one(source, targets) for source, targets in jobs.items()]
    for task in asyncio.as_completed(tasks):
        item_copied, item_unchanged, source, error = await task
        copied += item_copied
        unchanged += item_unchanged
        completed += 1
        if error is not None:
            errors.append(error)
            failed_sources.add(source)
        if completed % progress_step == 0 or completed == total:
            percent = completed * 100 // total
            log("INFO", f"progress: {completed}/{total} ({percent}%) source files")
    return copied, unchanged, errors, failed_sources


async def read_json(path: Path) -> dict[str, Any]:
    content = await asyncio.to_thread(path.read_text, encoding="utf-8")
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("input JSON root must be an object")
    return data


async def write_json(path: Path, data: dict[str, Any]) -> None:
    content = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        await asyncio.to_thread(temporary.write_text, content, encoding="utf-8")
        await asyncio.to_thread(os.replace, temporary, path)
    finally:
        if temporary.exists():
            await asyncio.to_thread(temporary.unlink)


async def main() -> int:
    try:
        data = await read_json(DEFAULT_INPUT_JSON)
        index, jobs, preflight_errors = prepare(data, DEFAULT_STICKER_DIR)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        log("ERROR", error)
        return 1

    log("INFO", f"stickers: {len(index)}, source files: {len(jobs)}")
    copied, unchanged, errors, failed_sources = await process_all(
        jobs, DEFAULT_CONCURRENCY, keep_source=False
    )

    valid_names = {
        target.stem
        for source, targets in jobs.items()
        if source not in failed_sources
        for target in targets
        if target.exists()
    }
    index = {name: item for name, item in index.items() if name in valid_names}

    try:
        await write_json(DEFAULT_OUTPUT_JSON, index)
    except OSError as error:
        log("ERROR", f"cannot write {DEFAULT_OUTPUT_JSON}: {error}")
        return 1

    all_errors = preflight_errors + errors
    if all_errors:
        log("ERROR", f"index written with {len(all_errors)} problem(s) omitted")
        for error in all_errors:
            log("ERROR", "failed:", error)

    target_count = sum(len(targets) for targets in jobs.values())
    log(
        "INFO",
        f"done: {len(index)} indexed, {target_count} targets processed "
        f"(copied={copied}, unchanged={unchanged})",
    )
    return 0


asyncio.run(main())
