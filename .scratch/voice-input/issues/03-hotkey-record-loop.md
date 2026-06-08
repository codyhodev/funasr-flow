Status: ready-for-agent

# 03 — 热键录音回路

## Parent

[PRD: FunASR 语音输入](../PRD.md)

## What to build

实现 X11 全局热键监听（python-xlib），用 `XGrabKey` 捕获 Ctrl+F1 组合键，程序消耗该按键事件不传递给焦点应用。

将热键、状态机、recorder、notifier 串联成完整录音回路：

1. 用户按下 Ctrl+F1 → notifier beep（开始音）→ 状态切换为 RECORDING → recorder 开始录音
2. 用户再次按下 Ctrl+F1 → notifier beep（停止音）→ recorder 停止录音 → 状态切换为 IDLE → WAV 文件写入 `/tmp/funasr-flow/` → notify("录音完成", "时长 X 秒")

如果录音中用户再次误触（未说话就按），也能正常停止（生成极短或空音频），状态恢复 IDLE。

## Acceptance criteria

- [ ] Ctrl+F1 被全局捕获，焦点应用收不到该组合键
- [ ] 首次 Ctrl+F1：触发 beep 开始音、状态变为 RECORDING、开始录音
- [ ] 再次 Ctrl+F1：触发 beep 停止音、停止录音、状态恢复 IDLE
- [ ] 录音完成后 notify-send 显示录音时长
- [ ] 录音中再次按 Ctrl+F1 可正常停止（允许空录音）
- [ ]  5 分钟超时后自动停止，行为与手动停止一致
- [ ] 程序退出时释放 XGrabKey，不再占用热键
- [ ] hotkey.py 可通过 mock Xlib 连接独立测试

## Blocked by

- #02 — 音频反馈通道
