---
name: data-analysis
description: 用 pandas 对 CSV/Excel 做数据清洗与分析（缺失值、去重、类型转换、分组聚合）、画图（matplotlib，含中文字体配置）和透视表。当用户拿来 CSV/Excel 说想做分析、清洗、统计汇总、画图表或做透视表时使用。
---

# 数据分析工作流

## 0. 依赖与读入

```bash
python3 -m pip install pandas matplotlib openpyxl
```

```python
import pandas as pd
df = pd.read_csv("data.csv", encoding="utf-8")   # 中文 CSV 常需指定编码
df = pd.read_excel("data.xlsx", sheet_name=0)
```

读中文 CSV 报 `UnicodeDecodeError` 时，依次试 `encoding="utf-8-sig"`、`"gbk"`。**先确认编码再读**，别反复瞎试。

第一件事永远是**看数据长什么样**：

```python
df.shape          # 行列数
df.head()         # 前几行
df.info()         # 列名、类型、非空数量
df.describe()     # 数值列统计
df.isna().sum()   # 每列缺失数
```

## 1. 清洗（按顺序）

1. **列名规范**：`df.columns = df.columns.str.strip()`，去空格、统一命名
2. **去重**：`df = df.drop_duplicates()`，必要时指定 `subset=["id"]`
3. **类型转换**：`pd.to_numeric(df["score"], errors="coerce")`（转不了的变 NaN 而不是报错）；日期用 `pd.to_datetime(df["date"], errors="coerce")`
4. **缺失值**：先判断是「真缺」还是「有隐含含义」
   - 删除：`df.dropna(subset=["关键列"])`
   - 填充：`df["x"].fillna(df["x"].median())`；类别列用众数 `df["c"].fillna(df["c"].mode()[0])`
   - **不要无脑 `fillna(0)`**，会污染统计结果
5. **异常值**：先用 `df.describe()` 看极值是否合理，再决定删除或保留；删值要记录口径
6. **文本列**：`df["name"] = df["name"].str.strip()`，统一大小写

每步做完打印一次 `df.shape` 和受影响列，确保改动符合预期。

## 2. 分组聚合与透视表

```python
g = df.groupby("班级")["分数"].agg(["count", "mean", "median", "std"])
df.pivot_table(index="班级", columns="科目", values="分数", aggfunc="mean")
```

- `agg` 可传列表一次算多个统计量
- 分组前确认分组列无缺失、无前后空格，否则会多出奇怪的组
- 多级索引结果用 `reset_index()` 变回普通表，方便导出

## 3. 画图

先解决中文字体（不配就是一屏方框）：

```python
import matplotlib
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC", "Source Han Sans SC",
    "PingFang SC", "Heiti SC", "Arial Unicode MS",
    "Microsoft YaHei", "SimHei",
]
plt.rcParams["axes.unicode_minus"] = False
```

常用图：

```python
df["分数"].hist(bins=20); plt.title("分数分布"); plt.savefig("hist.png", dpi=150, bbox_inches="tight")
df.groupby("班级")["分数"].mean().plot(kind="bar"); plt.title("各班均分")
plt.scatter(df["x"], df["y"]); plt.xlabel("x"); plt.ylabel("y")
```

要点：

- 无显示环境（服务器）先 `matplotlib.use("Agg")`，再 `import pyplot`
- 保存用 `bbox_inches="tight"` 防止标签被裁掉
- 画完**看一眼图**，确认中文正常，别只看代码没看结果

## 4. 结果交付

- 给结论时附上**依据**：样本量、口径（是否删了缺失 / 异常）、用了什么统计量
- 导出清洗后的数据：`df.to_csv("clean.csv", index=False, encoding="utf-8-sig")`（`utf-8-sig` 让 Excel 打开不乱码）
- 只描述数据里观察到的事实，不要下因果结论