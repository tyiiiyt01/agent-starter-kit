#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自检 —— 逐项复核安装结果，判定「算不算成功」。

用法:
    python3 scripts/doctor.py
    python3 scripts/doctor.py --packs code,research

设计原则：agent 负责「猜」（适配路径），doctor 负责「验」（判定对错）。
判定标准是锁死的，不随 agent 的判断变化。

退出码: 0 = 核心项全过；1 = 核心项失败
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = Path(os.path.expanduser("~")) / ".agent-starter-kit" / "state.json"
_OS_KEY = {"darwin": "darwin", "windows": "win32", "linux": "linux"}

OK, FAIL, WARN, INFO = "✅", "❌", "⚠️ ", "·"


# --------------------------------------------------------------------------
def expand(raw: str) -> Path:
    for var, env in (("%APPDATA%", "APPDATA"), ("%USERPROFILE%", "USERPROFILE")):
        raw = raw.replace(var, os.environ.get(env, ""))
    return Path(os.path.expanduser(raw))


def which(name: str) -> str | None:
    exe = shutil.which(name)
    if exe and "WindowsApps" in exe:
        return None  # 微软商店占位程序，不是真的
    return exe


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()
    except Exception:  # noqa: BLE001
        return 1, ""


# --------------------------------------------------------------------------
# 1. Python（唯一硬前置）
# --------------------------------------------------------------------------
def check_python() -> tuple[bool, str]:
    major = int(platform.python_version_tuple()[0])
    if major < 3:
        return False, f"Python 版本过低: {platform.python_version()}，需要 3.8+"
    exe = Path(os.path.realpath(sys.executable))
    return True, f"Python {platform.python_version()}  ({exe})"


# --------------------------------------------------------------------------
# 2. 工具链（缺失只警告，不算失败）
# --------------------------------------------------------------------------
TOOL_HINTS = {
    "node": ("写 JS/TS 项目、跑 npx 类 MCP 需要", "winget install OpenJS.NodeJS / brew install node"),
    "git": ("克隆仓库、装 git 依赖需要", "winget install Git.Git / xcode-select --install"),
    "uv": ("Python 环境隔离推荐用它", "winget install astral-sh.uv / brew install uv"),
    "clang++": ("写 C++ 需要", "xcode-select --install"),
    "g++": ("写 C++ 需要", "安装 MinGW-w64"),
    "cl": ("写 C++ 需要（MSVC）", "安装 Visual Studio Build Tools"),
}


def check_toolchain() -> list[tuple[str, bool, str]]:
    out = []
    for tool, (why, hint) in TOOL_HINTS.items():
        exe = which(tool)
        if exe:
            code, ver = run([tool, "--version"] if tool != "cl" else [tool])
            ver = (ver.splitlines() or [exe])[0]
            out.append((tool, True, ver[:60]))
        else:
            out.append((tool, False, f"{why} —— {hint}"))
    # MATLAB 是商业授权，只报告不建议装
    matlab = which("matlab")
    octave = which("octave")
    if matlab:
        out.append(("matlab", True, "已安装"))
    elif octave:
        out.append(("matlab", False, "未装 MATLAB，但有 Octave 可跑 .m 兼容语法"))
    else:
        out.append(("matlab", False, "未装 MATLAB，也没有 Octave。有学校授权就装 MATLAB"))
    return out


# --------------------------------------------------------------------------
# 2b. 能力包声明的依赖（CLI + Python 包）
# --------------------------------------------------------------------------
SHIM_DIR = Path(os.path.expanduser("~")) / ".agent-setup-kit" / "bin"
TIER_ORDER = {"light": 1, "medium": 2, "heavy": 3}


def expand_vars(raw: str) -> Path:
    for var, env in (("%APPDATA%", "APPDATA"), ("%USERPROFILE%", "USERPROFILE"),
                     ("%LOCALAPPDATA%", "LOCALAPPDATA"), ("%ProgramFiles%", "ProgramFiles")):
        raw = raw.replace(var, os.environ.get(env, ""))
    return Path(os.path.expanduser(raw))


