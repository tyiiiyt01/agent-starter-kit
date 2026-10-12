---
name: design-material
description: 用 Pillow 做图片批处理（缩放、裁剪、转格式、加圆角、拼接、纠正 EXIF 方向）与简单图文合成（叠字、生成二维码），并给出格式、分辨率、中文字体与商用授权的实用建议。当用户要做宣传海报 / 社团活动物料、批量处理图片、生成图文或二维码、判断图片格式与字体版权时使用。
---

# 设计素材与图像处理

面向**宣传 / 设计场景**：社团海报、活动物料、办公图文、图片批处理。**科研插图**要符合期刊硬指标，看 `academic-figures` 技能，本技能不做。

## 边界（先讲清楚）

- AI 适合做**批处理和结构化排版**：统一尺寸、转格式、批量压体积、叠固定文字、生成二维码；**真正的创意设计要人来做**，AI 出不了「专业设计效果」，**不要向用户承诺**
- **不生成可能侵权的素材**：不提供盗版字体 / 素材包下载，不复制、改造他人有版权的海报图

## 0. 依赖

```bash
python3 -m pip install Pillow qrcode
```

- `Pillow`（import 名 `PIL`）—— 图像处理主力；`qrcode` —— 生成二维码（渲染依赖 Pillow）
- 往图上叠中文时，还需要一个**中文字体文件**（见第 4 节）

## 1. 图像批处理（Pillow）

### 批量缩放 + 转格式

```python
from pathlib import Path
from PIL import Image, ImageOps

src, dst = Path("in"), Path("out"); dst.mkdir(exist_ok=True)
for p in src.glob("*.jpg"):
    im = Image.open(p)
    im = ImageOps.exif_transpose(im)      # ⚠️ 先纠正手机拍照方向，否则会歪
    im.thumbnail((1200, 1200))            # 原地缩放，保持比例，不会放大
    if im.mode in ("RGBA", "P"):          # ⚠️ 存 JPEG 前转 RGB，否则报错
        im = im.convert("RGB")
    im.save(dst / (p.stem + ".jpg"), quality=85, optimize=True)
```

- `thumbnail((w, h))`：**原地修改**，等比缩到不超过 w×h，**不会放大**
- `resize((w, h))`：**返回新图**，按给定尺寸强行拉伸，**会变形**
- `save(..., quality=85)`：JPEG 质量 1–100，85 左右体积 / 画质平衡好；`optimize=True` 再压一点体积

### 裁剪、加圆角、拼接

```python
from PIL import Image, ImageDraw

im = Image.open("a.jpg").convert("RGBA")
crop = im.crop((100, 100, 900, 600))    # box = (左, 上, 右, 下)，右下坐标不含

# 圆角（Pillow ≥ 8.2 才有 rounded_rectangle，先确认版本）
mask = Image.new("L", im.size, 0)
ImageDraw.Draw(mask).rounded_rectangle([(0, 0), im.size], radius=40, fill=255)
r = Image.new("RGBA", im.size, (0, 0, 0, 0)); r.paste(im, (0, 0), mask)
r.save("rounded.png")

# 横向拼接
ims = [Image.open(p).convert("RGB") for p in ("a.jpg", "b.jpg")]
W = sum(i.width for i in ims); H = max(i.height for i in ims)
canvas = Image.new("RGB", (W, H), "white"); x = 0
for i in ims:
    canvas.paste(i, (x, 0)); x += i.width
canvas.save("merged.jpg", quality=90)
```

## 2. 格式与体积

| 格式 | 适用 | 备注 |
|---|---|---|
| JPEG | 照片、有渐变的图 | 有损；**不支持透明** |
| PNG | 截图、图标、要透明 | 无损但体积大 |
| WebP | 网页图片 | 同画质体积更小，浏览器支持好 |
| SVG / PDF | 图标、logo、印刷 | **矢量**，无损缩放 |

- **印刷**：分辨率 **≥300 dpi**（照片级 350 dpi 更稳），留出血；印刷厂常要 **CMYK**（Pillow 转 CMYK 能力有限，正式印刷**先问印厂要求**或用专业工具）
- **屏幕**：72–150 dpi 即可，手机上 2x / 3x 图更清晰
- ⚠️ **位图放大不会变清晰**：把 300px 的图拉成 3000px 只会糊。真要放大，**原始素材必须是矢量（SVG / PDF）**或重新出图

