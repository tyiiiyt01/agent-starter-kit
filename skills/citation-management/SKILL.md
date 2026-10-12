---
name: citation-management
description: 管理参考文献：用 zotero-mcp 连接 Zotero、导出并维护 BibTeX、用 pandoc 配合 CSL（gb.csl 对应 GB/T 7714）生成规范引用，处理各类文献字段与去重。当用户要整理参考文献、管理 Zotero 库、生成 BibTeX 或按国标输出引用时使用。
---

# 参考文献管理

目标：文献信息**真实、可追溯**，引用格式**自动生成、不手敲**。

## 0. 铁律

- **绝不编造引用信息**（作者、年份、期刊、页码、DOI），必须来自真实来源
- 拿不准的字段**宁可留空并标注**，也不要猜
- 格式靠工具生成，不要手动排版参考文献表

## 1. zotero-mcp（连接 Zotero 库）

安装：

```bash
uv tool install zotero-mcp-server
zotero-mcp setup
```

⚠️ 前提：在 **Zotero 7** 里打开 "Allow other applications on this computer to communicate with Zotero"（设置 → 高级 / 本地 API），否则连不上。

配好后可以让 AI 直接检索本地 Zotero 库、按条件取条目、导出 bib。

## 2. BibTeX 工作流

BibTeX 是通用交换格式（Zotero、pandoc、LaTeX 都认）。

用 pandoc 生成规范引用：

```bash
pandoc thesis.md -o thesis.docx --citeproc --bibliography=refs.bib --csl=gb.csl
```

- `--citeproc`：pandoc 内置引用处理
- `--bibliography=refs.bib`：文献库
- `--csl=gb.csl`：输出样式

⚠️ **CSL 样式文件必须单独下载**：

- `gb.csl` 对应 **GB/T 7714**（中文学位论文 / 期刊常用）
- CSL 文件来自 **CSL 官方仓库**（Zotero Style Repository / `citation-style-language/styles`）
- 下载后放到工作目录，`--csl=` 指到本地文件路径

## 3. 常见文献类型的 BibTeX 字段要点

| 类型 | entry | 关键字段 |
|---|---|---|
| 期刊论文（J） | `@article` | author, title, journal, year, volume, number, pages, doi |
| 学位论文（D） | `@phdthesis` / `@mastersthesis` | author, title, school, year |
| 会议论文（C） | `@inproceedings` | author, title, booktitle, year, pages, publisher |
| 专著（M） | `@book` | author, title, publisher, year, address |
| 电子资源（EB/OL） | `@misc` / `@online` | author, title, year, url, urldate |
| 报告（R） | `@techreport` | author, title, institution, year, number |

规则要点：

- `author` 多人用 `and` 连接（**不是逗号**）；`pages` 用 `--` 双连字符
- key 命名 `第一作者姓+年份+关键词`，全库唯一
- 有 DOI 必须填
- 类型标识（J/M/D/C/EB/OL/R）在 GB/T 7714 里必须写全

## 4. 去重

- 判定顺序：DOI > 标题+年份 > 标题
- 合并时保留字段更全的那条，补齐缺失字段
- 预印本与正式版是不同条目，用 `related` 或备注关联，别直接删

## 5. 批量改格式 / 导出子集

- 改格式：**改 CSL 文件**，不要逐条手改；同一份 bib 换不同 csl 就能出不同期刊格式
- 导出子集：按关键词、年份、标签筛选后只导出选中条目
- 转换：Zotero 可导出 BibTeX；知网等导出 EndNote / RefWorks 格式后，可转成 BibTeX

## 6. 常见坑

- CSL 文件没下载 → pandoc 报错或退回默认样式，输出格式不对
- 用逗号连接作者 → BibTeX 解析错
- 手动敲参考文献 → 增删一条就序号全乱，且容易抄错
- 缺 `doi` / `pages` → 引用不完整
- 编造 DOI 或年份 → 学术不端，绝对禁止