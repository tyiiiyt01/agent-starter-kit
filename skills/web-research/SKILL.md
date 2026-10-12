---
name: web-research
description: 把公开网页抓成结构化数据做调研与资料整理：先按「单页 → 多页/需渲染 → 批量反爬」分层选工具，再用 requests + beautifulsoup4 抓取、pandas 落地 CSV/Excel。当用户要抓网页、收集公开数据、整理行业信息、批量提取网页内容或做数据调研时使用。
---

# 网页抓取与数据调研

主体：**先分层选工具 → 再抓 → 再落地 → 全程合规**。

## 1. 分层策略（核心，别一上来就上重型工具）

按任务量级逐档升级，**能用第 1 档就别上第 3 档**：

| 档 | 场景 | 用什么 | 成本 |
|---|---|---|---|
| 1 | 单页 / 少量页面、静态内容 | **AI 自带的网页抓取能力**，零安装 | 最低 |
| 2 | 多页、需要渲染 JS、要落成脚本 | 轻量 MCP（`fetch`）或 Python `requests` + `beautifulsoup4` | 低 |
| 3 | 批量 / 结构化 / 有反爬 | 重型爬虫（Firecrawl 等），**需 API Key** | 高 |

⚠️ **重要**：装重型爬虫（注册、配 Key、计费、长期维护）的成本远高于收益。先用第 1 档试，真不行再往上升。绝大多数「帮我查几个网页」用第 1 档就够了。

## 2. Python 抓取骨架（第 2 档）

```bash
python3 -m pip install requests beautifulsoup4 lxml pandas tabulate
```

包名与 import 名不一致，别记混：

- `requests` → `import requests`
- `beautifulsoup4` → `from bs4 import BeautifulSoup`
- `lxml` 是解析器，配 `BeautifulSoup(html, "lxml")` 用

```python
import requests, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://example.com/list"
headers = {                                  # 带 UA，很多站点没有 UA 会直接拒绝
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept-Language": "zh-CN,zh;q=0.9",
}
resp = requests.get(url, headers=headers, timeout=15)   # 一定要设 timeout
resp.raise_for_status()

# ⚠️ 中文编码：不要信 resp.text，先校准编码（见第 3 节）
if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
    resp.encoding = resp.apparent_encoding
soup = BeautifulSoup(resp.text, "lxml")

rows = []
for li in soup.select("ul.news li a"):       # CSS 选择器，按页面结构改
    rows.append({
        "标题": li.get_text(strip=True),
        "链接": urljoin(url, li.get("href", "")),  # 相对路径拼成绝对 URL
    })
    time.sleep(1)                            # 逐条限速，见第 5 节合规
```

要点：

- **先看页面结构**再写选择器：浏览器里「检查元素」，确认标签 / class 稳定再用
- 用 CSS 选择器 `select()`，或 `find()` / `find_all()`；`get_text(strip=True)` 去空白
- 列表页链接多半是**相对路径**，必须 `urljoin(base, href)` 拼成绝对地址，否则二次抓取会 404

## 3. ⚠️ 中文网页编码坑（高频）

国内站点 `Content-Type` 里声明的编码常常**不准或干脆不写**（缺省会被 requests 当 ISO-8859-1），照 `resp.text` 直接读就**满屏乱码**：

```python
print(resp.encoding, resp.apparent_encoding)   # 先打印两者对比
resp.encoding = resp.apparent_encoding          # 用内容推断的编码兜底
```

- `resp.encoding`：来自 HTTP 头 / 猜测，可能错
- `resp.apparent_encoding`：由内容统计推断，更稳（近似依赖 `charset-normalizer`，装 requests 时会带上）
- 已知是 UTF-8 就直接 `resp.encoding = "utf-8"`；国内老站常见 `gbk` / `gb2312`
- 写 CSV 给 Excel 看时用 `encoding="utf-8-sig"`，否则 Excel 打开乱码

## 4. 数据落地：pandas + tabulate

```python
import pandas as pd
from tabulate import tabulate

df = pd.DataFrame(rows)
df.to_csv("out.csv", index=False, encoding="utf-8-sig")   # utf-8-sig 让 Excel 不乱码
df.to_excel("out.xlsx", index=False)                       # 需 openpyxl
print(tabulate(df.head(20), headers="keys", tablefmt="github"))  # 直接出一个 Markdown 表格
```

- 交付时给一段 **Markdown 表格**（`tablefmt="github"`），用户能直接粘进报告
- 抓取字段固定后，先 `df.head()` 抽查，再批量导出

## 5. 合规红线（必须遵守）

- **遵守 `robots.txt`**：先请求 `https://站点/robots.txt`，看目标路径是否被 `Disallow`；被禁就不抓
- **不要高频请求**：加 `time.sleep`，**单站间隔建议 ≥1 秒**；大批量更要放慢，尽量低频跑
- **不抓个人隐私数据**（手机号、身份证、住址等）
- **不抓需登录的内容**，不绕付费墙、不破解验证码
- **不用于商业转售**，抓取结果自己调研用
- ⚠️ **违规爬取可能触犯法律**：《数据安全法》《个人信息保护法》以及站点服务条款。**不要把 AI 当挡箭牌** —— 抓取行为的法律责任由使用者承担

## 6. 常见坑

- **requests 抓不到动态渲染内容**：页面是 JS 渲染（Vue/React）时，HTML 里根本没有数据。先「查看网页源代码」，若内容是空的就说明要渲染。对策：F12 → Network → XHR/Fetch，**找到页面背后的 API 直接请求 JSON**；实在没有就用人浏览器 / 带渲染能力的 MCP，别硬啃
- **被反爬封 IP**：表现为 403 / 验证码 / 空内容。降频、加 UA，必要时换 IP；**不要用高并发硬刚**
- **并发过高被封**：多线程 / 协程要限并发数并加延迟，新手先串行
- **中文乱码**：见第 3 节，先校准编码
- **相对路径没拼接**：`href="/a/1"` 直接用会 404，要 `urljoin`
- **没有 timeout**：请求卡死会拖垮整批，务必 `timeout=15`