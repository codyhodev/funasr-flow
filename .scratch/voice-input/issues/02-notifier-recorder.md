Status: ready-for-agent

# 02 — 音频反馈通道

## Parent

[PRD: FunASR 语音输入](../PRD.md)

## What to build

实现两个独立模块：**notifier**（用户反馈）和 **recorder**（音频采集），并接入守护进程生命周期。

**notifier**：守护进程启动/停止时播放系统提示音（beep）和发送桌面通知（notify-send）。后续切片将使用同一接口在录音开始/结束/识别完成时触发反馈。

**recorder**：基于 sounddevice 的音频采集模块。接口接受开始/停止信号，录制 16kHz 单声道 16-bit PCM 音频，输出为 WAV 文件写入 `/tmp/funasr-flow/`。最长录制 5 分钟后自动停止。录制完成后删除临时文件。

两个模块均需提供 mock 友好的接口，便于后续测试。

## Acceptance criteria

- [ ] `notifier.py`：`play_beep_start()`、`play_beep_stop()`、`notify(title, body)` 三个接口
- [ ] 守护进程启动时触发 beep + notify("FunASR Flow", "服务已启动")
- [ ] 守护进程停止时触发 notify("FunASR Flow", "服务已停止")
- [ ] `recorder.py`：`start()` 开始录音，`stop()` 停止并返回 WAV 文件路径
- [ ] 录音参数：16kHz 采样率、单声道、16-bit PCM、WAV 格式
- [ ] 临时文件写入 `/tmp/funasr-flow/` 目录
- [ ] 录音达到 5 分钟自动停止
- [ ] 停止后临时文件被正确删除
- [ ] recorder 和 notifier 均可通过 mock 独立测试

## Blocked by

- #01 — 项目脚手架 + systemd 集成
