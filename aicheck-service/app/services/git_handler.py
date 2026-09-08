# -*- coding: utf-8 -*-
"""
Git 操作（移植自 checker/git_handler.py，async 化）

差异点：
- subprocess → asyncio.create_subprocess_exec（Windows ProactorEventLoop 兼容）
- clone_or_pull 支持指定 branch（clone -b / checkout）
- get_diff 支持 before/after sha（webhook 场景），缺省时回退 HEAD@{1}
"""
import asyncio
import os
import re
from typing import Optional, Tuple

from app.config import settings


class GitError(RuntimeError):
    pass


def _safe_path(base: str, name: str) -> str:
    """workspace 子目录名安全化"""
    safe = re.sub(r"[^A-Za-z0-9_.\-]+", "_", name).strip("_") or "repo"
    return os.path.join(base, safe)


def _extract_dir_from_url(url: str) -> str:
    m = re.search(r"/([^/]+?)(?:\.git)?/?$", url.rstrip("/"))
    if m:
        return m.group(1)
    return "repo"


def _parse_stat(s: str) -> Tuple[int, int]:
    adds = dels = 0
    m = re.search(r"(\d+)\s+insertion", s)
    if m:
        adds = int(m.group(1))
    m = re.search(r"(\d+)\s+deletion", s)
    if m:
        dels = int(m.group(1))
    return adds, dels


async def _run(cmd: list, cwd: str) -> str:
    """异步执行 git 命令；失败抛 GitError"""
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=settings.timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise GitError(f"git 命令超时: {' '.join(cmd)}")
    if proc.returncode != 0:
        raise GitError(f"git 命令失败: {' '.join(cmd)}\n{stderr.decode('utf-8', 'ignore')}")
    return stdout.decode("utf-8", "ignore")


class GitHandler:
    def __init__(self):
        os.makedirs(settings.workspaces_dir, exist_ok=True)

    def project_path(self, project_name: str) -> str:
        return _safe_path(settings.workspaces_dir, project_name)

    async def clone_or_pull(
        self, repository_url: str, project_name: str, branch: Optional[str] = None
    ) -> str:
        path = self.project_path(project_name)
        if os.path.exists(os.path.join(path, ".git")):
            await _run(["git", "reset", "--hard", "HEAD"], path)
            await _run(["git", "clean", "-fd"], path)
            await _run(["git", "fetch", "--all", "--prune"], path)
            if branch:
                try:
                    await _run(["git", "checkout", branch], path)
                except GitError:
                    await _run(
                        ["git", "checkout", "-B", branch, f"origin/{branch}"], path
                    )
            await _run(["git", "pull", "--ff-only"], path)
        else:
            parent = settings.workspaces_dir
            os.makedirs(parent, exist_ok=True)
            target = path
            cmd = ["git", "clone"]
            if branch:
                cmd += ["-b", branch]
            cmd += [repository_url, os.path.basename(target)]
            await _run(cmd, parent)
        return path

    async def checkout_commit(self, project_path: str, commit_sha: str) -> None:
        await _run(["git", "checkout", commit_sha], project_path)

    async def get_diff(
        self,
        project_path: str,
        before: Optional[str] = None,
        after: Optional[str] = None,
    ) -> dict:
        head = (await _run(["git", "rev-parse", "HEAD"], project_path)).strip()
        before = (before or "").strip()
        after = (after or head).strip()

        # 初始提交场景
        if not before or before == after:
            count_raw = await _run(
                ["git", "rev-list", "--count", "HEAD"], project_path
            )
            if int(count_raw.strip()) <= 1:
                files = (await _run(["git", "ls-files"], project_path)).split()
                full_diff = await _run(
                    ["git", "show", "HEAD", "--format=commit %H%n%n"], project_path
                )
                stat = await _run(["git", "show", "--stat", "HEAD"], project_path)
                adds, dels = _parse_stat(stat.split("\n")[-1] if stat else "")
                return {
                    "changed_files": [f for f in files if f],
                    "additions": adds,
                    "deletions": dels,
                    "full_diff": full_diff,
                    "commit_before": "初始提交",
                    "commit_after": head,
                    "summary": stat,
                }

        # 增量 diff
        try:
            files_raw = await _run(
                ["git", "diff", "--name-only", before, after], project_path
            )
            changed_files = [f for f in files_raw.split("\n") if f.strip()]
        except GitError:
            changed_files = []

        try:
            stat = await _run(["git", "diff", "--stat", before, after], project_path)
        except GitError:
            stat = ""

        try:
            full_diff = await _run(["git", "diff", before, after], project_path)
        except GitError:
            full_diff = ""

        adds, dels = 0, 0
        for line in stat.split("\n"):
            a, d = _parse_stat(line)
            adds += a
            dels += d

        return {
            "changed_files": changed_files,
            "additions": adds,
            "deletions": dels,
            "full_diff": full_diff,
            "commit_before": before,
            "commit_after": after,
            "summary": stat,
        }