def _collect(packs: list[str], field: str, key: str) -> list[dict]:
    out, seen = [], set()
    for name in packs:
        f = ROOT / "packs" / f"{name}.json"
        if not f.exists():
            continue
        for d in json.loads(f.read_text(encoding="utf-8")).get(field, []):
            if d[key] not in seen:
                seen.add(d[key])
                out.append(d)
    return out


def check_cli_deps(packs: list[str]) -> list[tuple[str, bool, str]]:
    """验证 CLI 依赖「能真的执行」，不是「文件在不在」。

    这是最关键的检查：官方安装器常常不写 PATH，
    文件躺在 Homebrew / app bundle / %LOCALAPPDATA% 里，命令却调不到。
    """
    rows = []
    for dep in _collect(packs, "cliDeps", "name"):
        name = dep["name"]
        tier = dep.get("tier", "light")

        # 1) PATH 里有吗
        hit = None
        for b in dep["bins"]:
            exe = shutil.which(b)
            if exe and "WindowsApps" not in exe:
                hit = (b, exe)
                break

        # 2) PATH 里没有 → 看已知位置（这种情况可自动建 shim 修复）
        if not hit:
            for raw in dep.get("knownPaths", {}).get(_OS_KEY.get(platform.system().lower(), "linux"), []):
                p = expand_vars(raw)
                if p.exists():
                    rows.append((f"{name} (未在 PATH)", False,
                                 f"已安装但调不到: {p} → 运行 apply.py 可自动建 shim 修复"))
                    break
            else:
                hint = dep.get("install", {}).get(_OS_KEY.get(platform.system().lower(), "linux"), "")
                fb = dep.get("fallback", "")
                rows.append((f"{name} ({tier})", False,
                             f"未安装。装法: {hint}｜替代: {fb}"))
            continue

        # 3) 在 PATH 里 → 真的执行一遍
        binname = hit[0]
        probe = dep.get("probe") or [binname, "--version"]
        code, out = run([str(x) for x in probe])
        if code != 0:
            rows.append((f"{name} (在执行时报错)", False,
                         f"{binname} 存在但执行失败（退出码 {code}）: {(out.splitlines() or ['无输出'])[0][:100]}"))
        else:
            ver = (out.splitlines() or [hit[1]])[0]
            rows.append((f"{name}", True, ver[:70]))
    return rows


def check_python_deps(packs: list[str]) -> list[tuple[str, bool, str]]:
    exe = sys.executable
    rows = []
    for dep in _collect(packs, "pythonDeps", "pip"):
        code, out = run([exe, "-c", f"import {dep['import']}"])
        if code == 0:
            rows.append((dep["pip"], True, f"import {dep['import']} 正常"))
        else:
            tier = dep.get("tier", "light")
            rows.append((dep["pip"], False,
                         f"import {dep['import']} 失败（{tier} 档）—— {dep.get('why', '')}"))
    return rows


def check_shims() -> list[tuple[str, bool, str]]:
    """shim 只有在它所在目录进了 PATH 才有用 —— 这条经常被忽略。"""
    if not SHIM_DIR.exists():
        return []
    shims = [p for p in SHIM_DIR.iterdir() if p.is_file()]
    if not shims:
        return []
    on_path = any(Path(p).resolve() == SHIM_DIR.resolve()
                  for p in os.environ.get("PATH", "").split(os.pathsep) if p)
    if not on_path:
        return [("shim 目录不在 PATH", False,
                 f"{SHIM_DIR} 不在 PATH 里，{len(shims)} 个 shim 不生效。"
                 f"需把它加入 PATH")]
    bad = []
    for s in shims:
        code, _ = run([str(s), "--version"], timeout=20)
        if code not in (0, 1) and code != 2:  # 有些工具 --version 返回非 0
            bad.append(s.name)
    if bad:
        return [("shim 执行异常", False, f"这些 shim 跑不通: {', '.join(bad)}")]
    return [("shim 目录", True, f"{len(shims)} 个 shim 已生效（{SHIM_DIR}）")]


