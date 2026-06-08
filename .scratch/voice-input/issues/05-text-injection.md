Status: ready-for-agent

# 05 — 文本注入

## Parent

[PRD: FunASR 语音输入](../PRD.md)

## What to build

实现 injector 模块，将 ASR 识别结果注入当前焦点窗口的光标位置。采用剪贴板方案：

1. 保存当前剪贴板内容
2. 将识别文本写入剪贴板
3. 合成 Ctrl+V 粘贴
4. 恢复原剪贴板内容

使用 xclip 操作剪贴板，xdotool 合成粘贴按键。整个过程对用户透明——之前复制的内容在注入后仍然可用。

将 injector 接入识别回路：transcriber 推理完成 → injector 注入文本 → notify-send 确认 + beep 完成音。至此完整语音输入闭环完成。

## Acceptance criteria

- [ ] `injector.py`：`inject(text: str)` 接口，执行保存→替换→粘贴→恢复全流程
- [ ] 粘贴使用系统剪贴板（`xclip -selection clipboard`）
- [ ] 注入完成后剪贴板内容与注入前完全一致
- [ ] 识别完成后自动调用 injector 注入文本
- [ ] 注入完成后 notify-send 确认（可含文本预览）
- [ ] 注入出错时 notify-send 显示错误，不损坏剪贴板
- [ ] injector 可通过 mock subprocess 独立测试

## Blocked by

- #04 — ASR 识别集成
