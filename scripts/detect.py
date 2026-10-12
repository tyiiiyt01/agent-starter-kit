#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境探测 —— 只读，不修改任何东西。输出 JSON 供 agent 做适配决策。

用法:
    python3 scripts/detect.py            摘要 + JSON
    python3 scripts/detect.py --json     只输出 JSON

退出码: 0 = Python 可用（必装项齐了）；1 = Python 缺失
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOSTS_FILE = ROOT / "hosts.json"


# --------------------------------------------------------------------------
# 路径展开：Windows 的 %VAR% 与 Unix 的 ~ 统一处理
# --------------------------------------------------------------------------
def expand(raw: str) -> Path:
    for var, env in (("%APPDATA%", "APPDATA"), ("%USERPROFILE%", "USERPROFILE")):
        raw = raw.replace(var, os.environ.get(env, ""))
    return Path(os.path.expanduser(raw))


def run(cmd: list[str], timeout: int = 20) -> str | None:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return out or None


# --------------------------------------------------------------------------
# 前置依赖探测
# --------------------------------------------------------------------------
def probe_python() -> dict:
    """探测 Python 3。

    Windows 上有个坑：干净系统里输入 python 会唤起微软商店的占位程序，
    它既不是真实 Python 也不会报错退出，必须显式识别。
    """
    for cand in (["py", "-3"], ["python3"], ["python"]):
        exe = shutil.which(cand[0])
        if not exe:
            continue
        if "WindowsApps" in exe:
            return {
                "ok": False,
                "cmd": " ".join(cand),
                "issue": "这是微软商店的占位程序，不是真实 Python",
                "hint": "安装: winget install Python.Python.3.12  或去 python.org 下载",
            }
        out = run(cand + ["-V"])
        if out and out.lower().startswith("python 3"):
            return {"ok": True, "cmd": " ".join(cand), "version": out, "path": exe}
    return {
        "ok": False,
        "cmd": None,
        "issue": "未找到 Python 3",
        "hint": "macOS: brew install python3 / xcode-select --install；Windows: winget install Python.Python.3.12",
    }


def probe_tool(name: str, version_args: list[str]) -> dict:
    exe = shutil.which(name)
    if not exe:
        return {"ok": False}
    return {"ok": True, "version": run([name] + version_args) or exe, "path": exe}


def probe_toolchain() -> dict:
    """编程能力相关工具链。macOS 与 Windows 的 C++ 编译器完全不同名。"""
    return {
        "node": probe_tool("node", ["-v"]),
        "npm": probe_tool("npm", ["-v"]),
        "git": probe_tool("git", ["--version"]),
        "uv": probe_tool("uv", ["--version"]),
        # C++：macOS 用 clang++，Windows 用 g++(MinGW) 或 cl(MSVC)
        "clang++": probe_tool("clang++", ["--version"]),
        "g++": probe_tool("g++", ["--version"]),
        "cl": probe_tool("cl", []),
        # MATLAB 是商业授权，永远装不了，只能检测
        "matlab": probe_tool("matlab", ["-batch", "disp(version)"]),
        "octave": probe_tool("octave", ["--version"]),
        "xcode-select": probe_tool("xcode-select", ["-p"]),
        "winget": probe_tool("winget", ["--version"]),
        "brew": probe_tool("brew", ["--version"]),
    }


# --------------------------------------------------------------------------
# 宿主探测
# --------------------------------------------------------------------------
def load_hosts() -> dict:
    return json.loads(HOSTS_FILE.read_text(encoding="utf-8"))["hosts"]


_OS_KEY = {"darwin": "darwin", "windows": "win32", "linux": "linux"}


def resolve_mcp_file(mcp: dict) -> Path | None:
    f = mcp.get("file")
    if isinstance(f, dict):
        f = f.get(_OS_KEY.get(platform.system().lower()))
    return expand(f) if f else None


def probe_hosts(hosts: dict) -> dict:
    found, missing = {}, {}
    for name, spec in hosts.items():
        hits = [str(expand(p)) for p in spec["detect"] if expand(p).exists()]
        entry = {
            "display": spec["display"],
            "verified": spec.get("verified", False),
            "verify_detail": spec.get("_verified_detail") or spec.get("_unverified"),
            "confirm_hint": spec.get("confirm_hint"),
            "detect_hits": hits,
            "skills_dir": [str(expand(p)) for p in spec["skills"]],
            "skills_dir_exists": any(expand(p).exists() for p in spec["skills"]),
            "mcp_file": "",
            "mcp_file_exists": False,
            "mcp_strategy": spec["mcp"]["strategy"],
            "mcp_shape": spec["mcp"].get("shape", "table"),
        }
        mf = resolve_mcp_file(spec["mcp"])
        if mf:
            entry["mcp_file"] = str(mf)
            entry["mcp_file_exists"] = mf.exists()

        # 工作区制宿主（如 Reasonix）：技能目录在工作区内部，路径不固定，
        # 需要用 skills_discovery 通配符搜索，把候选全部列出来。
        # agent 据此让用户挑当前工作区 —— 不能用 --skill-dir 之前必须先问。
        if spec.get("skills_discovery"):
            entry["skills_discovery"] = spec["skills_discovery"]
            candidates = discover_skill_dirs(spec)
            entry["skills_candidates"] = [str(c) for c in candidates]
            entry["skills_ambiguous"] = len(candidates) > 1
            if len(candidates) > 1:
                entry["skills_note"] = (
                    f"找到 {len(candidates)} 个候选技能目录，必须让用户指定装进哪一个"
                    f"（用 apply.py --skill-dir <路径>），不要按修改时间猜"
                )

        if hits:
            found[name] = entry
        else:
            missing[name] = entry
    return {"found": found, "missing": missing}


def discover_skill_dirs(spec: dict) -> list:
    """展开 skills_discovery 通配符。与 apply.py 保持同一实现 —— 见那里的注释。"""
    pattern = spec.get("skills_discovery")
    if not pattern:
        return []
    parts = Path(pattern).parts
    if len(parts) <= 3:
        return []
    anchor = expand(str(Path(*parts[:-3])))
    if not anchor.is_dir():
        return []
    try:
        hits = sorted(anchor.glob("/".join(parts[-3:])),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return []
    return [h for h in hits if h.is_dir()]


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="只输出 JSON")
    args = ap.parse_args()

    system = platform.system().lower()
    result = {
        "os": system,
        "os_name": f"{platform.system()} {platform.release()}",
        "is_windows": system == "windows",
        "python_runtime_running_this_script": {
            "executable": os.path.realpath(shutil.which("python3") or ""),
            "version": platform.python_version(),
            "argv0": " ".join([Path(os.path.realpath(__import__("sys").executable)).name]),
        },
        "python": probe_python(),
        "toolchain": probe_toolchain(),
        "hosts": probe_hosts(load_hosts()),
        "shell": {
            "has_bash": bool(shutil.which("bash")),
            "has_powershell": bool(shutil.which("powershell") or shutil.which("pwsh")),
        },
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"系统        : {result['os_name']}")
        py = result["python"]
        print(f"Python      : {'OK  ' + py['version'] if py['ok'] else '缺失 — ' + py['issue']}")
        for key in ("git", "node", "uv", "clang++", "g++", "cl", "matlab", "octave"):
            t = result["toolchain"][key]
            print(f"{key:<12}: {t.get('version') if t['ok'] else '未安装'}")
        hs = result["hosts"]
        print(f"已装宿主    : {', '.join(hs['found'].keys()) or '无'}")
        print(f"未装宿主    : {', '.join(hs['missing'].keys()) or '无'}")
        print()
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result["python"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())