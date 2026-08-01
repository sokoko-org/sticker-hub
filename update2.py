import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

import httpx
import aiofiles


BASE_DIR = Path(__file__).resolve().parent
INPUT_JSON = BASE_DIR / "w.json"
OUTPUT_DIR = BASE_DIR / "weibo"
OUTPUT_JSON = BASE_DIR / "o.json"

MAX_CONCURRENCY = 16
REQUEST_TIMEOUT = 15
TOTAL_TIMEOUT = None


def log_info(*args: Any) -> None:
    print("[INFO]", *args, file=sys.stderr)


def log_warn(*args: Any) -> None:
    print("[WARN]", *args, file=sys.stderr)


def log_error(*args: Any) -> None:
    print("[ERROR]", *args, file=sys.stderr)


async def fetch_one(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    group: str,
    data: Dict[str, Any],
    result: Dict[str, Dict[str, str]],
) -> None:
    """下载单个微博表情并写入 result 索引。"""
    url = data.get("url")
    name = data["phrase"].lstrip("[").rstrip("]")

    if not url:
        log_warn("skip, no source:", name, data)
        return

    async with sem:
        try:
            log_info("start", name, url)
            resp = await client.get(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                log_warn("download failed", name, url, "status=", resp.status_code)
                return
            content = resp.content

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            out_path = OUTPUT_DIR / f"{name}.png"

            async with aiofiles.open(out_path, "wb") as f:
                await f.write(content)

            # desc: "{group}_{name}"
            # url:  "/assets/weibo/{name}.webp"
            desc = f"{group}_{name}"
            result[name] = {
                "desc": desc,
                "url": f"/assets/weibo/{name}.webp",
            }

            log_info("ok", name, desc)
        except httpx.TimeoutException:
            log_warn("timeout", name, url)
        except Exception as e:
            log_error("error", name, url, ":", repr(e))


async def main() -> None:
    if not INPUT_JSON.exists():
        log_error("w.json not found:", INPUT_JSON)
        return

    with INPUT_JSON.open(encoding="utf8") as f:
        data: Dict[str, Dict[str, Any]] = json.load(f)

    total = len(data)
    log_info("total faces:", total)

    result: Dict[str, Dict[str, str]] = {}
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    limits = httpx.Limits(
        max_connections=MAX_CONCURRENCY,
        max_keepalive_connections=MAX_CONCURRENCY,
    )
    timeout = httpx.Timeout(
        timeout=TOTAL_TIMEOUT,
        connect=REQUEST_TIMEOUT,
        read=REQUEST_TIMEOUT,
        write=REQUEST_TIMEOUT,
        pool=None,
    )

    async with httpx.AsyncClient(limits=limits, timeout=timeout, http2=True) as client:
        tasks = []
        for group, _list in data["data"].items():
            tasks.extend(fetch_one(client, sem, group, item, result) for item in _list)
        for coro in asyncio.as_completed(tasks):
            await coro

    async with aiofiles.open(OUTPUT_JSON, "w", encoding="utf8") as f:
        await f.write(json.dumps(result, ensure_ascii=False, indent=2))

    log_info("done. success:", len(result), "failed:", total - len(result))


if __name__ == "__main__":
    asyncio.run(main())
