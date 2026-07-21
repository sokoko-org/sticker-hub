from pathlib import Path
import subprocess
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
import os


def resolve_encoder(name: str) -> str:
    """
    解析编码器路径：
    1. 优先检查当前目录下是否存在带 .exe（Windows）或不带后缀（Unix-like）的文件
    2. 其次在系统环境变量 PATH 中查找
    """
    local_bin = (
        Path(__file__).parent / f"{name}.exe"
        if os.name == "nt"
        else Path(__file__).parent / name
    )
    if local_bin.exists():
        return str(local_bin.resolve())

    if system_bin := shutil.which(name):
        return system_bin

    raise FileNotFoundError(
        f"\n未找到编码器 '{name}'！\n"
        f"请确保该工具已放置在当前脚本目录下，或已配置到系统PATH中\n"
        f"下载地址: https://developers.google.com/speed/webp/docs/precompiled"
    )


try:
    CWEBP = resolve_encoder("cwebp")
    GIF2WEBP = resolve_encoder("gif2webp")
except FileNotFoundError as e:
    print(e)
    exit(1)

# 单张图片处理的最大容忍时间（秒）
ENCODE_TIMEOUT = 60


def convert_png(src: Path, dst: Path):
    cmd = [
        CWEBP,
        "-lossless",
        "-q",
        "100",
        "-z",
        "9",
        "-m",
        "6",
        "-exact",
        str(src),
        "-o",
        str(dst),
    ]
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="backslashreplace",
            timeout=ENCODE_TIMEOUT,
        )
        return res.returncode == 0, res.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, f"转换超时：超过了 {ENCODE_TIMEOUT} 秒未响应，可能文件已损坏"


def convert_gif(src: Path, dst: Path):
    cmd = [
        GIF2WEBP,
        "-q",
        "100",
        "-mt",
        "-min_size",
        str(src),
        "-o",
        str(dst),
    ]
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="backslashreplace",
            timeout=ENCODE_TIMEOUT,
        )
        return res.returncode == 0, res.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, f"转换超时：超过了 {ENCODE_TIMEOUT} 秒未响应，可能文件已损坏"


def process_one(path_str: str, root_str: str):
    """
    接收字符串路径以适配多进程
    返回值: (状态码, 相对路径字符串, 打印信息, 错误详情)
    状态码: 1=成功, 0=跳过, -1=失败/异常
    """
    path = Path(path_str)
    root = Path(root_str)

    try:
        rel_path = str(path.relative_to(root))
    except ValueError:
        rel_path = path.name

    dst = path.with_suffix(".webp")

    if dst.exists():
        return 0, rel_path, f"[跳过] {rel_path}", "目标 WebP 文件已存在"

    err_msg = ""
    if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        ok, err_msg = convert_png(path, dst)
    elif path.suffix.lower() == ".gif":
        ok, err_msg = convert_gif(path, dst)
    else:
        return -1, rel_path, f"[不符合] {rel_path}", "不支持的文件格式"

    if not ok:
        if dst.exists():
            dst.unlink()
        reason = err_msg or "exe 转换失败(返回码非0)"
        return -1, rel_path, f"[失败] {rel_path}", reason

    old_size = path.stat().st_size
    new_size = dst.stat().st_size
    info = f"[完成] {rel_path} {old_size / 1024:.1f}KB -> {new_size / 1024:.1f}KB"

    path.unlink()
    return 1, rel_path, info, ""


def process_images(target):
    root = Path(target.strip().strip('"'))

    if not root.exists():
        print("路径不存在")
        return

    all_files = [
        str(p)
        for p in root.rglob("*")
        if p.suffix.lower() in (".png", ".gif", ".jpg", ".jpeg")
    ]

    total_files = len(all_files)
    if total_files == 0:
        print("没有找到需要转换的 PNG 或 GIF 图片")
        return

    print(f"\n找到 {total_files} 张图片，正在处理...")

    success = 0
    skipped_details = {}
    failed_details = {}

    max_workers = os.cpu_count()
    print(f"并行线程/进程数: {max_workers}\n")

    root_str = str(root)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one, f, root_str): f for f in all_files}

        for future in as_completed(futures):
            orig_file_path = futures[future]
            try:
                status, rel_key, message, reason = future.result()
                if message:
                    print(message)

                if status == 1:
                    success += 1
                elif status == 0:
                    skipped_details[rel_key] = reason
                else:
                    failed_details[rel_key] = reason
            except Exception as e:
                fallback_key = os.path.basename(orig_file_path)
                print(f"[异常] {fallback_key}: {e}")
                failed_details[fallback_key] = f"Python err: {e}"

    print("\n" + "=" * 40)
    print(f"总计找到文件: {total_files} 个")
    print(f"成功转换并删除: {success} 个")
    print(f"跳过处理文件: {len(skipped_details)} 个")
    print(f"失败/超时文件: {len(failed_details)} 个")

    if skipped_details:
        print("\n【已跳过文件清单】")
        for rel_file, reason in skipped_details.items():
            print(f"  - {rel_file} ({reason})")

    if failed_details:
        print("\n【失败/异常详细清单】")
        for rel_file, reason in failed_details.items():
            print(f"  - 路径: {rel_file}")
            indented_reason = "\n".join([f"    {line}" for line in reason.splitlines()])
            print(f"    原因:\n{indented_reason}")

    print("=" * 40)


if __name__ == "__main__":
    print(f"检测到环境：cwebp -> {CWEBP}")
    print(f"检测到环境：gif2webp -> {GIF2WEBP}")

    while True:
        print("\n输入目录(q退出):")
        x = input("> ").strip()

        if x.lower() == "q":
            break

        if x:
            process_images(x)
