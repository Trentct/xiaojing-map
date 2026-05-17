#!/usr/bin/env python3
"""
xiaojing-map: 一键生成书单地图 URL 的脚本

用法:
    python3 make-url.py --input /tmp/weread-export.json [选项]

工作流:
    1. 读取 Agent 拼好的 JSON
    2. LZ-string 压缩 + URL-safe base64 编码
    3. 拼接成 #weread=<encoded> fragment
    4. URL ≤ 70 KB → 输出链接(可选自动 open)
    5. URL > 70 KB → 降级:把 JSON 写到 ~/Downloads/,提示手动拖入

设计原则:
- 缺 lzstring 库时自动 pip install,无需用户提前装
- fragment 永远不发服务器,用户数据全程本地
- 支持本地 dev (http://localhost:3000) 和线上 (Vercel) 双端点
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ===== 默认配置 =====
DEFAULT_PROD_BASE_URL = "https://book-map-visualization.vercel.app"
DEFAULT_DEV_BASE_URL = "http://localhost:3000"
# Safari 在 ~80 KB 处会截断 URL,留余量
MAX_URL_LENGTH = 70_000


def ensure_lzstring() -> "lzstring.LZString":
    """缺 lzstring 时自动 pip install,然后 import。返回 LZString 实例。"""
    try:
        import lzstring  # type: ignore
    except ImportError:
        print("📦 首次运行需要安装 lzstring (压缩 URL 用),正在 pip install...", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "lzstring"],
        )
        import lzstring  # type: ignore
    return lzstring.LZString()


def encode_to_url(json_text: str, base_url: str) -> tuple[str, int]:
    """把 JSON 文本压缩 + 编码进 URL fragment,返回 (url, url_length)。"""
    lz = ensure_lzstring()
    # 必须用 EncodedURIComponent 模式,与网页端 LZString.decompressFromEncodedURIComponent 配对
    encoded = lz.compressToEncodedURIComponent(json_text)
    url = f"{base_url}/#weread={encoded}"
    return url, len(url)


def fallback_to_file(json_text: str, fallback_dir: Path) -> Path:
    """URL 过长时降级:写文件到 ~/Downloads/ 让用户手动拖入网页。"""
    fallback_dir.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    out_path = fallback_dir / f"weread-export-{timestamp}.json"
    out_path.write_text(json_text, encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="生成书单地图一键链接 (Agent → URL)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        type=Path,
        help="Agent 拼好的 JSON 文件路径",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=f"网页基础 URL,不传则用环境变量 BOOK_MAP_URL,或默认线上 {DEFAULT_PROD_BASE_URL}",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help=f"用本地 dev URL ({DEFAULT_DEV_BASE_URL}) 而不是线上",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="生成后用 macOS open / Linux xdg-open 直接在浏览器打开",
    )
    parser.add_argument(
        "--output-url-file",
        type=Path,
        default=None,
        help="把生成的 URL 也写到这个文件(stdout 之外的备份)",
    )
    parser.add_argument(
        "--fallback-dir",
        type=Path,
        default=Path.home() / "Downloads",
        help="URL 过长时的降级输出目录(默认 ~/Downloads)",
    )
    parser.add_argument(
        "--max-url-length",
        type=int,
        default=MAX_URL_LENGTH,
        help=f"超过此长度触发降级(默认 {MAX_URL_LENGTH} 字符)",
    )
    args = parser.parse_args()

    # 1. 读 JSON
    if not args.input.exists():
        print(f"❌ 输入文件不存在: {args.input}", file=sys.stderr)
        return 1
    json_text = args.input.read_text(encoding="utf-8")

    # 简单校验顶层结构
    try:
        data = json.loads(json_text)
        if not isinstance(data, dict) or not isinstance(data.get("books"), list):
            raise ValueError("JSON 顶层必须是 {books: [...]} 结构")
        book_count = len(data["books"])
    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ JSON 校验失败: {e}", file=sys.stderr)
        return 1

    # 2. 决定 base_url 优先级:--base-url > 环境变量 > --dev > 默认线上
    if args.base_url:
        base_url = args.base_url.rstrip("/")
    elif os.environ.get("BOOK_MAP_URL"):
        base_url = os.environ["BOOK_MAP_URL"].rstrip("/")
    elif args.dev:
        base_url = DEFAULT_DEV_BASE_URL
    else:
        base_url = DEFAULT_PROD_BASE_URL

    # 3. 编码
    url, url_len = encode_to_url(json_text, base_url)
    raw_size = len(json_text.encode("utf-8"))
    ratio = url_len / raw_size * 100 if raw_size else 0

    print(f"📊 数据统计", file=sys.stderr)
    print(f"   书目数: {book_count}", file=sys.stderr)
    print(f"   原始 JSON: {raw_size:,} bytes ({raw_size/1024:.1f} KB)", file=sys.stderr)
    print(f"   URL 长度:  {url_len:,} chars  ({url_len/1024:.1f} KB,压缩率 {ratio:.0f}%)", file=sys.stderr)
    print(f"   端点:      {base_url}", file=sys.stderr)
    print("", file=sys.stderr)

    # 4. 检查长度
    if url_len > args.max_url_length:
        print(
            f"⚠️  URL 长度 {url_len} 超过阈值 {args.max_url_length},降级到文件方式",
            file=sys.stderr,
        )
        out_path = fallback_to_file(json_text, args.fallback_dir)
        print(f"✅ JSON 已保存到: {out_path}", file=sys.stderr)
        print(
            f"请在 {base_url} 打开网页 → 档案导入 → 切到'微信读书 Agent' → 拖入此文件",
            file=sys.stderr,
        )
        print(str(out_path))  # stdout 输出文件路径(供 Agent 后续操作)
        return 0

    # 5. 写 URL 到备份文件(可选)
    if args.output_url_file:
        args.output_url_file.parent.mkdir(parents=True, exist_ok=True)
        args.output_url_file.write_text(url, encoding="utf-8")
        print(f"💾 URL 已保存到: {args.output_url_file}", file=sys.stderr)

    # 6. 自动打开浏览器(可选)
    if args.open:
        if sys.platform == "darwin":
            subprocess.run(["open", url], check=False)
            print("🌐 已用默认浏览器打开", file=sys.stderr)
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", url], check=False)
            print("🌐 已用默认浏览器打开", file=sys.stderr)
        else:
            print(f"⚠️  暂不支持自动打开浏览器 (platform={sys.platform})", file=sys.stderr)

    # 7. 输出 URL 到 stdout(Agent / 用户可直接复制)
    print(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
