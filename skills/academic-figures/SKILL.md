---
name: academic-figures
description: 按期刊与学位论文要求规范学术图表：用 SciencePlots 统一风格、解决中文字体、按 600/300 dpi 与矢量优先导出 PDF/EPS，并核对线宽、字号、双栏宽度等硬指标。当用户要画论文插图、生成符合投稿要求的图表或优化 matplotlib 出图时使用。
---

# 学术图表规范

目标：让 matplotlib 出的图**符合期刊 / 学位论文的硬要求**，并且中文不出方框。

## 1. 统一风格：SciencePlots

安装（pip 名 `SciencePlots`，import 名是 `scienceplots`）：

```bash
python3 -m pip install SciencePlots
```

用法：

```python
import matplotlib.pyplot as plt
import scienceplots

plt.style.use(['science', 'no-latex'])
```

- `science`：基础学术风格；`no-latex`：不强制走 LaTeX 渲染（不装 LaTeX 也能用）
- 可叠加，如 `['science', 'ieee']`（IEEE 风格）、`['science', 'grid']`
- 样式必须在**绘图前**设置

## 2. ⚠️ 中文方框问题

SciencePlots 默认偏**西文 serif 字体**，中文会显示成方框（tofu）。必须另配中文字体：

```python
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = [
    'Noto Sans CJK SC', 'Source Han Sans SC',          # Linux / 通用
    'PingFang SC', 'Heiti SC', 'Arial Unicode MS',     # macOS
    'Microsoft YaHei', 'SimHei',                       # Windows
]
plt.rcParams['axes.unicode_minus'] = False   # 负号变方框时加
```

- 要求**宋体**：把列表换成 `['SimSun', 'Songti SC', 'Noto Serif CJK SC']`
- 要求**黑体**：`['SimHei', 'Heiti SC', 'Noto Sans CJK SC']`
- `font.sans-serif` 是候选列表，系统里第一个存在的会被用上
- 找不到字体**不报错**，静默退回仍显示方框 —— 必须实际看图确认
- 先查本机有哪些中文字体：

```python
from matplotlib import font_manager
names = sorted({f.name for f in font_manager.fontManager.ttflist})
print([n for n in names if any(k in n for k in ('Hei','Song','YaHei','CJK','PingFang','Han','Sun'))])
```

- 无显示器环境加 `matplotlib.use('Agg')`（放在 import pyplot 之前）

## 3. 导出矢量图（正确姿势）

```python
plt.savefig('fig1.pdf', format='pdf', bbox_inches='tight')
```

- **矢量优先**：PDF / EPS / SVG，缩放不失真
- `bbox_inches='tight'` 去白边
- 需要位图时（≥300 dpi）：

```python
plt.savefig('fig1.png', dpi=600, bbox_inches='tight')
```

- ⚠️ **位图不能转矢量**：截图、照片、Excel 截图这类像素图无法「转换」成矢量，必须拿原始数据**重绘**
- 不要用 JPG（有损）；需要位图用 PNG / TIFF

## 4. 期刊 / 学位论文常见硬要求（逐项核对）

- [ ] 分辨率：线图 ≥600 dpi，位图（照片等）≥300 dpi
- [ ] 格式：矢量优先（PDF / EPS / SVG）
- [ ] 中文字体：常见要求宋体 / 黑体；西文：Arial / Times New Roman
- [ ] 线宽 ≥0.5 pt（`plt.rcParams['axes.linewidth']`、`lines.linewidth`）
- [ ] 字号：坐标轴刻度、图注不小于正文字号（常见 7–9 pt）
- [ ] 坐标轴：标注物理量与**单位**，如 `时间 (s)`、`速度 (m/s)`
- [ ] 刻度：主/次刻度是否都要，刻度朝内还是朝外（按期刊要求）
- [ ] 图注：放**图下方**，表注放**表上方**
- [ ] 单栏 / 双栏宽度：按版式设 `figsize`（单栏约 8 cm，双栏约 16–17 cm）
- [ ] 颜色：黑白打印与色盲读者可辨（用线型/标记区分，不要只靠颜色）
- [ ] 图内文字与图注语言一致（中文论文用中文，英文论文用英文）

## 5. 常用设置片段

```python
import matplotlib.pyplot as plt
import scienceplots

plt.style.use(['science', 'no-latex'])
plt.rcParams['font.sans-serif'] = ['SimSun', 'Songti SC', 'Noto Serif CJK SC']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.linewidth'] = 0.8      # 边框线宽
plt.rcParams['lines.linewidth'] = 1.2
plt.rcParams['font.size'] = 9

fig, ax = plt.subplots(figsize=(3.5, 2.6))   # 单栏约 8.9 cm
ax.plot(x, y, label='实验值')
ax.set_xlabel('时间 (s)')
ax.set_ylabel('速度 (m/s)')
ax.legend()
fig.savefig('fig1.pdf', format='pdf', bbox_inches='tight')
```

## 6. 常见坑

- SciencePlots 样式设晚了 → 不生效（必须在绘图前）
- 中文方框 → 没配中文字体，或配了系统里不存在的字体名
- 导出成 JPG → 有损、非矢量
- 忘记 `bbox_inches='tight'` → 白边太大
- 位图强行「矢量化」 → 结果仍是位图轮廓，必须重绘
- 只按颜色区分曲线 → 黑白打印 / 色盲读者无法分辨