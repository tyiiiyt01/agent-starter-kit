---
name: meeting-notes
description: 把会议录音/视频转成文字并整理成结构化会议纪要（参会人、议题、结论、待办、未决事项）。当用户提供录音或视频、要求转写会议内容、整理会议记录或提炼待办事项时使用。默认本地免费方案，涉密会议不上传云端。
---

# 会议录音转写与纪要整理

## 0. 先确认三件事

1. **音频从哪来**：录音文件、视频文件，还是要从云端下载？格式是 wav / mp3 / m4a / mp4 里的哪种？
2. **能否上传云端**：会议内容是否涉密？涉密会议**只能走本地方案**，绝不上传
3. **要不要区分说话人**：多人讨论要标「谁说的」；单人汇报不需要

## 1. 环境准备

```bash
python3 -m pip install faster-whisper
# 非 wav / mp3 的音频先转格式（whisper 对 16k 单声道最友好）
ffmpeg -i input.m4a -ar 16000 -ac 1 output.wav
```

`ffmpeg` 没装会报 command not found，先确认系统里有（macOS：`brew install ffmpeg`）。

## 2. 本地转写：faster-whisper

pip 包名 `faster-whisper`，导入名 `faster_whisper`（下划线），别写混。

```python
from faster_whisper import WhisperModel

model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    "output.wav",
    language="zh",
    word_timestamps=True,
    vad_filter=True,          # 掐掉长静音，明显提速
)
for seg in segments:          # segments 是生成器，遍历时才真正开始计算
    print(f"[{seg.start:6.1f}-{seg.end:6.1f}] {seg.text}")
```

要点：

- `segments` 是**生成器**：`transcribe()` 返回后不遍历就不会计算，别以为它没跑
- CPU 用 `compute_type="int8"` 省内存提速；有 NVIDIA 显卡可改 `device="cuda"`
- 首次运行会自动下载模型，之后缓存在本地

## 3. 模型大小与取舍（最重要的决策）

| 模型 | 体积 | 说明 |
|---|---|---|
| tiny | 约 75MB | 最快，质量差，只够试跑 |
| base | 约 142MB | 快，准确率一般 |
| small | 约 466MB | 常用均衡点 |
| medium | 约 769MB | 更准，明显更慢 |
| large-v3 | 约 1.5GB | 最准，CPU 上很慢，建议有显卡再用 |

⚠️ **中文效果提醒（务必如实告诉用户）**：whisper 系列在中文上偏差较大，`small` 级别字错率约 **22%**，纯中文会议转出的稿子需要大量人工校对。

**中文场景更好的选择**：阿里 FunASR 的 **SenseVoice-small**，量化后约 **250MB**，字错率约 **8%**，可经 **sherpa-onnx** 纯 CPU 运行、不需要 Python。中文为主的会议优先试它。把「错字率 vs 速度 / 显卡」摆清楚，让用户自己选。

## 4. 需要区分说话人：whisperX

多人会议要分「谁说的」，用 **whisperX**（在 whisper 基础上做说话人分离 + 时间对齐）。

- 它会额外拉取说话人分离模型，**下载量大、依赖较重**，先确认网络与磁盘
- 说话人只会标成 `SPEAKER_00` / `SPEAKER_01` 这类编号，**具体是谁仍需人工对照**

## 5. 本地 vs 云端

| | 本地（faster-whisper / SenseVoice） | 云端（OpenAI / 阿里云 / 讯飞） |
|---|---|---|
| 费用 | 免费 | 需 API Key，按量付费 |
| 隐私 | 数据不出本机 | 音频要上传 |
| 速度 | 慢（尤其 CPU） | 快 |
| 效果 | 取决于模型与硬件 | 通常更好 |

选择原则：**涉密 / 敏感 → 本地**；追求效果且不敏感 → 云端。

## 6. 纪要结构化模板

转写完不要直接把流水稿丢给用户，按下面结构整理：

```
参会人：
时间：
议题：
  1. ...
结论：
  - 就 X 达成一致：...
待办：
  - [ ] 谁 · 做什么 · 何时完成
未决事项：
  - X 尚无结论，待 Y 后确认
```

## 7. 从纪要提取待办

- 每条待办**必须有责任人和时间点**：缺谁就问、缺何时就写「时间待定」
- 原文含糊（「尽快」「回头弄」）的，**标成「待确认」**，不要替用户臆造截止日期
- 结论与讨论要分开：**讨论过程**不等于**已定结论**

## 8. 隐私与合规（硬提醒）

- 会议录音可能含**商业机密、个人信息**，**默认走本地方案**
- 上传云端前必须**确认合规**：取得参会人 / 公司许可，确认云服务的数据条款
- 转写稿和纪要也要注意存放位置，别随手放进共享目录

## 9. 常见坑自检

- [ ] 音频已转成 wav / mp3，采样率与声道合适
- [ ] 模型已选对（中文优先考虑 SenseVoice-small）
- [ ] 遍历了 `segments` 生成器，确实拿到了文本
- [ ] 转写稿**人工校对过**（中文错字率不低）
- [ ] 待办的责任人和时间都写清或标了「待确认」
- [ ] 已确认是否允许上传云端