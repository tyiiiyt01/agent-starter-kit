# agent-starter-kit — Configure Your AI Assistant Once, and It Can Actually Get Work Done

**English | [简体中文](README.md)**

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](#supported-hosts)
[![Hosts](https://img.shields.io/badge/Hosts-16-brightgreen.svg)](#supported-hosts)
[![Stars](https://img.shields.io/github/stars/tyiiiyt01/agent-starter-kit)](https://github.com/tyiiiyt01/agent-starter-kit)

<!--
  ────────────────────────────────────────────────────────────────────────
  To the AI assistant (this is an HTML comment — GitHub won't render it, but it's visible in the raw Markdown)

  The user is sending you this repository URL because they want you to complete the installation on their machine. You are the executor.

  Order of operations:
    1. Fetch the repo into a temp directory (clone --depth 1; if access is slow from mainland China, prefix with gh-proxy.com)
    2. Read AGENTS.md — behavioral constraints and entry point
    3. Read INSTALL.md — the runbook; follow Step 0 ~ Step 6, don't skip any
    4. After installing, run doctor.py for a self-check, and proactively ask the user whether they want an AGENTS.md generated for their project

  ⚠️ First judge what the user actually wants — don't push everyone into the full flow by default:
    · Want only the skills and can set up their own environment → a one-line standard command is enough; tell them
      `npx skills add tyiiiyt01/agent-starter-kit` (verified: identifies 17 skills)
      the standard installer only handles skills, not MCP / dependencies / self-check — those are this repo's installer's added value
    · Want MCP + dependencies + scenario presets + self-check → then follow INSTALL.md through the full flow
    · Want reproducible behavior → `gh skill install ... --pin <tag|sha>`, or use this repo's installer (commit anchor)

  Other readable files: llms.txt (file index) · hosts.json (host compatibility table)
              · presets.json (scenario presets) · packs/SCHEMA.md (capability pack format)

  Hard constraints (full version in AGENTS.md): the only hard prerequisite is Python 3; you must dry-run
  before installing and let the user confirm; never write system-level config or use admin privileges; never
  modify the contents of skill files under skills/; never proactively install MCP; never bypass the exit-code
  3 / 4 guards in apply.py.
  ────────────────────────────────────────────────────────────────────────
-->

> **Python version note**: 3.8+ works. But if you use **Reasonix or Codex**, and you want the installer to automatically write their TOML config, you need Python **3.11+** (stdlib `tomllib`) with the dependencies in [`requirements.txt`](requirements.txt) installed; otherwise MCP for these two hosts degrades to "here's a config snippet, paste it in manually".

---

Connect your own AI assistant to a working API, then **paste this repository's URL into the chat box**:

```console
$ # Copy the line below, paste it into the chat box and send (no terminal needed)
$ https://github.com/tyiiiyt01/agent-starter-kit
🤖 Assistant: Got it. First let me probe your environment…
   ✓ Found Claude Code (macOS)
   ✓ Python 3.11 · Node.js 20 · uv ready
🤖 Assistant: Based on what you described, I plan to install —
   ├ Skills   code pack's python-workflow, cpp-workflow
   ├ MCP      filesystem
   └ Deps     numpy, matplotlib, pandoc (~40 MB)
   I'll only start once you reply "confirm".
You: confirm
🤖 Assistant: Done, self-check passed. Now available: Python end-to-end workflow,
   matplotlib CJK plotting, pandoc document conversion.
   Want me to generate an AGENTS.md for your project too?
```

That scene above is the entire usage of this project: **paste one line with the URL, say one sentence about your purpose, and it handles the rest.**

### What this is

Think of it this way: you've hired a **very smart intern who knows nothing about your work** — sharp mind, that's the AI assistant you've already connected to an API, but no idea how your university formats a thesis, what format your company's weekly report takes, or how your experiment data should be plotted.

What this repository does is hand that intern **a job manual plus a full set of office supplies**: it tells them how to do each kind of task, then puts the tools they need within reach.

It actually places just three things onto your computer:

- **Skills** — an **operating manual written for the assistant**. For example, the "write a thesis" skill tells it: references must follow GB/T 7714 (the Chinese national standard for bibliographic references), Chinese text in figures must not render as boxes, and what pitfalls the school template has. It couldn't do these things before; install the skill and it can.
- **MCP** — **extra interfaces / plugins** for the assistant, letting it actually operate files, web pages, and more on your machine instead of just chatting with you. This kit is deliberately restrained here and installs only what is truly necessary.
- **Dependencies** — the **tools** that actually do the work behind the skills (e.g. Python libraries for plotting, pandoc for document conversion). Skills are the "instructions"; dependencies are the "machine the instructions run on".

### What hassle this saves me

**Without it**, you'd have to do all of this yourself: dig through tutorials, type out install commands one by one (which `pip install` packages, which versions — all guesswork), hunt the world over for good skill files, hand-edit the assistant's config to add plugins, and still often get stuck on inexplicable "it's installed but the assistant says it can't find it" problems (jargon: **PATH** issues).

**With it**: environment probing, skill selection, dependency installation, and self-check verification all go to your assistant; before it acts, it lays the list in front of you, and it only starts after you say "confirm". Your entire job is two things — **paste the URL, click confirm**.

📖 Quick start · 🧩 [Capability list](#eight-capability-packs--seventeen-skills) · ❓ [FAQ](#faq) · ⬆️ [Updating](#updating) · 🗑️ [Uninstalling](#uninstalling)

## Table of contents

- [Why use it](#why-use-it)
- [What it actually does](#what-it-actually-does)
- [What it doesn't do](#what-it-doesnt-do)
- [Quick start](#quick-start)
- [Supported hosts](#supported-hosts)
- [Scenario presets](#scenario-presets)
- [Eight capability packs · Seventeen skills](#eight-capability-packs--seventeen-skills)
- [Keep MCP minimal](#keep-mcp-minimal)
- [High-star community skills](#high-star-community-skills)
- [Dependency tiers](#dependency-tiers)
- [Networks in mainland China](#networks-in-mainland-china)
- [Security and boundaries](#security-and-boundaries)
- [FAQ](#faq)
- [Updating](#updating)
- [What to do when something goes wrong](#what-to-do-when-something-goes-wrong)
- [Uninstalling](#uninstalling)
- [Repository layout](#repository-layout)
- [Contributing](#contributing)
- [License](#license)

## Why use it

- **No technical knowledge required** — just say "I want to write my graduation thesis" and it figures out what to install, how, and how to verify it. All you do is **paste the URL and confirm**.
- **Install the whole set at once** — 17 skills across five directions (coding, literature, data, office, study), all in one go. **So what**: no more "find a plotting skill today, set up a literature tool tomorrow" — you save an entire afternoon of assembling and debugging.
- **What gets installed is deterministic** — skill files are byte-for-byte identical, so your machine's result matches everyone else's, and you see the list before anything happens. **So what**: no mystical "it works for others but errors on my machine" differences.
- **Cures "installed but unusable"** — it auto-detects tools missing from PATH and adds a forwarding script, and the self-check **actually executes** them to confirm they run rather than just checking that files exist. **So what**: no more "it's installed but the assistant says it can't find it".
- **Doesn't make the AI dumber** — each pack attaches only the few plugins it truly needs (measured: 3 of them already consume 72% of a 200k context). **So what**: it won't get slower and more forgetful the more you install.
- **Low cost of trial and error** — you can dry-run first, keep a ledger of "what was installed", and uninstall with one instruction, removing only the entries it installed itself. **So what**: safe to try, safe to roll back, no fear of messing up your computer.

## What it actually does

No feature names — plain language. Here are the concrete moments it works for you:

- **Writing lab reports**: you have experimental data. Previously you'd format it yourself, tweak the figure fonts yourself (Chinese often renders as boxes), and apply the school template. Now send it the data, say "write this up as a lab report", and it produces a `.docx` you can hand in directly.
- **Writing a graduation thesis**: search the literature, deep-read PDFs, format to the school template, and normalize references into a proper citation format — it walks beside you step by step, and you never adjust styles by hand.
- **Cleaning up data**: a pile of messy Excel / CSV files. Tell it what dimensions to aggregate by and what charts to make; it handles cleaning, computation, and plotting, with CJK labels that don't turn into mojibake.
- **Classes and homework**: send it the slides or a problem set, and it explains the reasoning, breaks down the steps, and generates similar problems for practice (**explanation and guidance only, no answers**).
- **Everyday office work**: turn a meeting recording or shorthand into minutes; batch-generate documents from a template; convert between PDF / Word / spreadsheets.

> **One honest boundary**: the documents it produces aim for "**structurally correct, properly formatted, ready to use**", **not "beautifully designed"**. A full deck with real design polish needs the community `ppt-master` skill on top (see [High-star community skills](#high-star-community-skills)); the charts in a report are "clear, standard, no CJK mojibake", not "magazine-grade visuals". We'd rather under-promise than have you install it and be disappointed.

## What it doesn't do

This thing only does what it should. The following it **explicitly does not do**:

- **Doesn't ghostwrite homework** — academic integrity comes first; it gives explanations, step-by-step guidance, and verification, not answers.
- **Doesn't bypass paywalls** — for paid databases like CNKI (China National Knowledge Infrastructure, the country's main academic database), it only does compliant searching and offers no way around access restrictions.
- **Doesn't install commercial software** — e.g. MATLAB (commercial license, tens of GB): if detected, it uses it; if not, it falls back to Octave for `.m`-compatible syntax.
- **Doesn't manipulate running Office windows** — file-level read/write only (`.docx` / `.xlsx` / `.pptx`); it never touches the Word window you have open.
- **Doesn't silently change the system** — no system-level config, no admin privileges, no quietly changing your settings; everything installs into your user directory. Anything that needs a system prompt to confirm (e.g. installing Xcode Command Line Tools on macOS) will guide you to click it yourself.

## Quick start

**One thing to get straight first**: this repository is essentially **a batch of standard skills** — `skills/<name>/SKILL.md`, 17 in total, conforming to the Agent Skills spec. So you can **install it just like any other skill**, without going through the installer below.

Three paths — pick the one that fits you:

### ① Want only the skills → a one-line standard command

```bash
npx skills add tyiiiyt01/agent-starter-kit
```

**Verified result**: it identifies all 17 skills, installs them into `~/.agents/skills/`, then creates links in the skills directories of the tools you already have installed (Claude Code / Cursor / Codex…).

Common variants:

```bash
npx skills add tyiiiyt01/agent-starter-kit --list          # see what skills are available first
npx skills add tyiiiyt01/agent-starter-kit --skill xlsx     # install just one
npx skills add tyiiiyt01/agent-starter-kit -g               # install at the user level (global)
```

> ⚠️ Two caveats, found by testing:
> 1. **Requires Node ≥ 22.20** (lower versions emit a warning, though it may still run)
> 2. **It uses symlinks, not copies** — and on Windows creating symlinks requires admin privileges or Developer Mode, so it may fail. This kit's installer **deliberately uses copies** precisely to avoid this

### ② Want "skills + MCP + dependencies + self-check" → paste the URL to your AI assistant (recommended)

**The standard skill installer only handles skills.** MCP registration, Python dependencies, command-line tools, scenario presets, and self-check — **no standard mechanism can do any of these**, because every host's MCP config format differs (JSON / TOML, dictionaries / arrays of tables).

Paste this repository's URL into the chat box and add a one-line purpose:

```
https://github.com/tyiiiyt01/agent-starter-kit I want to write a graduation thesis
```

Your assistant probes the environment itself, matches a scenario, and prints a list; **it only acts after you confirm**, then runs a self-check and tells you which capabilities are now available.

> You don't need to know the command line — it will guide you. At the end it also asks: **do you want an `AGENTS.md` generated for the current project** — say yes; this is the single most worthwhile setup for a beginner, letting the AI remember your project's conventions so you don't have to repeat them every time.

**It reads these files in the repo to do its job** (your assistant reads them; you don't have to):

| File | What it's for |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Behavioral constraints — what it's allowed and forbidden to do |
| [`INSTALL.md`](INSTALL.md) | Runbook, Step 0 → Step 6 |
| [`llms.txt`](llms.txt) | File index — see at a glance which files in the repo matter |
| [`hosts.json`](hosts.json) · [`presets.json`](presets.json) | Host compatibility table · scenario presets |

> To check exactly what it will do, open any of the files above and see for yourself — it's all plain text, no hidden logic.

### ③ Want a pinned version (when you need reproducible behavior)

```bash
gh skill install tyiiiyt01/agent-starter-kit --all --pin v0.2.3
```

`gh skill install` supports `--pin <tag|sha>` to pin to a specific version. This kit's own installer does the same thing with commit anchors (see [SECURITY.md](SECURITY.md) section 3.4).

### Installing only a few packs / adding community skills

Name the packs directly (see "Eight capability packs" below), e.g.: `use agent-starter-kit to install the code and study packs for me`; community skills work too: `also add ppt-master`.

> When it can't match your purpose, it defaults to installing only `code` (the minimum usable set) and tells you that you can add more anytime.

### Comparison of the three approaches

| | ① Standard command | ② Paste to AI assistant | ③ Pinned version |
|---|---|---|---|
| Skills | ✅ 17 | ✅ | ✅ |
| MCP registration | ❌ | ✅ | ❌ |
| Python / CLI dependencies | ❌ | ✅ | ❌ |
| Scenario presets (one-sentence customization) | ❌ | ✅ | ❌ |
| Self-check (really runs to verify) | ❌ | ✅ | ❌ |
| Version pinning | default branch | commit anchor verified | ✅ `--pin` |
| Who it's for | people who can set up their own environment | users unfamiliar with the environment | people who need reproducibility |

## Supported hosts

**16** (11 paths verified against official docs / 5 partially verified / 0 unverified):

| Host | Skills directory | MCP config | Verified |
|---|---|---|---|
| Claude Code | `~/.claude/skills/` | `claude mcp add --scope user` | ✅ |
| Cursor | `~/.cursor/skills/` · `~/.agents/skills/` | `~/.cursor/mcp.json` | ✅ |
| Trae (international) | `~/.trae/skills/` · `~/.agents/skills/` | `<config dir>/User/mcp.json` | ✅ |
| Trae CN (China) | `~/.trae-cn/skills/` · `~/.agents/skills/` | `<config dir>/User/mcp.json` | ⚠️ |
| Codex CLI | **`~/.agents/skills/`** | `~/.codex/config.toml` | ✅ |
| Gemini CLI | `~/.gemini/skills/` · `~/.agents/skills/` | `~/.gemini/settings.json` | ✅ |
| Qwen Code (Tongyi) | `~/.qwen/skills/` · `~/.agents/skills/` | `~/.qwen/settings.json` | ⚠️ |
| Windsurf | `~/.codeium/windsurf/skills/` | `~/.codeium/windsurf/mcp_config.json` | ✅ |
| Cline (VS Code extension) | `~/.cline/skills/` · `~/.agents/skills/` | `~/.cline/data/settings/cline_mcp_settings.json` | ✅ |
| Roo Code (VS Code extension) | `~/.roo/skills/` · `~/.agents/skills/` | inside VS Code globalStorage | ⚠️ |
| Zed | `~/.agents/skills/` | `~/.config/zed/settings.json` (section `context_servers`) | ✅ |
| OpenCode | `~/.config/opencode/skills/` | `~/.config/opencode/opencode.json` (section `mcp`) | ✅ |
| GitHub Copilot CLI | `~/.copilot/skills/` · `~/.agents/skills/` | `~/.copilot/mcp-config.json` | ✅ |
| Kiro (AWS) | **no skill support** | `~/.kiro/settings/mcp.json` | ✅ |
| Amp (Sourcegraph) | **no skill support** | `~/.config/amp/settings.json` | ⚠️ |
| Reasonix | workspace-local `.reasonix/skills/` (workspace-based) | `[[plugins]]` in `~/.reasonix/config.toml` | ⚠️ |

### About the shared `.agents/skills/` directory

Several hosts **all recognize** the `.agents/skills/` convention: Cursor, Trae, Codex, Gemini CLI, Cline, Roo Code, Zed, GitHub Copilot.

So if you have more than one of these tools installed, **writing skills there once makes them readable by all of them** — no need to install per tool.

### Three cases needing special handling

- **Reasonix is workspace-based** — skills go inside the workspace at `.reasonix/skills/`, and different workspaces have separate directories. During install it asks you "which workspace are you currently using" rather than guessing.
- **Kiro / Amp don't support skills** — they only use the steering / AGENT.md mechanism, so this kit only registers MCP for them and **does not install skills**. This isn't a failed install; it's a limitation of the tools themselves.
- **Codex needs a restart after config changes** — restart Codex after installing for it to take effect.

### These tools currently can't be supported

| Tool | Reason |
|---|---|
| Aider | Neither native MCP nor SKILL.md support |
| Continue.dev | Its MCP config is YAML, and the script only handles JSON/TOML |
| Copilot inside VS Code | Config is **project-level** `.vscode/mcp.json`, not user-level |
| Kilo Code / Warp | Paths vary too much by form factor, or it's a terminal tool — left out for now to avoid writing to the wrong place |

> Hosts marked ⚠️: the paths come from analogous inference or community sources, not officially confirmed. **During install the AI first asks you to confirm the real path**, and the self-check re-verifies afterward — it won't silently write to the wrong place. The evidence behind the paths in the table is in the `_source` field of [`hosts.json`](hosts.json) (each entry carries a link to the official docs).

## Scenario presets

You don't need to name packs — just say "I want to write a graduation thesis" and the AI knows what to install:

| You say | It installs |
|---|---|
| I want to write a graduation thesis | `research` `writing` |
| I'm entering a mathematical modeling contest (CUMCM, the China Undergraduate Mathematical Contest in Modeling) | `math-modeling` `code` `writing` |
| I'm taking major courses / preparing for exams | `study` `code` |
| I work at a company | `office` `office-work` |
| I do student affairs / make promotional material | `design` `office` |
| I do research / publish short papers | `research` `writing` `math-modeling` |
| STEM course assignments | `code` `study` `writing` |
| All of it | install all eight packs |

## Eight capability packs · Seventeen skills

| Pack | For | Skills |
|---|---|---|
| `code` | Writing code | `python-workflow` (Python end-to-end workflow + matplotlib CJK fonts) · `cpp-workflow` (C++ build + Octave fallback for `.m`) |
| `research` | Literature search and investigation | `paper-research` (search + deep PDF reading + GB/T 7714) · `cn-literature` (compliant search of Chinese-language literature) · `citation-management` (Zotero + BibTeX) · `web-research` (web scraping and data research) |
| `math-modeling` | Mathematical modeling contests | `math-modeling` (problem analysis → modeling → solving → sensitivity → writing, with a solver selection table) |
| `writing` | Writing papers | `thesis-format` (apply the school template) · `academic-figures` (600 dpi / vector / CJK fonts) · `lab-report` (error propagation + fitting) |
| `office` | Documents and data | `office-docs` (file-level read/write of docx/xlsx/pptx/pdf) · `data-analysis` (pandas cleaning) · `doc-batch` (docxtpl batch generation) |
| `office-work` | Office collaboration | `meeting-notes` (meeting transcription to minutes) · `email-calendar` (email and calendar) |
| `study` | Studying | `study-tutor` (explaining major courses + guiding exercises + OCR→LaTeX) |
| `design` | Design assets | `design-material` (batch image processing, poster material, QR codes, CJK fonts) |

**The Office capabilities are all implemented with pure Python libraries** (python-docx / openpyxl / python-pptx / pypdf / docxtpl), with no dependency on an Office client and no third-party Office MCP — one less runtime layer, one less point of failure.

## Keep MCP minimal

This runs counter to "more is better". Measured data: **3 MCPs already consume 143k tokens (72%) of a 200k context**, and 7 MCPs burn 67,300 tokens on the first turn. **Install too many MCPs and the agent gets noticeably dumber.**

So this kit is designed like this:

- Each pack attaches **only the few MCPs it truly needs**, not a "must-install top ten MCPs".
- Each pack marks one as `essential`; with `--minimal-mcp` you keep only that one.
- If the AI feels slow or forgets what you said earlier — it's most likely MCPs eating the context; try `--minimal-mcp`.

## High-star community skills

The following are optional add-ons. Besides the 17 built-in skills, `community-skills.json` also catalogs a list of high-star community skills you can add as needed:

| Skill | Stars | Description |
|---|---|---|
| `anthropics-skills` | ~180k | Anthropic's official docx / pptx / xlsx / pdf four-pack |
| `obra/superpowers` | ~296k | Engineering-methodology meta-skill (heavyweight; suited to people who code often) |
| `ui-ux-pro-max-skill` | ~133k | UI / design |
| `ppt-master` | ~61k | Generate a full designed PPT deck from scratch |
| `cloudflare/security-audit-skill` | ~28k | Security review |
| `MathModeling-skills` | ~1.06k | Staged workflow for mathematical modeling |

**None are installed by default** — that's deliberate. Community skills are third-party repositories with three problems you can't ignore:

| Problem | Example |
|---|---|
| **License constraints** | `anthropics/skills` uses a **proprietary license** that explicitly forbids extracting/copying/deriving/distributing |
| **Questionable provenance** | `ppt-master` was created 2025-12 and hit ~60k stars almost immediately — the growth curve is implausible |
| **Excessive size** | `ppt-master`'s skill directory measures about **78 MB** |

None of them is suitable as a "trust by default" object. Install by name when you want them:

```bash
python3 scripts/apply.py --packs code --with-community ppt-master   # name one
python3 scripts/apply.py --packs code --with-community all          # all 13
```

Once installed, each item gets three layers of protection:

1. **Pinned version** — every entry carries a `commit` anchor, verified after cloning, **aborted on mismatch**
   (git's own checks can't stop a mirror from swapping contents; only comparing against the anchor can)
2. **Executable code is listed** — the report says "contains N executable scripts" and shows you the items that
   match high-risk patterns (curl pipe execution, touching key paths, hardcoded-IP outbound calls)
3. **No endorsement of third parties** — **this kit only pins versions and scans patterns; it does not audit code**. A scan with no hits does not mean it's safe

> ⚠️ This also means: for anything installed with `--with-community`, it's best to glance over the repository yourself first. You're downloading
> someone else's code — that's not the same as installing a package that ships with the system.

## Tools that can't be installed automatically get official download links

Some things the AI can't install — MATLAB (needs a license), anything needing admin privileges (Xcode CLT, MSVC, LibreOffice), or things that are enormous (TeX Live). In those cases the kit doesn't vaguely say "go install it yourself" — it pulls **the official download page, per-platform install commands, and a verification method** from [`manual-installs.json`](manual-installs.json).

17 tools are cataloged, including Python / Git / Node / uv / MATLAB / Octave / LibreOffice / TeX / pandoc / ffmpeg / Zotero and more. Take MATLAB as an example — what you get is more than just a URL:

```
Official download: https://www.mathworks.com/downloads/
China site (faster): https://www.mathworks.cn/downloads/
First check whether your school has a license → register with your school email, visit mathworks.com/academia to check for a Campus-Wide license
Even without a license it's fine → start with GNU Octave (free, highly syntax-compatible): https://octave.org/download
```

> ⚠️ These are all third-party repositories with **different licenses** (some MIT, some with redistribution restrictions). The `license_risk` field in the list flags the risk, and you're prompted about it during install.

## Dependency tiers

This section matters — don't skip it. For the skills to run, they need key tools. This kit splits them into three tiers by size and **installs only the lightweight tier by default**:

| Tier | Examples | Size | Policy |
|---|---|---|---|
| `light` | pandoc · poppler · markitdown · tectonic · scipy | tens of MB | installed automatically by default |
| `medium` | pdf2zh (with translation models) · scikit-learn | 100MB–1GB | requires `--tier medium` |
| `heavy` | LibreOffice (≈700MB) | >1GB | **never installed automatically**; detect + guide only |

### The antidote to "installed but unusable"

Many things **are installed but not on PATH**, so commands can't reach them — this is the most common failure mode of this whole setup. For example, on macOS LibreOffice lives at `/Applications/LibreOffice.app/Contents/MacOS/soffice`, pandoc's official single-file installer doesn't write to PATH, and TinyTeX's links land in `/usr/local/bin` — these directories are often not on PATH.

So the kit auto-detects these **known locations**, and on a hit creates a forwarding script (shim) to fix it; the self-check then **actually executes** them to confirm they're usable — not just checks that files exist.

### Two more things done to reduce reliance on heavy packages

1. **Prefer `PyMuPDF` for PDF handling** (pure pip, no sudo, no poppler binary needed); install poppler only when its command line is truly required.
2. **Prefer `tectonic` for LaTeX compilation** (a single binary of about 50 MB, downloads macro packages on demand) rather than TinyTeX / MacTeX (over 1 GB).

## Networks in mainland China

This part decides whether the install succeeds. Direct connections to GitHub Releases often drop to **30 KB/s**, and anything hundreds of MB just stalls. This kit has multi-path acceleration built in:

- **GitHub**: automatically falls back `direct → gh-proxy.com → ghfast.top → ghproxy.net → hub.gitmirror.com` (these are mirror accelerators commonly used in China for GitHub and Hugging Face, where direct access is very slow)
- **Generates a mirror config file** `~/.agent-starter-kit/mirrors.env`; `source` it once and it takes effect:

| Variable | Value | Why |
|---|---|---|
| `PIP_INDEX_URL` | Tsinghua PyPI mirror | pip's direct connection is very slow from China |
| `HF_ENDPOINT` | `https://hf-mirror.com` | **the most important** — speech transcription / PDF translation tools must download models first, and without this they won't download |
| `NPM_CONFIG_REGISTRY` | `https://registry.npmmirror.com` | same for npm |
| `PYTHONUTF8` | `1` | avoids CJK mojibake on Windows |

> ⚠️ Public mirrors risk going down or being rate-limited, and **must not be used for private repositories**. Mirrors fail fast, which is why we build in multi-path fallback rather than hardcoding one.

## Security and boundaries

> ⚠️ **Read this section before you start.** The core promise of this kit is "**visible, you decide, reversible**".

- **What gets installed, and in what shape, is fully deterministic** — skill files are byte-for-byte identical, so your machine's result matches others'.
- **You see the list before anything is installed**, and it acts only after you confirm; `scripts/apply.py --dry-run` lets you rehearse without writing anything.
- **Inspectable and removable**: `uninstall.md` gives uninstall instructions and removes only entries this kit installed.
- Throughout, it **never touches system-level config** and never writes to directories needing admin / root privileges (everything goes into your user directory).
- **Never touches your API keys, accounts, or login credentials**.
- ⚠️ **No paywall bypass**: it doesn't provide a way around paid databases like CNKI — compliant search only.
- ⚠️ **No ghostwriting homework**: academic integrity first; "problem-solving ability" = explanation + step-by-step guidance + verification, not answers.

## FAQ

**Q: Do I need to know the command line?**
No. You only paste the repo URL into the chat box, reply with a purpose, and confirm the list; probing, installing, and verifying are all done by the assistant, which guides you step by step.

**Q: What does it install on my machine?**
Three kinds, all listed for your confirmation before anything happens: ① skill files (a batch of Markdown placed into your assistant's skills directory); ② MCP config (merged into your assistant's config file, or registered via the host's own command); ③ dependencies (Python packages + command-line tools; by default only the tens-of-MB lightweight tier). The kit keeps a ledger at `~/.agent-starter-kit/state.json`, so what was installed is clear at a glance.

**Q: What if it breaks something?**
Uninstall per [`uninstall.md`](uninstall.md). It removes only the entries recorded in the ledger and never touches MCP, skills, or files you configured yourself. Note: Python packages and command-line tools are **not uninstalled automatically by default** (they may be used by your other projects); they're listed for you to decide.

**Q: Will it be slow / how much will I download?**
By default only the `light` tier, usually tens of MB. The `medium` tier (100MB–1GB) needs `--tier medium` explicitly; the `heavy` tier (e.g. LibreOffice, about 700MB) is **never installed automatically** — detect and guide only.

**Q: I have no API key and haven't connected an API — can I use it?**
No. **Having an AI assistant installed and connected to a working API is a hard prerequisite** — the whole process is executed by your assistant. Also, Python 3.8+ is the only hard environment requirement (and on Windows it avoids the "Microsoft Store stub" trap).

**Q: Can I install only part of it?**
Yes. Either name the packs directly ("install code and study for me"), or state a purpose and let it match a scenario preset, or just say "install only the coding-related stuff". When it can't match, it defaults to installing only `code` and tells you that you can add more anytime.

**Q: Why are some things installed but unusable?**
Most are **PATH problems** — the program is on disk but its directory isn't on PATH, so commands can't reach it (e.g. macOS's LibreOffice, pandoc's single-file installer). The kit auto-detects known locations and creates a forwarding script (shim) to fix it, and the self-check really executes them to confirm. If it's still unreachable, run `apply.py` again (idempotent, won't reinstall) to rebuild the shim.

## Updating

Installation is **idempotent**: running it repeatedly won't reinstall, it only fills in what's missing and updates what's old.

- **Update to the latest**: paste the repo URL to the assistant **once more** and have it run the process again. It re-fetches the latest code and does a "delta install" against the current environment.
- **Pin a version** (recommended when you want reproducible behavior):

  ```bash
  git clone --branch v0.2.3 --depth 1 https://github.com/tyiiiyt01/agent-starter-kit
  ```

  The current latest release is `v0.2.3`. `--branch v0.2.3` pins behavior to that version so it no longer drifts with `main`; `--depth 1` fetches only that version.
  See [CHANGELOG.md](CHANGELOG.md) for the change log, and [SECURITY.md](SECURITY.md) section 3.4 for why pinning is recommended.
- **Just adding a pack / skill**: just say "also install the `design` pack" or "add `anthropics-skills`" — no need to redo the whole thing.

## What to do when something goes wrong

| Symptom | Try this first |
|---|---|
| A command is "installed but unreachable" | Have the assistant run `apply.py` once (idempotent) to rebuild the shim; or check whether the tool's directory is on PATH |
| The AI got slower and forgets earlier context | Most likely MCPs eating the context; have the assistant use `--minimal-mcp` to keep only `essential` |
| Downloads in China stall at a few KB/s | Use the mirrors in `~/.agent-starter-kit/mirrors.env`, or have the assistant retry with a GitHub accelerator prefix |
| A large dependency times out | Don't wait it out — have the assistant skip that item and use a substitute (e.g. poppler → PyMuPDF) |
| A skill didn't take effect | Have the assistant run `scripts/doctor.py` for a per-item self-check; it really executes them to verify |
| You want a full rollback | See "Uninstalling" below and remove entries one by one per the ledger |

> If you're truly stuck, send the assistant the **raw error text** — far more useful than describing "it doesn't work".

## Uninstalling

In one sentence: **have the assistant read [`uninstall.md`](uninstall.md) and perform the uninstall** (e.g. "uninstall agent-starter-kit per uninstall.md").

Key points:

- **The ledger is the source of truth**: it removes only the skills, MCP entries, and shims recorded in `~/.agent-starter-kit/state.json`.
- **Only what it installed itself**: MCP, skills, and files you configured elsewhere are left untouched.
- **Dependencies aren't uninstalled by default**: Python packages and command-line tools are listed and left to your decision (to avoid breaking unrelated projects).
- Before uninstalling it prints a list and **waits for your confirmation**.

## Repository layout

```
agent-starter-kit/
├── README.md             ← the file you're reading
├── AGENTS.md             ← the assistant's behavioral constraints (it reads this file automatically)
├── INSTALL.md            ← runbook (Step 0–6); the assistant follows this
├── llms.txt              ← file index, so the assistant can grasp the whole repo in one page
├── uninstall.md          ← uninstall instructions
├── SECURITY.md           ← security disclosure policy and this project's risk boundaries
├── CHANGELOG.md          ← version change log
├── LICENSE               ← Apache-2.0
├── requirements.txt      ← the install engine's own dependencies (tomli-w)
├── hosts.json            ← host compatibility table; adding a new host only touches this
├── presets.json          ← scenario presets ("I want to write a thesis" → which packs to install)
├── community-skills.json ← high-star community skill list (optional install, with stars and licenses)
├── templates/
│   ├── AGENTS.md.template            ← an AGENTS.md template for your own project
│   ├── claude-settings.json.template ← permission allowlist template
│   └── README.md                     ← how to use these two templates
├── scripts/
│   ├── detect.py         ← environment probing (read-only)
│   ├── apply.py          ← idempotent install, supports --dry-run / --tier / --minimal-mcp
│   ├── doctor.py         ← per-item self-check, verifying "it really runs"
│   ├── pin_commits.py    ← (maintainers) refresh the commit pins for community skills
│   └── check_release.py  ← (maintainers) verify version consistency before releasing
├── packs/                ← definitions of the eight capability packs + SCHEMA.md (format spec)
└── skills/               ← the seventeen skill files (byte-for-byte identical, must not be modified)
```

> Why both `AGENTS.md` and `llms.txt`? They don't conflict — they do different jobs:
> **`AGENTS.md`** is the **operating instructions** for "the agent that will do work on your machine" (what it may and may not do),
> **`llms.txt`** is the **read-only map** for "the agent that needs to understand this repo" (which files to read). This is current community practice.

## Contributing

Improvements welcome. A few hard rules:

- Before changing `packs/*.json`, read [`packs/SCHEMA.md`](packs/SCHEMA.md) — a wrong field name is **silently ignored**.
- Adding a skill: the directory name must match the `name` in `SKILL.md`'s frontmatter **exactly** (`doctor.py` checks this).
- Adding a host: only change `hosts.json`, no script changes needed.
- All scripts use only Python, with **no `.sh`** (the first cross-platform principle: `.sh` doesn't run on Windows); all writes are explicitly UTF-8 without BOM.
- Always self-test with a **fake HOME**; never test against your real config:

  ```bash
  HOME=/tmp/test-home python3 scripts/apply.py --packs code --dry-run
  HOME=/tmp/test-home python3 scripts/doctor.py
  ```

More conventions in [`AGENTS.md`](AGENTS.md), section 5.

## License

This project is released under the **Apache-2.0** license; see `LICENSE` for details.

**Third-party content notice**:

- The skill files under `skills/` in this repository are this project's own content and are released with it under Apache-2.0.
- `community-skills.json` catalogs **third-party open-source repositories**, each under its own original license (including MIT, CC-BY-4.0, and "unverified"), flagged by the `license` / `license_risk` fields; **confirm the upstream license yourself before downloading and using them**.
- Community skills are **not installed by default**; you specify them explicitly when you want them.