## 3. 科研插图 vs 设计海报

**科研插图**（论文 / 毕设）看 `academic-figures`（dpi、矢量、字体合规、黑白可辨）；**设计海报**（社团 / 宣传 / 活动）用本技能（尺寸版式、色彩、可读性、批量产出）。两套标准别混用。

## 4. 配色与字体

- **配色**：主色 1 个 + 辅助色 1–2 个，别超 3 色；用在线取色 / 配色工具定色板，别凭感觉堆颜色
- **可读性**：深底浅字或浅底深字，标题与正文对比要够，手机上也要看清

⚠️ **中文字体配置有两条不同路径，别混**：

```python
# 路径 A —— matplotlib（画图）：走 font.sans-serif 候选列表（详见 academic-figures）
plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "Source Han Sans SC",
                                   "PingFang SC", "Microsoft YaHei", "SimHei"]

# 路径 B —— PIL（往图片上叠字）：走 ImageFont.truetype(真实字体文件路径, 字号)
from PIL import Image, ImageDraw, ImageFont
im = Image.open("bg.jpg").convert("RGB")
draw = ImageDraw.Draw(im)
font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)  # macOS 示例
draw.text((60, 60), "活动海报标题", fill="white", font=font)
im.save("poster.jpg", quality=90)
```

- PIL **不加载 `.ttf` / `.ttc` 文件就用默认位图字体**，中文会变方框 → 必须 truetype；`.ttc` 是字体集合，可用 `index=` 指定第几款
- 字体缺失时常常**不报错、直接出方框**，生成后**一定看图确认**
- 常见中文字体路径（**先确认文件真存在，别照抄**）：
  - macOS：`/System/Library/Fonts/PingFang.ttc`、`/System/Library/Fonts/STHeiti Medium.ttc`、`/Library/Fonts/Arial Unicode.ttf`
  - Windows：`C:\Windows\Fonts\msyh.ttc`（微软雅黑）、`C:\Windows\Fonts\simhei.ttf`（黑体）、`C:\Windows\Fonts\simsun.ttc`（宋体）
- **字体版权**：商用设计务必看授权；推荐可商用的开源中文字体 **思源黑体 / 思源宋体（Source Han，西文名 Noto Sans / Serif CJK）**、文泉驿系列；拿不准就换开源字体

## 5. 生成二维码 / 简单图文

```python
import qrcode

img = qrcode.make("https://example.com/activity")   # 返回 PIL 图像，可直接 save
img.save("qrcode.png")

# 控制参数（纠错级别 / 边长 / 留白）时用 QRCode 对象：
qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
qr.add_data("https://example.com/activity"); qr.make(fit=True)
qr.make_image(fill_color="black", back_color="white").save("qrcode2.png")
```

- `qrcode.make()` 返回的就是 PIL 图像，可按第 4 节方式用 `paste` 把它贴到海报上
- 二维码四周留白（`border`）别省，太小扫不出来

## 6. 常见坑

- **`thumbnail` vs `resize`**：`thumbnail` 原地改、保比例、不放大；`resize` 返回新图、会拉伸变形
- **RGBA / P 存 JPEG 报错**：`cannot write mode RGBA as JPEG` → 先 `im.convert("RGB")`
- **手机照片方向歪**：EXIF 里有旋转标记，处理前先 `ImageOps.exif_transpose(im)`
- **透明通道**：PNG 有 alpha，转 JPEG 会丢透明（变黑 / 白底），要透明就存 PNG / WebP
- **字体路径跨平台不同**：macOS 与 Windows 完全不同，先找实际文件
- **内存占用**：超大图一次 `load()` 很吃内存，可先 `draft()` 降采样再处理；批量时**逐张打开用完即释放**，别把所有图堆进列表
- **颜色模式**：印刷要 CMYK，Pillow 的 CMYK 支持有限，正式印刷先问印厂

## 7. 不要做的

- 不承诺「专业设计效果」，不替代设计师；不下载 / 分发盗版字体、素材包；不把他人有版权的图直接改成自己的物料