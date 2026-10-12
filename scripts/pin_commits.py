#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""维护者工具：刷新 community-skills.json 里各仓库的 commit 锚点。

用法:
    python3 scripts/pin_commits.py            # 只列出差异，不写文件
    python3 scripts/pin_commits.py --write    # 确认后写回

为什么要 pin commit：安装时会把第三方仓库 clone 到用户机器上。
git 自身的校验只保证「传输过程内容自洽」，**挡不住**镜像把默认分支换成
另一个合法但恶意的 commit，也挡不住被劫持的仓库回滚到有漏洞的旧版本。
只有比对锚点 commit 才能挡住这些（防镜像篡改 / repo-jacking）。

所以每次想「跟着上游更新」时，跑这个脚本、**看一眼 diff 是不是你预期的那几个仓库改了**，
再决定写不写回。别无条件刷新 —— 那等于把锚点变成摆设。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "community-skills.json"


def gh(*args: str) -> tuple[int, str]:
    # 注意：环境里的 GH_TOKEN 若是 App 令牌，某些接口会 403。
    # 用 env -u GH_TOKEN 走用户的 OAuth 令牌更稳。
    cmd = ["env", "-u", "GH_TOKEN", "gh", *args]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return 127, "找不到 gh 命令（没装 gh CLI）"
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def latest_commit(repo: str) -> str | None:
    slug = repo.replace("https://github.com/", "").rstrip("/")
    for branch in ("main", "master"):
        code, out = gh("api", f"repos/{slug}/commits/{branch}", "--jq", ".sha")
        if code == 0 and out.strip():
            return out.strip()
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="写回文件（默认只列差异）")
    args = ap.parse_args()

    data = json.loads(ENTRIES.read_text(encoding="utf-8"))
    changed, failed = [], []

    for e in data["skills"]:
        latest = latest_commit(e["repo"])
        if not latest:
            failed.append(e["id"])
            print(f"  取不到 {e['id']:24}（{e['repo']}）")
            continue
        old = e.get("commit", "")
        if old == latest:
            print(f"  一致 {e['id']:24} {latest[:12]}")
        else:
            changed.append((e, old, latest))
            print(f"  变了 {e['id']:24} {old[:12] or '(空)':12} → {latest[:12]}")

    print()
    if failed:
        print(f"⚠ {len(failed)} 个仓库取不到最新 commit: {failed}")
        print("  可能是仓库改名/删除，或 gh 未授权。**不要把它们从清单里悄悄删掉** —— 先核实。")
    if not changed:
        print("所有锚点都是最新的，无需改动。")
        return 0

    print(f"有 {len(changed)} 个仓库的锚点需要更新。")
    print("⚠ 写回前请确认：这些变化是你预期的吗？（上游正常发版 vs 仓库被劫持）")
    if not args.write:
        print("（当前是只读模式，没有改动文件。确认后加 --write）")
        return 0

    for e, _, latest in changed:
        e["commit"] = latest
    ENTRIES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写回 {ENTRIES}")
    print("别忘了把这次锚点更新记进 CHANGELOG。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())