# --------------------------------------------------------------------------
# 3. 技能投放结果
# --------------------------------------------------------------------------
FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---", re.S)


def validate_skill_dir(path: Path) -> tuple[bool, str]:
    """校验技能目录：SKILL.md 存在、frontmatter 合法、name 与目录名一致。"""
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return False, "缺少 SKILL.md"
    try:
        text = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False, "SKILL.md 不是 UTF-8 编码"
    m = FRONTMATTER.search(text)
    if not m:
        return False, "SKILL.md 缺少 YAML frontmatter（--- 包裹的头部）"
    head = m.group(1)
    if "name:" not in head:
        return False, "frontmatter 缺少 name 字段"
    if "description:" not in head:
        return False, "frontmatter 缺少 description 字段"
    name_match = re.search(r"name:\s*(\S+)", head)
    if name_match and name_match.group(1).strip("\"'") != path.name:
        return False, f"frontmatter 的 name（{name_match.group(1)}）与目录名（{path.name}）不一致"
    return True, "正常"


def check_skills(hosts: dict, expected_packs: list[str]) -> tuple[bool, list[tuple[str, bool, str]]]:
    """返回 (是否至少一个宿主成功, 明细)。"""
    pack_skills: set[str] = set()
    for name in expected_packs:
        pack_file = ROOT / "packs" / f"{name}.json"
        if pack_file.exists():
            pack_skills |= set(
                json.loads(pack_file.read_text(encoding="utf-8")).get("skills", [])
            )

    rows, any_ok = [], False
    if not pack_skills:
        return False, [("(未指定能力包，跳过技能校验)", False, "")]

    for host_name, spec in hosts.items():
        if not any(expand(p).exists() for p in spec["detect"]):
            continue
        dest_root = expand(spec["skills"][0])
        if not dest_root.exists():
            rows.append((f"{host_name} @ {dest_root}", False, "技能目录不存在，未投放"))
            continue
        bad = []
        for skill in sorted(pack_skills):
            target = dest_root / skill
            if not target.exists():
                bad.append(f"{skill}(未安装)")
                continue
            good, msg = validate_skill_dir(target)
            if not good:
                bad.append(f"{skill}({msg})")
        if bad:
            rows.append((f"{host_name} @ {dest_root}", False, "; ".join(bad)))
        else:
            rows.append((f"{host_name} @ {dest_root}", True, f"{len(pack_skills)} 个技能全部就位"))
            any_ok = True
    return any_ok, rows


