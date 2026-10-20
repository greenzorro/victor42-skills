"""
File: wechat_article_video_dl.py
Project: toolkit
Created: 2026-10-14
Author: Victor Cheng
Email: hi@victor42.work
Description: 下载微信公众号文章内嵌的视频（mpvideo / wxv_* 类型）
"""

import os
import sys
import re
import time
import json
import argparse
import subprocess
import urllib.request
import urllib.error

current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(current_dir))

from utils.basic import get_param_value, sanitize_file_name_string
from utils.path import PATH_DOWNLOADS

UA_PC = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
UA_WX = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.40(0x18002824) "
    "NetType/WIFI Language/zh_CN"
)
REFERER = "https://mp.weixin.qq.com/"

# 风控退避节奏：第 n 次失败后等待秒数
RETRY_DELAYS = [2, 5, 10, 20, 30]

# 单个 format 对象：format_id 后依次跟 width / height / filesize / url / 清晰度中文
FORMAT_RE = re.compile(
    r"format_id:\s*'(\d+)'.*?width:\s*'(\d+)'.*?height:\s*'(\d+)'.*?"
    r"filesize:\s*'(\d+)'.*?url:\s*'([^']+)'.*?"
    r"video_quality_wording:\s*'([^']*)'",
    re.S,
)


def http_get(url, headers=None, timeout=30):
    """标准库 GET，返回 (status, bytes)"""
    h = {"User-Agent": UA_PC, "Referer": REFERER}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def unescape_url(url):
    """HTML 实体 / JS 转义还原为可直接请求的 URL"""
    url = url.replace("\\x26amp;", "&").replace("\\x26", "&").replace("&amp;", "&")
    url = url.replace("\\/", "/")
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    return url


def parse_article(html):
    """从文章 HTML 提取视频与清晰度；返回 (videos, snaps)

    videos: [{"vid": "wxv_...", "formats": [{format_id,width,height,filesize,url,wording}]}]
    snaps:  [视频号 export_id]，本工具不处理，仅提示
    """
    videos = []
    for part in re.split(r"video_id:\s*'", html)[1:]:
        vid = part.split("'", 1)[0]
        if not vid.startswith("wxv_"):
            continue
        formats = []
        for m in FORMAT_RE.finditer(part):
            fid, w, h, size, url, wording = m.groups()
            formats.append({
                "format_id": fid,
                "width": int(w),
                "height": int(h),
                "filesize": int(size),
                "url": unescape_url(url),
                "wording": wording,
            })
        if formats:
            videos.append({"vid": vid, "formats": formats})
    snaps = list(dict.fromkeys(re.findall(r"export/[A-Za-z0-9_\-]{20,}", html)))
    return videos, snaps


def article_ids(html):
    """取 __biz / mid / idx，用于查询视频标题"""
    def grab(pattern):
        m = re.search(pattern, html)
        return m.group(1) if m else ""
    return grab(r'var biz = "([^"]+)"'), grab(r'var mid = "?(\d+)'), grab(r'var idx = "?(\d+)')


def fetch_title(biz, mid, idx, vid):
    """通过取流元数据接口拿视频标题；失败返回空串"""
    if not (biz and mid and idx):
        return ""
    url = (
        "https://mp.weixin.qq.com/mp/videoplayer?action=get_mp_video_play_url"
        "&preview=0&__biz={}&mid={}&idx={}&vid={}&is_need_ticket=0&is_need_ad=0"
        "&comment_id=&is_need_reward=0&both_ad=0&reward_uin_count=0&send_time="
        "&msg_daily_idx=1&is_original=0&is_only_read=0&req_id=&pass_ticket="
        "&is_low_change=1"
    ).format(biz, mid, idx, vid)
    status, body = http_get(url, headers={"User-Agent": UA_WX})
    if status != 200:
        return ""
    try:
        return (json.loads(body).get("video_title") or "").strip()
    except (ValueError, AttributeError):
        return ""


