# -*- coding: utf-8 -*-
"""
GitHub 推送监听 → 自动触发代码检查

用途：本机没有公网 IP / 内网穿透，GitHub Webhook 无法回调 localhost:8004，
因此用轮询 GitHub API 的方式实现"有人推送立即触发"：检测到分支 HEAD 变化，
就调用 Django 的 /api/codecheck/ 触发一次检查。

用法：
    python watch_push.py                       # 持续监听，默认 60s 一次
    python watch_push.py --interval 30         # 30s 一次
    python watch_push.py --once                # 只检查一次（用于自测）
    python watch_push.py --trigger-on-start    # 首次也立即触发（默认只记录 sha）

依赖：无第三方库（urllib）。Django 需处于运行状态（默认 http://localhost:8000）。
"""
import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = BASE_DIR / "data" / "watch_push_state.json"

DJANGO_BASE_URL = os.getenv("DJANGO_BASE_URL", "http://localhost:8000")
USERNAME = os.getenv("CODECHECK_USERNAME", "admin")
PASSWORD = os.getenv("CODECHECK_PASSWORD", "admin123")

DEFAULT_REPO = "Qiny-ops/Continue"
DEFAULT_BRANCH = "main"
DEFAULT_PROJECT_CODE = "mapp"


def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def _http_json(url: str, headers: dict | None = None, timeout: int = 30):
    req = urllib.request.Request(url, headers={
        "User-Agent": "aicheck-watch-push",
        "Accept": "application/json",
        **(headers or {}),
    })
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_remote_head(repo: str, branch: str) -> str:
    """取远端分支最新 commit sha（GitHub API，无需凭据，公开仓库即可）"""
    data = _http_json(f"https://api.github.com/repos/{repo}/commits/{branch}")
    return data.get("sha", "")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def login() -> str:
    """登录 Django 拿 JWT"""
    req = urllib.request.Request(
        f"{DJANGO_BASE_URL}/api/users/login/",
        data=json.dumps({"username": USERNAME, "password": PASSWORD}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return (data.get("data") or {}).get("token", "")


def trigger(token: str, project_code: str, repo: str, branch: str, sha: str, base_sha: str = "") -> dict:
    payload = {
        "project_code": project_code,
        "repository_url": f"https://github.com/{repo}.git",
        "branch": branch,
        "commit_sha": sha,
        "case_source": "platform",
        "trigger_source": "webhook",
    }
    # BUG-014：把"上一次看到的 HEAD"作为 base_sha 传入，让 diff 对比
    # last_sha..sha（覆盖 60s 内连推多 commit 的完整变更），而非空 diff。
    if base_sha and base_sha != sha:
        payload["base_sha"] = base_sha
    req = urllib.request.Request(
        f"{DJANGO_BASE_URL}/api/codecheck/",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="监听 GitHub 推送并触发代码检查")
    ap.add_argument("--repo", default=DEFAULT_REPO, help="owner/repo，默认 Qiny-ops/Continue")
    ap.add_argument("--branch", default=DEFAULT_BRANCH)
    ap.add_argument("--project-code", default=DEFAULT_PROJECT_CODE)
    ap.add_argument("--interval", type=int, default=60, help="轮询间隔（秒）")
    ap.add_argument("--once", action="store_true", help="只检查一次后退出")
    ap.add_argument("--trigger-on-start", action="store_true", help="首次运行也立即触发一次")
    args = ap.parse_args()

    _log(f"监听 {args.repo}@{args.branch} → 项目 {args.project_code}，间隔 {args.interval}s")

    state = load_state()
    key = f"{args.repo}@{args.branch}"
    last_sha = state.get(key, "")

    while True:
        try:
            sha = get_remote_head(args.repo, args.branch)
        except urllib.error.HTTPError as e:
            _log(f"获取远端 HEAD 失败: HTTP {e.code}")
        except Exception as e:
            _log(f"获取远端 HEAD 失败: {e}")
        else:
            if not sha:
                _log("未取到 sha，跳过本轮")
            elif not last_sha:
                _log(f"记录初始 sha={sha[:8]}")
                state[key] = sha
                save_state(state)
                last_sha = sha
                if args.trigger_on_start:
                    _log("首次运行触发一次")
                    try:
                        token = login()
                        r = trigger(token, args.project_code, args.repo, args.branch, sha)
                        _log(f"已触发 task id={r.get('id')} status={r.get('status')}")
                    except Exception as e:
                        _log(f"触发失败: {e}")
            elif sha != last_sha:
                _log(f"检测到新提交 {last_sha[:8]} → {sha[:8]}，触发检查")
                try:
                    token = login()
                    r = trigger(token, args.project_code, args.repo, args.branch, sha, base_sha=last_sha)
                    _log(f"已触发 task id={r.get('id')} status={r.get('status')}")
                    state[key] = sha
                    save_state(state)
                    last_sha = sha
                except Exception as e:
                    _log(f"触发失败，sha 暂不更新: {e}")
            else:
                _log(f"无变化（sha={sha[:8]}）")

        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
