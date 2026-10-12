#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""幂等安装器。

用法:
    python3 scripts/apply.py --packs code --dry-run          # 预演，不改任何东西
    python3 scripts/apply.py --packs code,research           # 实际安装（含 light 档依赖）
    python3 scripts/apply.py --packs math-modeling --tier medium
    python3 scripts/apply.py --hosts claude-code --no-cli     # 只投技能和 MCP，不碰依赖

依赖分档:
    light   （<100MB）默认装
    medium  （100MB-1GB）需要 --tier medium 才装
    heavy   （>1GB）永不自动装，只检测 + 给引导

保证:
    · 幂等      —— 重复运行不报错、不重复装
    · 增量合并  —— 写配置是合并而非覆盖，用户自己的配置会被保留
    · 可回滚    —— 记录到 state.json，供卸载使用
    · CLI 优先  —— strategy=cli 的宿主走命令行写入，绝不手写覆盖大文件
    · 失败不中断 —— 单个依赖/MCP 失败不影响整体，记入结果报告
    · PATH shim —— 装了但不在 PATH 的工具会自动建转发脚本，解决「下载了却用不了」

所有文件一律以 UTF-8 无 BOM 写入（Windows 默认可能是 GBK，会导致中文乱码 + 配置解析失败）。
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.1.0"
STATE_DIR = Path(os.path.expanduser("~")) / ".agent-starter-kit"
STATE_FILE = STATE_DIR / "state.json"
SHIM_DIR = STATE_DIR / "bin"
_OS_KEY = {"darwin": "darwin", "windows": "win32", "linux": "linux"}
TIER_ORDER = {"light": 1, "medium": 2, "heavy": 3}
# 国内网络下 PyPI 直连很慢，默认走清华镜像（它本身就是 PyPI 的完整镜像，海外也能用）
DEFAULT_PYPI_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------
def os_key() -> str:
    return _OS_KEY.get(platform.system().lower(), "linux")


def expand(raw: str) -> Path:
    for var, env in (("%APPDATA%", "APPDATA"), ("%USERPROFILE%", "USERPROFILE"),
                     ("%LOCALAPPDATA%", "LOCALAPPDATA"), ("%ProgramFiles%", "ProgramFiles")):
        raw = raw.replace(var, os.environ.get(env, ""))
    return Path(os.path.expanduser(raw))


def read_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"[!] {path} 不是合法 JSON（{exc}）。请先修好它，不要覆盖——里面可能有用户自己的配置。"
        )


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_state() -> dict:
    return read_json(STATE_FILE, {"skills": [], "mcp": [], "hosts": [], "packs": [],
                                  "pythonDeps": [], "cliDeps": [], "shims": []})


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(STATE_FILE, state)


def run(cmd: list[str], timeout: int = 900) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()
    except FileNotFoundError:
        return 127, f"命令不存在: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"超时（{timeout}s）: {' '.join(cmd[:3])}"
    except Exception as exc:  # noqa: BLE001
        return 1, str(exc)


# 配置里的占位符，写入前必须替换，否则 MCP 会拿着字面量启动然后失败
def substitute(value):
    if isinstance(value, list):
        return [substitute(v) for v in value]
    if isinstance(value, str):
        return value.replace("{{HOME}}", str(Path.home()))
    return value


# --------------------------------------------------------------------------
# 国内网络加速
# --------------------------------------------------------------------------
# GitHub 直连在国内经常掉到 30 KB/s，加代理前缀可到 4-8 MB/s。
# 镜像会失效或限速，所以内置多路回退，不硬编码单一镜像。
GH_PROXIES = [
    "",  # 先试直连
    "https://gh-proxy.com/",
    "https://ghfast.top/",
    "https://ghproxy.net/",
    "https://hub.gitmirror.com/",
]

MIRRORS_ENV = {
    "PIP_INDEX_URL": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "UV_DEFAULT_INDEX": "https://pypi.tuna.tsinghua.edu.cn/simple",
    "HF_ENDPOINT": "https://hf-mirror.com",
    "NPM_CONFIG_REGISTRY": "https://registry.npmmirror.com",
    "PYTHONUTF8": "1",
}