def _remove_quietly(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def download_with_curl(url, path):
    """用系统 curl 下载 mpvideo CDN 资源（Python 标准库 TLS 会被风控判为机器人）

    先落地 ASCII 临时名再改名为最终名：Windows 的 curl.exe 经 CRT 用系统 ANSI
    代码页转换命令行参数，直接把中文目标路径交给 -o 会被劣化成 '?'。
    """
    out_dir = os.path.dirname(os.path.abspath(path)) or os.getcwd()
    tmp_name = ".wechat_video_dl_%d_%d.part" % (os.getpid(), int(time.time() * 1000))
    tmp_path = os.path.join(out_dir, tmp_name)
    cmd = [
        "curl", "-sS", "-L", "-r", "0-", "-o", tmp_name,
        "-H", "referer: " + REFERER,
        "-H", "user-agent: " + UA_PC,
        "-H", "accept-encoding: identity;q=1, *;q=0",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=out_dir)
    if proc.returncode != 0:
        _remove_quietly(tmp_path)
        return 0, (proc.stderr or "").strip()
    if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
        _remove_quietly(tmp_path)
        return 0, "empty response"
    size = os.path.getsize(tmp_path)
    os.replace(tmp_path, path)
    return size, ""


def ensure_curl():
    """确认系统 curl 可用（Windows 10 1803+ 起自带 curl.exe）"""
    try:
        proc = subprocess.run(["curl", "--version"], capture_output=True, text=True)
    except OSError:
        proc = None
    if proc is not None and proc.returncode == 0:
        return True
    print("错误：未找到可用的 curl。macOS / Linux / Windows 10(1803+) 均自带 curl；"
          "若缺失请先安装（Windows 可在「设置 → 应用 → 可选功能」中添加，"
          "或使用 Git for Windows 自带的 curl）。")
    return False


def download_with_retry(url, path):
    """带退避重试下载；返回 (字节数, 错误信息)"""
    for attempt, delay in enumerate([0] + RETRY_DELAYS, 1):
        if delay:
            time.sleep(delay)
        size, err = download_with_curl(url, path)
        if size:
            return size, ""
        print(f"    重试 {attempt}/{len(RETRY_DELAYS) + 1}（{err or '失败'}）", file=sys.stderr)
    return 0, "download failed"


def process(source, output, quality, list_only):
    print(f"正在获取文章：{source}")
    status, body = http_get(source)
    if status != 200:
        print(f"错误：文章获取失败（HTTP {status}）")
        return
    html = body.decode("utf-8", "ignore")

    videos, snaps = parse_article(html)
    print(f"发现 {len(videos)} 个可下载视频，{len(snaps)} 个视频号视频（不支持）")
    if not videos:
        return

    biz, mid, idx = article_ids(html)
    os.makedirs(output, exist_ok=True)

    for i, video in enumerate(videos, 1):
        formats = sorted(video["formats"], key=lambda f: (f["height"], f["filesize"]), reverse=True)
        title = fetch_title(biz, mid, idx, video["vid"])
        print(f"\n[{i}] {video['vid']}  {title or '(无标题)'}")
        for f in formats:
            print(f"      f{f['format_id']:<6} {f['width']}x{f['height']:<5} "
                  f"{f['filesize'] / 1048576:6.2f}MB  {f['wording']}")
        if list_only:
            continue

        chosen = formats if quality == "all" else formats[:1]
        for f in chosen:
            name = sanitize_file_name_string(title) if title else video["vid"]
            suffix = f"-f{f['format_id']}" if quality == "all" else ""
            path = os.path.join(output, f"{i} {name}{suffix}.mp4")
            print(f"  -> {path}")
            size, err = download_with_retry(f["url"], path)
            print(f"     {'完成 ' + str(size) + ' 字节' if size else '失败：' + err}")
            # 轻量限速，避免触发风控
            time.sleep(1)

    if snaps:
        print(f"\n注意：跳过 {len(snaps)} 个视频号视频（需 finder/登录链路，本工具不支持）：")
        for s in snaps:
            print(f"      {s}")


def main():
    parser = argparse.ArgumentParser(description="下载微信公众号文章内嵌的视频")
    parser.add_argument("--source", "-s", help="微信公众号文章 URL")
    parser.add_argument("--output", "-o",
                        help="输出目录（默认：系统下载目录下的 WeChatVideos）")
    parser.add_argument("--quality", "-q", choices=["best", "all"], help="下载清晰度，默认 best")
    parser.add_argument("--list", "--dry-run", dest="list_only", action="store_true",
                        help="只列出视频与清晰度，不下载")
    args = parser.parse_args()

    source = get_param_value(args, "source", prompt_text="请输入微信公众号文章 URL")
    default_output = os.path.join(PATH_DOWNLOADS, "WeChatVideos")
    output = get_param_value(args, "output", script_default=default_output)
    quality = get_param_value(args, "quality", script_default="best")
    list_only = bool(args.list_only)

    if not source:
        print("错误：未提供文章 URL")
        return
    if not ensure_curl():
        return
    process(source, output, quality, list_only)


if __name__ == "__main__":
    main()
