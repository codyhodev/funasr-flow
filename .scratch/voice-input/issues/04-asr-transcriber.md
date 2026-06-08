Status: ready-for-agent

# 04 — ASR 识别集成

## Parent

[PRD: FunASR 语音输入](../PRD.md)

## What to build

实现 transcriber 模块，封装 FunASR SenseVoice-Small 模型的加载和推理。模型在守护进程启动时预加载到内存，推理接口接受 WAV 文件路径返回识别文本。

在 `funasr-flow install` 阶段触发模型下载（通过 modelscope SDK），缓存到 `~/.cache/funasr-flow/models/`。模型仅下载一次，后续 install 跳过。

将 transcriber 接入录音回路：录音完成 → transcriber 推理 → notify-send 显示识别文本预览（前 50 字）。推理期间状态切换为 TRANSCRIBING，完成后恢复 IDLE。推理出错时 notify 显示错误信息。

## Acceptance criteria

- [ ] `funasr-flow install` 下载 SenseVoice-Small 模型到 `~/.cache/funasr-flow/models/`
- [ ] 模型已存在时跳过下载
- [ ] 守护进程启动时加载模型到内存（首次启动若模型未下载则报错退出并提示先 install）
- [ ] `transcriber.py`：`transcribe(wav_path: str) -> str` 接口，返回识别文本（含标点）
- [ ] 录音完成后自动调用 transcriber，状态切换为 TRANSCRIBING
- [ ] 推理完成后 notify-send 显示识别文本预览（前 50 字）
- [ ] 推理出错时 notify-send 显示错误信息，状态恢复 IDLE
- [ ] transcriber 可通过喂入已知 WAV 文件独立测试

## Blocked by

- #03 — 热键录音回路
