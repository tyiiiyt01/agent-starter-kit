#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""维护者工具：发版前校验版本号一致性。

用法:
    python3 scripts/check_release.py            # 校验（退出码非 0 表示不一致）

为什么需要它：版本号在 4 个地方各写了一份 —— `scripts/apply.py` 的 VERSION 常量、
`README.md`、`README.en.md`、`SECURITY.md`，以及 `CHANGELOG.md` 的章节标题。
这个项目已经在 v0.2.0 → v0.2.1 的迭代里漏改过一次（README 与 SECURITY 停在旧版），
导致文档告诉用户去锁一个不含新特性的旧版本。与其靠记性，不如让它可校验。

发版流程建议：
    1. 改 CHANGELOG：把 [Unreleased] 归档为 [x.y.z]
    2. 改 scripts/apply.py 的 VERSION
    3. 跑本脚本 —— 它会指出还有哪个文件写着旧版本号
    4. git tag -a vx.y.z && git push origin vx.y.z
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 期望写入「当前版本」的文件（相对路径 → 说明）
VERSION_FILES = {
    "scripts/apply.py": "VERSION 常量（安装/预演输出会打印它）",
    "README.md": "中文版「更新」一节的锁版本命令",
    "README.en.md": "英文版「Updating」一节的锁版本命令",
    "SECURITY.md": "安全政策里的锁版本示例",
}


def strip_comments(text: str) -> str:
    """去掉 HTML 注释 —— 否则会把注释里的模板示例（如 `## [x.y.z]`）当成真章节。"""
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def current_version() -> str:
    text = (ROOT / "scripts/apply.py").read_text(encoding="utf-8")
    m = re.search(r'^VERSION = "([^"]+)"', text, re.M)
    if not m:
        print('❌ 在 scripts/apply.py 里找不到 VERSION = "x.y.z"')
        sys.exit(1)
    return m.group(1)


def versions_in(text: str) -> list[str]:
    """找出文本里所有版本号。

    注意 scripts/apply.py 用的是 `VERSION = "0.2.2"`（没有 v 前缀），
    所以两种写法都要认。
    """
    body = strip_comments(text)
    found = set(re.findall(r"\bv(\d+\.\d+\.\d+)", body))
    found |= set(re.findall(r'VERSION = "(\d+\.\d+\.\d+)"', body))
    return sorted(found)


def main() -> int:
    ver = current_version()
    print(f"当前版本（来自 scripts/apply.py）: v{ver}\n")

    problems: list[str] = []
    for rel, why in VERSION_FILES.items():
        p = ROOT / rel
        if not p.exists():
            problems.append(f"{rel} 不存在")
            continue
        found = versions_in(p.read_text(encoding="utf-8"))
        if not found:
            problems.append(f"{rel} 里找不到任何版本号 —— 应该在示例里出现当前版本（{why}）")
            continue
        stale = [v for v in found if v != ver]
        mark = "✅" if not stale else "❌"
        print(f"  {mark} {rel:20} 出现: {', '.join('v'+v for v in found)}")
        if stale:
            problems.append(f"{rel} 仍写着旧版本 {', '.join('v'+v for v in stale)} —— {why}")

    # CHANGELOG 必须有当前版本的章节（注释里的模板示例不算）
    cl = ROOT / "CHANGELOG.md"
    if cl.exists():
        text = strip_comments(cl.read_text(encoding="utf-8"))
        heads = re.findall(r"^## \[([^\]]+)\]", text, re.M)
        print(f"\n  CHANGELOG 章节: {', '.join(heads)}")
        if ver not in heads:
            problems.append(f"CHANGELOG.md 里没有 [{ver}] 章节 —— 发版前要把 [Unreleased] 归档为该版本")
        if "Unreleased" not in heads:
            problems.append("CHANGELOG.md 缺少 [Unreleased] 章节 —— 归档后要新开一个空的")
        # 重复章节（真实世界里出现过）
        dupes = {h for h in heads if heads.count(h) > 1}
        if dupes:
            problems.append(f"CHANGELOG.md 有重复章节: {', '.join(sorted(dupes))}")
        # 底部的 compare/tag 链接引用要覆盖每个已发布版本
        refs = re.findall(r"^\[([^\]]+)\]:\s*(\S+)$", text, re.M)
        ref_names = {n for n, _ in refs}
        missing_refs = [h for h in heads if h not in ref_names]
        if missing_refs:
            problems.append(
                f"CHANGELOG.md 底部缺链接引用: {', '.join(missing_refs)}"
                f" —— 加了新章节要在文末补 [版本]: compare/tag 链接")
    else:
        problems.append("CHANGELOG.md 不存在")

    print()
    if problems:
        print(f"❌ 发现 {len(problems)} 个不一致：")
        for p in problems:
            print(f"   · {p}")
        print("\n修完再发版 —— 否则用户按文档锁版本会锁到一个不含新特性的旧版。")
        return 1
    print(f"✅ 版本号一致（v{ver}），可以发版。")
    print(f"   下一步: git tag -a v{ver} -m \"...\" && git push origin v{ver}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())