import asyncio
import json
import sys
from itertools import count
from pathlib import Path
from typing import Any, Dict, Iterator

import aiofiles
import httpx


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "tieba"
OUTPUT_JSON = BASE_DIR / "o.json"
URL_TEMPLATE = "https://tb3.bdstatic.com/emoji/{name}@2x.png"
STOP_NUM = 140
REQUEST_TIMEOUT = 15


def log_info(*args: Any) -> None:
    print("[INFO]", *args, file=sys.stderr)


def log_warn(*args: Any) -> None:
    print("[WARN]", *args, file=sys.stderr)


def log_error(*args: Any) -> None:
    print("[ERROR]", *args, file=sys.stderr)


def iter_names() -> Iterator[str]:
    """依次生成无编号名称以及从 2 开始的编号名称。"""
    yield "image_emoticon"
    for index in count(2):
        yield f"image_emoticon{index}"


async def download_all(
    client: httpx.AsyncClient,
    result: Dict[str, Dict[str, str]],
) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name in iter_names():
        url = URL_TEMPLATE.format(name=name)
        log_info("start", name, url)

        try:
            response = await client.get(url)
        except httpx.TimeoutException:
            log_error("timeout", name, url)
            return 1
        except httpx.RequestError as error:
            log_error("request failed", name, url, ":", repr(error))
            return 1

        if str(STOP_NUM) in name:
            log_info("reached max, stop:", url)
            return 0
        # if response.status_code == 404:
        #     log_info("reached max, stop:", url)
        #     return 0

        if response.status_code != 200:
            log_error("download failed", name, url, "status=", response.status_code)
            continue

        out_path = OUTPUT_DIR / f"{name}.png"
        async with aiofiles.open(out_path, "wb") as file:
            await file.write(response.content)

        result[name] = {
            "desc": name,
            "url": f"/assets/tieba/{name}.webp",
        }
        log_info("ok", name)

    return 0


async def main() -> int:
    result: Dict[str, Dict[str, str]] = {}
    timeout = httpx.Timeout(REQUEST_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        exit_code = await download_all(client, result)

    async with aiofiles.open(OUTPUT_JSON, "w", encoding="utf8") as file:
        await file.write(json.dumps(result, ensure_ascii=False, indent=2))

    log_info("done. success:", len(result))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