# --------------------------------------------------------------------------
# 4. MCP 注册结果
# --------------------------------------------------------------------------
def check_mcp(hosts: dict, expected_packs: list[str]) -> list[tuple[str, bool, str]]:
    rows = []
    for host_name, spec in hosts.items():
        if not any(expand(p).exists() for p in spec["detect"]):
            continue
        mcp = spec["mcp"]
        # cli 策略：用宿主自己的命令反查，比读文件可靠
        if mcp["strategy"] == "cli":
            exe = which("claude")
            if not exe:
                rows.append((f"{host_name} MCP", False, "找不到 claude 命令，无法反查"))
                continue
            code, out = run(["claude", "mcp", "list"])
            rows.append((f"{host_name} MCP", code == 0, out.splitlines()[0] if out else "无输出"))
            continue

        # json / toml：读配置文件确认条目存在
        f = mcp.get("file")
        if isinstance(f, dict):
            f = f.get(_OS_KEY.get(platform.system().lower()))
        path = expand(f) if f else None
        if not path or not path.exists():
            rows.append((f"{host_name} MCP", False, f"配置文件不存在: {path}"))
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            rows.append((f"{host_name} MCP", False, f"{path} 不是 UTF-8，可能是编码写错了"))
            continue

        names: list[str] = []
        if mcp.get("format") == "toml" or str(path).endswith(".toml"):
            key = mcp.get("key", "mcp_servers")
            names = re.findall(rf"^\s*\[{re.escape(key)}\.([^\]]+)\]", raw, re.M)
        else:
            try:
                data = json.loads(raw)
                names = list(data.get(mcp.get("key", "mcpServers"), {}).keys())
            except json.JSONDecodeError as exc:
                rows.append((f"{host_name} MCP", False, f"配置不是合法 JSON: {exc}"))
                continue
        rows.append(
            (
                f"{host_name} MCP @ {path}",
                bool(names),
                f"已注册 {len(names)} 个: {', '.join(names)}" if names else "配置存在但没有任何 server",
            )
        )
    return rows


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packs", default="", help="留空则读 state.json 里装过的包")
    args = ap.parse_args()

    if args.packs:
        packs = [p.strip() for p in args.packs.split(",") if p.strip()]
    else:
        packs = []
        if STATE_FILE.exists():
            try:
                packs = json.loads(STATE_FILE.read_text(encoding="utf-8")).get("packs", []) or []
            except json.JSONDecodeError:
                packs = []
        if not packs:
            packs = ["code"]

    hosts = json.loads((ROOT / "hosts.json").read_text(encoding="utf-8"))["hosts"]

    print("自检结果 —— 逐项复核安装是否真的可用")
    print()

    py_ok, py_msg = check_python()
    print(f"{OK if py_ok else FAIL} Python 环境            {py_msg}")

    # 工具链
    tools = check_toolchain()
    for name, ok, msg in tools:
        print(f"{OK} {name:<21} {msg}" if ok else f"{WARN} {name:<20} {msg}")

    print()
    skills_ok, skill_rows = check_skills(hosts, packs)
    for label, ok, msg in skill_rows:
        print(f"{OK if ok else FAIL} 技能投放 {label}")
        if msg:
            print(f"     {' ' * 8}{msg}")

    print()
    for label, ok, msg in check_mcp(hosts, packs):
        print(f"{OK if ok else FAIL} MCP {label}")
        if msg:
            print(f"     {' ' * 8}{msg}")

    # --- 能力包声明的依赖 ---
    py_deps = check_python_deps(packs)
    if py_deps:
        print()
        print("Python 依赖（按能力包声明）")
        for name, ok, msg in py_deps:
            print(f"{OK if ok else WARN} {name:<21} {msg}")

    cli_deps = check_cli_deps(packs)
    if cli_deps:
        print()
        print("命令行工具（已验证能真的执行，不是只看文件存在）")
        for name, ok, msg in cli_deps:
            print(f"{OK if ok else WARN} {name:<26} {msg}")
        degraded = [n for n, ok, _ in cli_deps if not ok]
        if degraded:
            print()
            print("⚠️  缺失的工具不影响基本使用 —— 每个都有替代方案（见上面每行的「替代」）。")
            print("    要补齐就按上面给的装法执行，然后重跑本自检。")

    for label, ok, msg in check_shims():
        print(f"{OK if ok else WARN} {label:<26} {msg}")

    print()
    core_ok = py_ok and skills_ok
    if core_ok:
        print("核心项全部通过 —— 现在可以正常使用了。")
    else:
        print("核心项未通过。请看上面 ❌ 的项；⚠️ 属于可选能力，不影响基本使用。")
        if not py_ok:
            print("  → Python 是唯一硬前置，必须先解决（见 INSTALL.md 的 Step 0）")
        if not skills_ok:
            print("  → 技能没投放成功。确认宿主路径是否正确（用 hosts.json 里的 confirm_hint）。")
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())