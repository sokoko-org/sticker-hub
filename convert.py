from pathlib import Path
import subprocess
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

CWEBP = r".\cwebp.exe"
GIF2WEBP = r".\gif2webp.exe"


def convert_png(src: Path, dst: Path):
    cmd = [
        CWEBP,
        "-lossless",
        "-q", "100",
        "-z", "9",
        "-m", "6",
        "-exact",
        str(src),
        "-o", str(dst),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode == 0, res.stderr.strip()


def convert_gif(src: Path, dst: Path):
    cmd = [
        GIF2WEBP,
        "-lossless",
        "-q", "100",
        "-m", "6",
        "-min_size",
        "-kmin", "0",
        "-kmax", "1",
        str(src),
        "-o", str(dst),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.returncode == 0, res.stderr.strip()


def process_one(path_str: str):
    """
    返回值: (状态码, 打印信息, 错误详情)
    状态码: 1=成功, 0=跳过, -1=失败/异常
    """
    path = Path(path_str)
    dst = path.with_suffix(".webp")

    if dst.exists():
        return 0, f"[跳过] {dst.name}", "目标 WebP 文件已存在"

    err_msg = ""
    if path.suffix.lower() == ".png":
        ok, err_msg = convert_png(path, dst)
    elif path.suffix.lower() == ".gif":
        ok, err_msg = convert_gif(path, dst)
    else:
        return -1, f"[不符合] {path.name}", "不支持的文件格式"

    if not ok:
        if dst.exists():
            dst.unlink()
        reason = err_msg if err_msg else "exe 转换失败(返回码非0)"
        return -1, f"[失败] {path.name}", reason

    old_size = path.stat().st_size
    new_size = dst.stat().st_size
    info = f"[完成] {path.name} {old_size/1024:.1f}KB -> {new_size/1024:.1f}KB"

    path.unlink()
    return 1, info, ""


def process_images(target):
    root = Path(target.strip('"'))

    if not root.exists():
        print("路径不存在")
        return

    all_files = [
        str(p) for p in root.rglob("*") 
        if p.suffix.lower() in (".png", ".gif")
    ]

    total_files = len(all_files)
    if total_files == 0:
        print("没有找到需要转换的 PNG 或 GIF 图片")
        return

    print(f"找到 {total_files} 张图片，正在处理...")

    success = 0
    
    skipped_details = {}
    failed_details = {}

    max_workers = os.cpu_count()
    print(f"并行线程/进程数: {max_workers}\n")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one, f): f for f in all_files}
        
        for future in as_completed(futures):
            orig_path = Path(futures[future]) 
            try:
                status, message, reason = future.result()
                if message:
                    print(message)
                
                if status == 1:
                    success += 1
                elif status == 0:
                    skipped_details[orig_path.name] = reason
                else:
                    failed_details[orig_path.name] = reason
            except Exception as e:
                print(f"[异常] {orig_path.name}: {e}")
                failed_details[orig_path.name] = f"Python 进程异常: {e}"

    print("\n" + "="*30)
    print(" 转换任务结束汇总报告")
    print("="*30)
    print(f"总计找到文件: {total_files} 个")
    print(f"成功转换并删除: {success} 个")
    print(f"跳过处理文件: {len(skipped_details)} 个")
    print(f"失败/异常文件: {len(failed_details)} 个")
    
    if skipped_details:
        print("\n【已跳过文件清单】")
        for file, reason in skipped_details.items():
            print(f"  - {file} ({reason})")

    if failed_details:
        print("\n【失败/异常详细清单】")
        for file, reason in failed_details.items():
            print(f"  - 文件: {file}")
            indented_reason = "\n".join([f"    {line}" for line in reason.splitlines()])
            print(f"    原因:\n{indented_reason}")
    
    print("="*30)


if __name__ == "__main__":
    while True:
        print("\n输入目录(q退出):")
        x = input("> ").strip()

        if x.lower() == "q":
            break

        if x:
            process_images(x)
