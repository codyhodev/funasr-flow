# FunASR Flow

基于 [FunASR](https://github.com/modelscope/FunASR) SenseVoice-Small 的 Linux 桌面语音输入工具。

按下**右 Ctrl 键**开始录音，松开后自动识别并注入文本到光标位置。

## 功能

- 🎤 **右 Ctrl 一键录音** — 按住右 Ctrl 开始录音，松开自动识别
- 🧠 **离线语音识别** — 基于阿里达摩院 SenseVoice-Small 模型，本地运行，无需网络
- 📋 **自动文本注入** — 识别结果通过 xclip + xdotool 自动粘贴到当前光标位置
- 🔔 **提示音反馈** — 开始录音（短促低音）、停止录音（双声高音）
- 📌 **系统托盘** — PyQt5 托盘图标，idle/recording/disabled 三种状态视觉反馈
- 🔧 **启用/禁用切换** — 右键菜单可临时禁用热键，无需退出程序
- 🚀 **桌面自启** — `funasr-flow install` 一键安装到 XDG autostart

## 快速开始

```bash
# 1. 安装系统依赖
sudo apt install xclip xdotool ffmpeg portaudio19-dev python3-dev

# 2. 安装 FunASR Flow
uv venv
source .venv/bin/activate
uv pip install -e . -i https://mirrors.aliyun.com/pypi/simple/

# 3. 安装到桌面自启（含模型下载）
funasr-flow install

# 4. 启动守护进程
funasr-flow daemon
```

## 使用方式

| 操作 | 效果 |
|------|------|
| 按下**右 Ctrl** | 开始录音（系统托盘变红） |
| 松开**右 Ctrl** | 停止录音 → 语音识别 → 文本粘贴到光标位置 |
| 托盘右键 → 禁用 | 热键暂时失效，图标变灰 |
| 托盘右键 → 启用 | 恢复热键功能 |
| 托盘右键 → 退出 | 退出程序 |

## 命令

| 命令 | 说明 |
|------|------|
| `funasr-flow install` | 下载模型 + 安装 XDG 桌面自启文件 |
| `funasr-flow uninstall` | 移除桌面自启文件 |
| `funasr-flow daemon` | 前台运行守护进程（由 autostart 调用） |

## 架构概览

```
用户按下右 Ctrl
    ↓
HotkeyListener (pynput)       ← 全局热键监听
    ↓
VoiceInputLoop (状态机)       ← 控制录音→识别→注入流程
    ↓
┌─────────┬──────────────┬──────────────┐
│ Recorder │ Transcriber  │  Injector    │
│sounddevice│ FunASR Auto │ xclip+xdotool│
│16kHz PCM │ SenseVoiceSm│ 写入剪贴板   │
│  → WAV   │    → 文本    │  Ctrl+Shift+V│
└─────────┴──────────────┴──────────────┘
    ↓
系统托盘反馈 (PyQt5)          ← idle/recording/disabled 图标
```

详细架构说明见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)。

## 系统依赖

| 依赖 | 用途 |
|------|------|
| Python ≥ 3.10 | 运行环境 |
| xclip | 将识别文本写入剪贴板 |
| xdotool | 模拟 Ctrl+Shift+V 粘贴操作 |
| ffmpeg | FunASR 音频编解码后端 |
| portaudio19-dev (libportaudio2) | sounddevice 音频采集的后端 |
| PyQt5 | 系统托盘图标 |
| PyTorch ≥ 2.0 | FunASR 模型推理 |
| pynput | 全局热键监听 |

完整依赖清单和安装说明见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) 和 [`docs/INSTALL.md`](docs/INSTALL.md)。

## 测试

```bash
uv pip install pytest -i https://mirrors.aliyun.com/pypi/simple/
pytest
```

## 许可证

MIT
