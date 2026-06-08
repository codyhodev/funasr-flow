Status: ready-for-agent

# PRD: FunASR 语音输入

## Problem Statement

用户在 Linux 桌面工作环境中，经常需要将脑中想法快速转化为文字输入。从"想要输入"到"打开发光焦点、切换输入法、开始打字"的流程存在摩擦，尤其在思考密集时，打字速度跟不上思维。现有的语音输入方案或依赖网络（隐私风险、延迟高），或收费昂贵，或 Linux 支持不完善。

用户需要一个**离线、低延迟、一键触发**的语音输入工具：按下按键开始说话，再按按键停止，文字自动出现在光标位置。

## Solution

一个基于 FunASR SenseVoice-Small 的 Linux 桌面语音输入守护进程。通过 systemd user service 常驻后台，全局监听 Ctrl+F1 热键；按下开始录音，释放停止录音；录音完成后调用本地 FunASR 模型将语音转为文本，再通过剪贴板模拟粘贴将文本注入当前焦点窗口的光标位置。

## User Stories

1. 作为 Linux 桌面用户，我按下 Ctrl+F1 开始语音录音，再次按下 Ctrl+F1 停止录音，识别结果自动出现在光标位置，以便我无需切换窗口就能随时输入文字。
2. 作为用户，我希望首次安装后只需一条命令就能启动服务，之后开机自动运行，无需每次手动启动。
3. 作为用户，我按下 Ctrl+F1 时能听到提示音，知道录音已开始，避免误开或不知道麦克风是否在工作。
4. 作为用户，录音结束时能听到不同的提示音，知道录音已停止、正在处理。
5. 作为用户，识别完成后能看到桌面通知显示前几个字的预览，确认注入成功。
6. 作为用户，即使说话持续 5 分钟，录音也不会丢失，到达时限会自动停止并处理。
7. 作为用户，识别结果完全离线处理，音频数据不会离开我的电脑。
8. 作为用户，Ctrl+F1 组合键不会被焦点应用接收到，不会在编辑器或终端中产生意外的快捷键效果。
9. 作为用户，ASR 模型在服务启动时预加载，首次按键时无需额外等待。
10. 作为用户，我可以通过 `funasr-flow install` 完成安装和模型下载，通过 `funasr-flow start/stop` 控制服务。
11. 作为用户，系统托盘或通知区域不显示任何图标——此工具在后台完全静默运行。
12. 作为用户，录音阶段如果误触 Ctrl+F1 导致开始录音，可以再按一次立即停止（未说话或放弃当前输入）。
13. 作为用户，文本注入使用我当前的系统输入法和焦点窗口，不用额外配置。
14. 作为用户，剪贴板内容在注入前后不受影响——之前复制的内容仍然可用。

## Implementation Decisions

### 整体架构

- 进程形态：systemd user service 管理的前台进程，不自己做 daemonize
- 安装方式：`uv tool install .`，通过 `pyproject.toml` 的 `[project.scripts]` 暴露 CLI
- 并发模型：多线程——热键监听线程、录音线程、ASR 推理线程，通过临时文件传递音频数据
- 状态管理：纯 Python 状态机，状态枚举为 `IDLE | RECORDING | TRANSCRIBING`

### CLI 设计

- 子命令：`install`（安装 systemd unit + 下载模型）、`uninstall`（移除 unit + 停止服务）、`start`、`stop`、`status`
- `start/stop/status` 通过 `systemctl --user` 代理

### 热键监听

- 使用 python-xlib 的 XGrabKey 捕获 Ctrl+F1
- 程序消耗按键事件，不传递给其他应用
- X11 only

### 音频采集

- 使用 sounddevice 库，PortAudio 后端
- 参数：16kHz 采样率、单声道、16-bit PCM
- 格式：WAV 文件写入 `/tmp/funasr-flow/`，用完立即删除
- 最大录音时长：5 分钟（超时自动停止）
- 不含 VAD 自动停止——用户手动控制录音边界

### 语音识别

- 模型：SenseVoice-Small（约 50MB）
- 启动时预加载模型到内存
- 模型下载：`install` 阶段触发，缓存到 `~/.cache/funasr-flow/models/`
- 整段识别模式（非流式）：录完整段 → 一次性推理 → 返回完整文本

### 文本注入

- 剪贴板方案：保存当前剪贴板 → 将识别文本写入剪贴板 → 合成 Ctrl+V → 恢复原剪贴板
- 使用 xclip 或 xsel 操作剪贴板

### 用户反馈

- 录音开始/停止：系统提示音（beep）
- 识别完成：notify-send 桌面通知（显示文本预览）

### 项目结构

```
src/funasr_flow/
├── __init__.py
├── cli.py           # 命令行入口，uv tool 入口点
├── hotkey.py        # X11 全局热键监听
├── recorder.py      # sounddevice 音频采集
├── transcriber.py   # FunASR SenseVoice-Small 推理
├── injector.py      # 剪贴板保存/替换/恢复 + 粘贴
├── notifier.py      # beep 提示音 + notify-send 通知
└── state.py         # 状态机枚举
```

## Testing Decisions

### 测试原则

- 只测外部行为，不测实现细节
- 外部依赖（X11、sounddevice、FunASR 模型、xclip、notify-send）全部 mock
- 每个模块独立可测

### 各模块测试要点

| 模块 | 测试方式 | 关键断言 |
|------|----------|----------|
| state.py | 纯单元测试，无 mock | 状态转换合法性 |
| recorder.py | mock sounddevice.InputStream | 输出 WAV 文件格式正确（16kHz mono 16-bit）、时长截断 |
| transcriber.py | 喂已知 WAV 文件 | 输出文本非空、标点存在 |
| injector.py | mock subprocess | 调用顺序：保存剪贴板 → 设置新内容 → 粘贴 → 恢复 |
| notifier.py | mock subprocess | beep 和 notify-send 被正确调用 |
| hotkey.py | mock Xlib | 按键事件触发状态转换回调 |
| cli.py | 写 unit 文件到临时目录 | 模板内容、systemctl 调用参数 |

### 集成测试

- 端到端：mock 所有外部依赖，验证完整状态转换链路
- 不做真实麦克风+热键的端到端测试（需要物理环境，不适合 CI）

## Out of Scope

- Wayland 支持（当前仅 X11）
- 流式识别（当前仅整段识别）
- VAD 自动停止录音
- GUI 配置面板 / 系统托盘图标
- 多语言支持（SenseVoice-Small 支持但未做切换 UI）
- Windows/macOS 支持
- 自定义快捷键配置（硬编码 Ctrl+F1）
- 多模型切换
- 音频设备选择（使用系统默认麦克风）
- 录制音频的持久化存储

## Further Notes

- FunASR: https://github.com/modelscope/FunASR
- SenseVoice-Small: https://github.com/FunAudioLLM/SenseVoice
- FunASR 模型仓库依赖 modelscope 或 huggingface 下载
- python-xlib 需要在 X11 环境下才能工作，SSH 远程或纯 Wayland 不可用
- 用户需要加入 `input` 组或类似权限以使用 evdev（如后续迁移到 evdev 热键）