def write_mirrors_env() -> Path:
    """写出镜像环境变量文件。

    HF_ENDPOINT 尤其重要 —— pdf2zh / faster-whisper 首次运行要下模型，
    不配镜像在国内基本下不动。
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / "mirrors.env"
    lines = ["# agent-starter-kit 生成的国内网络加速环境变量",
             "# 用法: source ~/.agent-starter-kit/mirrors.env",
             ""]
    for k, v in MIRRORS_ENV.items():
        lines.append(f'export {k}="{v}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def with_proxy(url: str, proxy: str) -> str:
    """给 GitHub URL 套上加速前缀。已是代理形式或非 GitHub 则原样返回。"""
    if not proxy or not url.startswith("https://github.com/"):
        return url
    return proxy.rstrip("/") + "/" + url


def clone_with_fallback(repo_url: str, dest: Path, proxy_choice: str, log: list) -> bool:
    """克隆仓库，直连失败就逐个试加速镜像。

    proxy_choice: "auto" 走 GH_PROXIES 多路回退；空字符串表示只用直连。
    """
    proxies = GH_PROXIES if proxy_choice == "auto" else [proxy_choice]
    if dest.exists():
        shutil.rmtree(dest)
    for proxy in proxies:
        url = with_proxy(repo_url, proxy)
        code, out = run(["git", "clone", "--depth", "1", url, str(dest)], timeout=600)
        if code == 0:
            tag = proxy or "直连"
            log.append(f"克隆成功（{tag}）: {repo_url}")
            return True
        log.append(f"克隆失败（{proxy or '直连'}）: {out.splitlines()[-1][:100] if out else ''}")
    return False


# --------------------------------------------------------------------------
# 配置载入
# --------------------------------------------------------------------------
def load_hosts() -> dict:
    return read_json(ROOT / "hosts.json")["hosts"]


def resolve_mcp_file(mcp: dict) -> Path | None:
    f = mcp.get("file")
    if isinstance(f, dict):
        f = f.get(os_key())
    return expand(f) if f else None


def discover_skill_dirs(spec: dict) -> list[Path]:
    """展开 skills_discovery 通配符，找出候选技能目录。

    用于工作区制的宿主（如 Reasonix）：技能目录在工作区内部，工作区名不固定，
    没法写死路径，只能搜索。返回按修改时间倒序 —— 最近用过的排前面。
    """
    pattern = spec.get("skills_discovery")
    if not pattern:
        return []
    # Path.glob 不吃展开后的绝对路径，所以拆成「锚点目录 + 尾部通配模式」
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


class AmbiguousSkillsDir(Exception):
    """发现多个候选技能目录，无法自动决定装进哪一个。

    典型场景：工作区制宿主（Reasonix）有多个工作区，每个都有自己的技能目录。
    这时必须让用户指定，不能按修改时间瞎猜 —— 猜错的话用户在自己工作区里看不到技能。
    """

    def __init__(self, host: str, candidates: list[Path]):
        self.host = host
        self.candidates = candidates
        super().__init__(host)


def resolve_skills_root(spec: dict, override: str | None = None) -> Path:
    """决定技能装到哪。

    优先级：显式 override > skills_discovery 找到的唯一目录 > 静态 skills[0]。
    找到多个候选时抛 AmbiguousSkillsDir，由调用方要求用户指定。
    """
    if override:
        return expand(override)
    found = discover_skill_dirs(spec)
    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        raise AmbiguousSkillsDir(spec.get("display", "未知宿主"), found)
    return expand(spec["skills"][0])


def load_packs(names: list[str]) -> dict:
    packs = {}
    for name in names:
        path = ROOT / "packs" / f"{name}.json"
        if not path.exists():
            raise SystemExit(f"[!] 找不到能力包: {name}（期望在 {path}）")
        packs[name] = read_json(path)
    return packs


def detect_hosts(hosts: dict) -> dict:
    return {n: s for n, s in hosts.items() if any(expand(p).exists() for p in s["detect"])}


# --------------------------------------------------------------------------
# 依赖探测
# --------------------------------------------------------------------------
def cli_probe(dep: dict) -> dict:
    """探测 CLI 依赖。三级结果：PATH 里有 / 装了但不在 PATH / 没装。

    「装了但不在 PATH」是最常见的失败模式 —— 官方安装器往往不写 PATH，
    文件躺在 Homebrew、app bundle 或 %LOCALAPPDATA% 里，命令却调不到。
    """
    for b in dep["bins"]:
        exe = shutil.which(b)
        if exe and "WindowsApps" not in exe:
            return {"state": "ok", "bin": b, "path": exe}
    for raw in dep.get("knownPaths", {}).get(os_key(), []):
        p = expand(raw)
        if p.exists():
            return {"state": "off_path", "bin": dep["bins"][0], "path": str(p)}
    return {"state": "missing", "bin": dep["bins"][0], "path": None}


def py_dep_probe(dep: dict, python_exe: str) -> bool:
    code, _ = run([python_exe, "-c", f"import {dep['import']}"], timeout=60)
    return code == 0


def make_shim(name: str, target: str) -> Path:
    """给不在 PATH 的工具建转发脚本。

    Windows 用 .cmd，其余用 sh。这是「下载了却用不了」的解药。
    """
    SHIM_DIR.mkdir(parents=True, exist_ok=True)
    if platform.system().lower() == "windows":
        shim = SHIM_DIR / f"{name}.cmd"
        # 注：.cmd 用 UTF-8 写入，若目标路径含中文可能失效，此时回退到手动加 PATH
        shim.write_text(f'@echo off\r\n"{target}" %*\r\n', encoding="utf-8")
    else:
        shim = SHIM_DIR / name
        shim.write_text(f'#!/bin/sh\nexec "{target}" "$@"\n', encoding="utf-8")
        shim.chmod(0o755)
    return shim


# --------------------------------------------------------------------------
# 计划生成
# --------------------------------------------------------------------------
def collect_python_deps(pack_names: list[str], packs: dict) -> list[dict]:
    out, seen = [], set()
    for pn in pack_names:
        for d in packs[pn].get("pythonDeps", []):
            if d["pip"] not in seen:
                seen.add(d["pip"])
                out.append(d)
    return out


def collect_cli_deps(pack_names: list[str], packs: dict) -> list[dict]:
    out, seen = [], set()
    for pn in pack_names:
        for d in packs[pn].get("cliDeps", []):
            if d["name"] not in seen:
                seen.add(d["name"])
                out.append(d)
    return out


def plan_skills(pack_names: list[str], packs: dict, target_hosts: dict,
                skill_dir: str | None = None) -> list[dict]:
    actions = []
    for host_name, spec in target_hosts.items():
        dest_root = resolve_skills_root(spec, skill_dir)
        for pack_name in pack_names:
            for skill in packs[pack_name].get("skills", []):
                src = ROOT / "skills" / skill
                actions.append({
                    "kind": "skill", "host": host_name, "skill": skill,
                    "src": str(src), "dst": str(dest_root / skill),
                    "exists": (dest_root / skill).exists(),
                    "src_ok": (src / "SKILL.md").exists(),
                })
    return actions


def plan_mcp(pack_names: list[str], packs: dict, target_hosts: dict,
             minimal: bool = False) -> list[dict]:
    """生成 MCP 安装计划。

    minimal=True 时只装标记了 essential 的 server —— 因为 MCP 会占满上下文：
    实测 3 个 MCP 可吃掉 200k 上下文里的 143k，装多了 agent 会变笨。
    """
    actions = []
    seen: set[tuple[str, str]] = set()
    for host_name, spec in target_hosts.items():
        mcp = spec["mcp"]
        for pack_name in pack_names:
            for server in packs[pack_name].get("mcp", []):
                if minimal and not server.get("essential"):
                    continue
                # 多个包会声明同一个 server（如 filesystem），这里就去重，
                # 否则同一个 MCP 会被安装两次、报告里出现「已写入」紧跟「已存在，跳过」
                sig = (host_name, server["name"])
                if sig in seen:
                    continue
                seen.add(sig)
                actions.append({
                    "kind": "mcp", "host": host_name, "server": server,
                    "strategy": mcp["strategy"], "cmd": mcp.get("cmd"),
                    "file": str(resolve_mcp_file(mcp) or ""), "key": mcp.get("key"),
                    "shape": mcp.get("shape"),
                    "verified": spec.get("verified"),
                })
    return actions


# --------------------------------------------------------------------------
# 社区高星技能（可选安装）
# --------------------------------------------------------------------------
def load_community() -> dict:
    path = ROOT / "community-skills.json"
    return read_json(path, {}).get("skills", [])


def plan_community(entries: list[dict], only: list[str], target_hosts: dict,
                   skill_dir: str | None = None) -> list[dict]:
    out = []
    for e in entries:
        if only and e["id"] not in only:
            continue
        for host_name, spec in target_hosts.items():
            out.append({
                "kind": "community", "host": host_name, "entry": e,
                # 必须和普通技能用同一个解析结果，否则同一宿主会装到两个不同目录
                "dest_root": str(resolve_skills_root(spec, skill_dir)),
            })
    return out


def do_community(action: dict, proxy: str, state: dict) -> str:
    """克隆社区技能仓库，把其中声明的技能目录复制到宿主技能目录。

    仓库里的技能目录名来自 community-skills.json 的 subdirs 字段 ——
    不猜结构，找不到就如实报告。
    """
    e, host = action["entry"], action["host"]
    tmp = STATE_DIR / "tmp" / e["id"]
    log: list[str] = []
    if not clone_with_fallback(e["repo"], tmp, proxy, log):
        return f"社区技能 {e['id']} 安装失败（所有镜像都不通）: {log[-1] if log else ''}"

    dest_root = Path(action["dest_root"])
    installed, missing = [], []
    for sub in e.get("subdirs", []):
        # 允许 subdirs 里写 "path/to/skill"，两边都试
        src = tmp / sub
        if not (src / "SKILL.md").exists():
            missing.append(sub)
            continue
        dst = dest_root / Path(sub).name
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
        installed.append(Path(sub).name)
        entry = {"host": host, "skill": Path(sub).name, "path": str(dst),
                 "source": e["repo"], "license": e.get("license", "未知")}
        if entry not in state["skills"]:
            state["skills"].append(entry)

    shutil.rmtree(tmp, ignore_errors=True)
    msg = f"社区技能 {e['id']} → {host}: 装了 {len(installed)} 个"
    if installed:
        msg += f"（{', '.join(installed)}）"
    if missing:
        msg += f"\n    仓库里没找到这些子目录，已跳过: {', '.join(missing)}"
    if e.get("license_risk"):
        msg += f"\n    ⚠ 许可证: {e.get('license', '未核实')} —— {e['license_risk']}"
    return msg


# --------------------------------------------------------------------------
# 执行：技能
# --------------------------------------------------------------------------
def do_skill(action: dict, state: dict) -> str:
    if not action["src_ok"]:
        return f"跳过（源缺失）: {action['skill']}"
    src, dst = Path(action["src"]), Path(action["dst"])
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    entry = {"host": action["host"], "skill": action["skill"], "path": str(dst)}
    if entry not in state["skills"]:
        state["skills"].append(entry)
    return f"已投放 {action['skill']} → {dst}"


# --------------------------------------------------------------------------
# 执行：MCP
# --------------------------------------------------------------------------
def _emit_manual(host_name: str, server: dict, reason: str) -> str:
    snippet = json.dumps(
        {server["name"]: {"command": server.get("command"),
                          "args": substitute(server.get("args", []))}},
        ensure_ascii=False, indent=2)
    return f"需手动处理 [{host_name}/{server['name']}]: {reason}\n{snippet}"


def do_mcp(action: dict, state: dict) -> str:
    host_name, server = action["host"], action["server"]
    name = server["name"]
    srv_args = substitute([str(a) for a in server.get("args", [])])
    srv_env = substitute(server.get("env")) or {}

    if action["strategy"] == "cli":
        cmd = list(action.get("cmd") or []) + [name]
        for k, v in srv_env.items():
            cmd += ["--env", f"{k}={v}"]
        cmd += ["--", server["command"]] + srv_args
        code, out = run(cmd, timeout=120)
        if code != 0:
            return _emit_manual(host_name, server, f"CLI 写入失败: {out[:200]}")
        entry = {"host": host_name, "server": name, "via": "cli"}
        if entry not in state["mcp"]:
            state["mcp"].append(entry)
        return f"已通过 cli 注册 {name} → {host_name}"

    if action["strategy"] == "json":
        path = Path(action["file"])
        if not action["file"]:
            return _emit_manual(host_name, server,
                                "hosts.json 里这个宿主没声明 mcp.file，无法写入")
        data = read_json(path, {})
        key = action["key"] or "mcpServers"
        existing = data.setdefault(key, {})
        if not isinstance(existing, dict):
            return _emit_manual(host_name, server,
                                f"配置里 [{key}] 不是字典结构，与预期不符，已跳过以免写坏文件")
        if name in existing:
            return f"已存在，跳过 {name} → {path}"
        existing[name] = {"command": server["command"], "args": srv_args}
        if srv_env:
            existing[name]["env"] = srv_env
        write_json(path, data)
        entry = {"host": host_name, "server": name, "path": str(path)}
        if entry not in state["mcp"]:
            state["mcp"].append(entry)
        return f"已合并写入 {name} → {path}"

    if action["strategy"] == "toml":
        try:
            import tomli_w  # type: ignore
        except ImportError:
            return _emit_manual(
                host_name, server,
                "TOML 写入需要 tomli_w（pip install tomli-w），本机没有。"
                "为安全起见不手工拼接 TOML，请手动粘贴下面的配置段，或先装 tomli-w 后重跑。")
        try:
            import tomllib
        except ImportError:
            # Python < 3.11 没有 tomllib，回退到第三方 tomli（同一套 API）
            try:
                import tomli as tomllib  # type: ignore
            except ImportError:
                return _emit_manual(
                    host_name, server,
                    "读 TOML 需要 Python 3.11+ 的 tomllib，或 pip install tomli。"
                    "两者都没有，无法安全读写这个配置文件。")
        try:
            path = Path(action["file"])
            data = tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except Exception as exc:  # noqa: BLE001
            return _emit_manual(host_name, server, f"读取 TOML 失败: {exc}")

        key = action["key"] or "mcp_servers"
        shape = action.get("shape") or "table"
        entry_body = {"command": server["command"], "args": srv_args}
        if srv_env:
            entry_body["env"] = srv_env

        if shape == "array":
            # 数组表（如 Reasonix 的 [[plugins]]）：每个条目一个块，不是 name→{} 字典
            section = data.setdefault(key, [])
            if not isinstance(section, list):
                return _emit_manual(
                    host_name, server,
                    f"配置里的 [{key}] 不是数组表，但 hosts.json 声明 shape=array。"
                    f"结构不符，为避免写坏配置文件已跳过。请人工确认 {path} 的实际结构。")
            if any(isinstance(e, dict) and e.get("name") == name for e in section):
                return f"已存在，跳过 {name} → {action['file']}"
            section.append({"name": name, **entry_body})
        else:
            section = data.setdefault(key, {})
            if name in section:
                return f"已存在，跳过 {name} → {action['file']}"
            section[name] = entry_body

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tomli_w.dumps(data), encoding="utf-8")
        entry = {"host": host_name, "server": name, "path": str(path), "shape": shape}
        if entry not in state["mcp"]:
            state["mcp"].append(entry)
        return f"已合并写入 {name} → {path}（{shape}）"

    return _emit_manual(host_name, server, f"未知策略: {action['strategy']}")


# --------------------------------------------------------------------------
# 执行：依赖
# --------------------------------------------------------------------------
def resolve_python_exe() -> str:
    for cand in (["py", "-3"], ["python3"], ["python"]):
        exe = shutil.which(cand[0])
        if exe and "WindowsApps" not in exe:
            return " ".join([exe] + cand[1:])
    return sys.executable


def do_python_dep(dep: dict, python_exe: str, mirror: str, state: dict) -> str:
    if py_dep_probe(dep, python_exe.split()[0]):
        return f"已存在，跳过 {dep['pip']}"
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "--python", python_exe.split()[0]]
    else:
        cmd = python_exe.split() + ["-m", "pip", "install", "--user"]
    cmd += [dep["pip"]]
    if mirror:
        cmd += ["-i", mirror]
    code, out = run(cmd)
    if code != 0:
        return f"安装失败 {dep['pip']}: {out.splitlines()[-1][:160] if out else '未知错误'}"
    entry = {"pip": dep["pip"], "import": dep["import"], "why": dep.get("why", "")}
    if entry not in state["pythonDeps"]:
        state["pythonDeps"].append(entry)
    return f"已安装 {dep['pip']}（import {dep['import']}）"


def do_cli_dep(dep: dict, tier_limit: int, state: dict) -> str:
    name = dep["name"]
    probe = cli_probe(dep)
    tier = dep.get("tier", "light")

    # 已经在 PATH 里
    if probe["state"] == "ok":
        return f"已在 PATH，跳过 {name}（{probe['path']}）"

    # 装了但不在 PATH → 建 shim（这是「下载了却用不了」的解法）
    if probe["state"] == "off_path":
        if dep.get("shim", True) is False:
            return (f"{name} 已安装但不在 PATH: {probe['path']}\n"
                    f"    需手动把它所在目录加入 PATH")
        shim = make_shim(probe["bin"], probe["path"])
        entry = {"name": name, "bin": probe["bin"], "target": probe["path"], "shim": str(shim)}
        if entry not in state["shims"]:
            state["shims"].append(entry)
        return (f"{name} 已安装但不在 PATH → 已建 shim: {shim}\n"
                f"    注意：需确保 {SHIM_DIR} 在 PATH 里（doctor 会复核）")

    # 没装
    if TIER_ORDER.get(tier, 1) > tier_limit:
        hint = dep.get("install", {}).get(os_key())
        why_not = "重装项，不自动安装" if tier == "heavy" else f"属于 {tier} 档，需 --tier {tier}"
        return (f"未安装 {name}（{why_not}）\n    装法: {hint}\n"
                f"    不装的替代方案: {dep.get('fallback', '无')}")

    cmd_str = dep.get("install", {}).get(os_key())
    if not cmd_str:
        return f"未安装 {name}，且当前系统没有适配的安装命令。装法见 README"
    cmd = shlex.split(cmd_str)
    if any(ch in cmd_str for ch in "|&>"):
        return f"未安装 {name}。该命令需要 shell 管道，为安全不自动执行，请手动运行:\n    {cmd_str}"
    code, out = run(cmd)
    if code != 0:
        tail = out.splitlines()[-1][:160] if out else "未知错误"
        return (f"安装失败 {name}: {tail}\n    手动重试: {cmd_str}\n"
                f"    替代方案: {dep.get('fallback', '无')}")
    entry = {"name": name, "bin": dep["bins"][0], "method": cmd_str,
             "why": dep.get("why", "")}
    if entry not in state["cliDeps"]:
        state["cliDeps"].append(entry)
    return f"已安装 {name}"


# --------------------------------------------------------------------------
# 计划渲染
# --------------------------------------------------------------------------
def render_plan(skills, mcps, py_deps, cli_deps, packs, pack_names, python_exe, tier_limit,
                community=None, minimal_mcp=False, mirrors=True, gh_proxy="auto") -> str:
    community = community or []
    L = [f"agent-starter-kit v{VERSION} —— 即将执行以下操作：", ""]

    by_host: dict[str, list[dict]] = {}
    for a in skills:
        by_host.setdefault(a["host"], []).append(a)
    for host, items in by_host.items():
        L.append(f"【技能文件】投放到 {Path(items[0]['dst']).parent}")
        for a in items:
            mark = "~" if a["exists"] else "+"
            warn = "" if a["src_ok"] else "   ⚠ 源文件缺失，将跳过"
            L.append(f"  {mark} {a['skill']}{warn}")
        L.append("")

    seen = set()
    for a in mcps:
        sig = (a["host"], a["strategy"], a["file"])
        if sig in seen:
            continue
        seen.add(sig)
        L.append(f"【MCP 配置】{a['host']} → {a['file'] or a['strategy'] + ' 命令写入'}")
        # 多个包可能声明同一个 server（如 filesystem），按名字去重展示 —— 实际只会装一份
        shown = set()
        for b in mcps:
            if (b["host"], b["strategy"], b["file"]) != sig:
                continue
            sname = b["server"]["name"]
            if sname in shown:
                continue
            shown.add(sname)
            opt = "（可选）" if b["server"].get("optional") else ""
            why = b["server"].get("why", "")
            # why 里那句上下文提醒对所有 MCP 都一样，清单里只留一次更清爽
            why = why.split("。⚠️ MCP 会占用")[0]
            L.append(f"  + {sname:<16}{opt}{why}")
        if a["verified"] is not True:
            L.append(f"  ⚠ 该宿主路径未经完全核实（{a['verified']}），装完自检会复核")
        L.append("")

    if minimal_mcp:
        L.append("【已按 --minimal-mcp 过滤】只装 essential 的 MCP")
        L.append("  原因：MCP 极吃上下文 —— 实测 3 个 MCP 能占掉 200k 上下文里的 143k。")
        L.append("  装多了 agent 反而变笨。需要更多能力随时再说。")
        L.append("")

    if community:
        L.append("【社区高星技能】从 GitHub 克隆后投放")
        seen_c = set()
        for a in community:
            e = a["entry"]
            if e["id"] in seen_c:
                continue
            seen_c.add(e["id"])
            tag = "（默认）" if e.get("default") else ""
            L.append(f"  + {e['id']:<22}{tag}{e.get('what', '')}")
            if e.get("license_risk"):
                L.append(f"    ⚠ 许可证 {e.get('license', '未核实')}：{e['license_risk']}")
        L.append("  标「默认」的属于基础能力补充；不想要可以加 --no-community-defaults")
        L.append("")

    if mirrors:
        L.append("【国内网络加速】写入环境变量文件")
        for k, v in MIRRORS_ENV.items():
            L.append(f"  {k}={v}")
        L.append("  (HF_ENDPOINT 尤其重要 —— pdf2zh / faster-whisper 下模型必须靠它)")
        L.append("")

    if gh_proxy == "auto":
        L.append("【GitHub 加速】多路回退: 直连 → " + " → ".join(p.strip("/").replace("https://", "")
                                                        for p in GH_PROXIES[1:]))
        L.append("")

    if py_deps:
        L.append(f"【Python 依赖】装到 {python_exe}")
        for d in py_deps:
            tier = d.get("tier", "light")
            if TIER_ORDER.get(tier, 1) > tier_limit:
                L.append(f"  · {d['pip']:<20}跳过（{tier} 档）—— {d.get('why', '')}")
            else:
                L.append(f"  + {d['pip']:<20}{d.get('why', '')}")
        L.append("")

    if cli_deps:
        L.append("【命令行工具】")
        for d in cli_deps:
            probe = cli_probe(d)
            tier = d.get("tier", "light")
            if probe["state"] == "ok":
                L.append(f"  ✓ {d['name']:<14}已在 PATH，无需处理")
            elif probe["state"] == "off_path":
                L.append(f"  ⚠ {d['name']:<14}已装但不在 PATH → 自动建 shim 修复")
            elif TIER_ORDER.get(tier, 1) > tier_limit:
                L.append(f"  · {d['name']:<14}不装（{tier} 档）—— {d.get('why', '')}")
            else:
                L.append(f"  + {d['name']:<14}{d.get('why', '')}")
        L.append("")

    manual = []
    for name in pack_names:
        manual += packs[name].get("manual", [])
    if manual:
        L.append("【需要你自己动手的】")
        for m in manual:
            L.append(f"  ! {m}")
        L.append("")

    L += ["不会做任何系统级修改，不需要管理员权限。",
          "回答「确认」我就开始装。"]
    return "\n".join(L)


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packs", default="code", help="逗号分隔的能力包名")
    ap.add_argument("--hosts", default="", help="逗号分隔，留空则自动探测")
    ap.add_argument("--dry-run", action="store_true", help="只预演，不做任何修改")
    ap.add_argument("--tier", default="light", choices=["light", "medium", "heavy", "none"],
                    help="允许自动安装的依赖档位上限（默认 light；heavy 永不自动装）")
    ap.add_argument("--no-cli", action="store_true", help="不装任何命令行工具")
    ap.add_argument("--no-python-deps", action="store_true", help="不装任何 Python 包")
    ap.add_argument("--pypi-mirror", default=DEFAULT_PYPI_MIRROR,
                    help="PyPI 镜像地址。传空字符串即用官方源")
    ap.add_argument("--minimal-mcp", action="store_true",
                    help="只装标记 essential 的 MCP。MCP 很吃上下文，装多了 agent 会变笨")
    ap.add_argument("--with-community", nargs="?", const="all", default="",
                    help="额外装社区高星技能。传 'all' 装全部，或传逗号分隔的 id。"
                         "标了 default 的（ppt-master / anthropics-skills）本来就是默认装的")
    ap.add_argument("--no-community-defaults", action="store_true",
                    help="不装默认社区技能。默认会装 community-skills.json 里标了 default 的那几个")
    ap.add_argument("--gh-proxy", default="auto",
                    help="GitHub 加速前缀。'auto' 多路回退，'' 只用直连，或指定单个镜像")
    ap.add_argument("--no-mirrors", action="store_true", help="不生成 mirrors.env（国内加速环境变量）")
    ap.add_argument("--skill-dir", default=None,
                    help="显式指定技能投放目录。工作区制宿主（如 Reasonix）有多个工作区时必须给")
    ap.add_argument("--force-unverified", action="store_true",
                    help="允许写入未经核实的宿主路径。"
                         "默认拒绝 —— 必须先向用户确认真实路径，确认后才加这个开关")
    args = ap.parse_args()

    pack_names = [p.strip() for p in args.packs.split(",") if p.strip()]
    packs = load_packs(pack_names)
    all_hosts = load_hosts()

    if args.hosts:
        wanted = [h.strip() for h in args.hosts.split(",") if h.strip()]
        missing = [h for h in wanted if h not in all_hosts]
        if missing:
            raise SystemExit(f"[!] hosts.json 里没有这些宿主: {missing}。请先补 hosts.json。")
        target_hosts = {h: all_hosts[h] for h in wanted}
    else:
        target_hosts = detect_hosts(all_hosts)

    if not target_hosts and not args.dry_run:
        print("[!] 没有探测到任何已安装的宿主。")
        print("    请用 --hosts <名字> 显式指定，或让用户确认他用的哪个助手。")
        return 2

    # 未核实宿主：默认拒绝写入，除非用户已确认过要写的位置。
    # 判定粒度分开：
    #   · 技能目录 —— 给了 --skill-dir 就算已确认（用户点名了路径）
    #   · MCP 配置 —— 无法用参数指定路径，只能靠 --force-unverified
    # 在「装到什么位置」这种不可逆操作上，不能只靠文档提醒 agent 自觉。
    writes_mcp = any(packs[p].get("mcp") for p in pack_names)
    needs_confirm = {}
    for h, s in target_hosts.items():
        if s.get("verified") is True:
            continue
        reasons = []
        if not args.skill_dir:
            reasons.append("技能目录")
        if writes_mcp and not args.force_unverified:
            reasons.append("MCP 配置")
        if reasons and not args.force_unverified:
            needs_confirm[h] = (s, reasons)

    if needs_confirm and not args.dry_run:
        print("[!] 以下宿主的路径未经核实，已停止以免写错位置：")
        for h, (s, reasons) in needs_confirm.items():
            print(f"      {h}（{s.get('display')}）  verified={s.get('verified')}"
                  f"  待确认：{'、'.join(reasons)}")
            if s.get("confirm_hint"):
                print(f"        怎么确认：{s['confirm_hint']}")
            print(f"        推测路径：{s['skills'][0]}  |  MCP: {resolve_mcp_file(s['mcp'])}")
        print()
        print("    请先让用户确认真实路径，然后：")
        print("      · 技能目录用 --skill-dir <路径> 指定")
        print("      · MCP 路径确认后加 --force-unverified 放行")
        print("    （只想看看会做什么，可以先加 --dry-run，它不会写任何东西。）")
        return 3

    if unverified := {h: s for h, s in target_hosts.items() if s.get("verified") is not True}:
        if args.force_unverified and not args.dry_run:
            print(f"[i] 已用 --force-unverified 放行未核实宿主: {', '.join(unverified)}")
            print()

    python_exe = resolve_python_exe()
    tier_limit = 0 if args.tier == "none" else TIER_ORDER[args.tier]

    try:
        skills = plan_skills(pack_names, packs, target_hosts, args.skill_dir)
        mcps = plan_mcp(pack_names, packs, target_hosts, minimal=args.minimal_mcp)

        # 社区技能：标了 default 的默认装（如 ppt-master / anthropics-skills），
        # 其余的靠 --with-community 点名。技能只加载 description，比 MCP 便宜得多，
        # 所以默认装几个高价值的划算。
        entries = load_community()
        selected: list[str] = []
        if not args.no_community_defaults:
            selected += [e["id"] for e in entries if e.get("default")]
        if args.with_community:
            if args.with_community == "all":
                selected = [e["id"] for e in entries]
            else:
                selected += [x.strip() for x in args.with_community.split(",") if x.strip()]
        selected = list(dict.fromkeys(selected))
        community = (plan_community(entries, selected, target_hosts, args.skill_dir)
                     if selected else [])
    except AmbiguousSkillsDir as exc:
        print(f"[!] {exc.host} 上找到多个候选技能目录，无法自动决定：")
        for c in exc.candidates:
            print(f"      {c}")
        print()
        print("    这是工作区制宿主（如 Reasonix）的正常情况 —— 每个工作区各有独立技能目录。")
        print("    请用户确认当前用哪个工作区，然后用 --skill-dir 指定，例如：")
        print(f"      python3 scripts/apply.py --packs <包> --skill-dir '{exc.candidates[0]}'")
        return 4

    py_deps = [] if args.no_python_deps else collect_python_deps(pack_names, packs)
    cli_deps = [] if args.no_cli else collect_cli_deps(pack_names, packs)

    if args.dry_run:
        print(render_plan(skills, mcps, py_deps, cli_deps, packs, pack_names,
                          python_exe, tier_limit, community,
                          args.minimal_mcp, not args.no_mirrors, args.gh_proxy))
        return 0

    state = load_state()
    state["hosts"] = sorted(set(state.get("hosts", [])) | set(target_hosts.keys()))
    state["packs"] = sorted(set(state.get("packs", [])) | set(pack_names))

    results = []
    for action in skills:
        results.append(do_skill(action, state))
    for action in mcps:
        results.append(do_mcp(action, state))
    for action in community:
        results.append(do_community(action, args.gh_proxy, state))
    for dep in py_deps:
        if TIER_ORDER.get(dep.get("tier", "light"), 1) <= tier_limit:
            results.append(do_python_dep(dep, python_exe, args.pypi_mirror, state))
    for dep in cli_deps:
        # 已装未在 PATH 的，无论档位都建 shim（不下载，零成本）
        probe = cli_probe(dep)
        if probe["state"] == "off_path" or TIER_ORDER.get(dep.get("tier", "light"), 1) <= tier_limit:
            results.append(do_cli_dep(dep, tier_limit, state))

    if not args.no_mirrors:
        env_path = write_mirrors_env()
        state["mirrors_env"] = str(env_path)

    save_state(state)

    print(f"agent-starter-kit v{VERSION} 安装完成（能力包: {', '.join(pack_names)}｜宿主: {', '.join(target_hosts) or '无'}）")
    print()
    for line in results:
        print("  " + line)
    print()
    print(f"PATH shim 目录: {SHIM_DIR}")
    if any("shim" in r for r in results):
        print(f"  ⚠ 请确保 {SHIM_DIR} 已在 PATH 中，否则 shim 不生效")
    if not args.no_mirrors:
        print(f"国内加速环境变量: {STATE_DIR / 'mirrors.env'}")
        print(f"  用法: source {STATE_DIR / 'mirrors.env'}")
    print()
    print("下一步：运行  python3 scripts/doctor.py  做自检。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())