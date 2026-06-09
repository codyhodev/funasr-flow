# 架构设计

## 模块概览

```
src/funasr_flow/
├── cli.py          # 命令行入口 (install / uninstall / daemon)
├── config.py       # 配置文件管理 (YAML → Config 数据类)
├── lock.py         # 单实例进程锁 (PID 文件)
├── hotkey.py       # 全局热键监听器 (pynput)
├── loop.py         # 核心回路：热键→录音→识别→注入 状态机
├── state.py        # 状态枚举 (IDLE / RECORDING / TRANSCRIBING)
├── transition.py   # 状态转换逻辑 (next_on_toggle)
├── recorder.py     # 音频采集器 (sounddevice → 16kHz PCM WAV)
├── transcriber.py  # 语音识别器 (FunASR SenseVoice-Small)
├── injector.py     # 文本注入器 (xclip + xdotool)
├── notifier.py     # 用户反馈提示音 (sounddevice 正弦波)
├── tray.py         # 系统托盘 (PyQt5 QSystemTrayIcon)
└── icons/          # 托盘图标 (Lucide mic, MIT)
    ├── mic_idle.png
    ├── mic_recording.png
    ├── mic_disabled.png
    └── app.png
```

## 状态机

```
                    热键触发 (右 Ctrl)
                         │
    ┌────────────────────┼────────────────────┐
    ▼                    ▼                    ▼
  IDLE ──────▶ RECORDING ──────▶ TRANSCRIBING
    ▲                              │
    └──────────────────────────────┘
         (识别/注入完成后自动恢复)

IDLE 状态下热键 → RECORDING（开始录音）
RECORDING 状态下热键 → TRANSCRIBING（停止录音，开始识别）
TRANSCRIBING 状态下热键 → 忽略（识别期间不响应）
```

状态转换逻辑定义在 `transition.py:next_on_toggle()`：

```python
IDLE       → RECORDING
RECORDING  → TRANSCRIBING
其他       → None (忽略)
```

## 数据流

### 完整录音→注入链路

```
1. 用户按下右 Ctrl
   └─ pynput Listener 捕获 KeyPress 事件
   └─ HotkeyListener 匹配 Key.ctrl_r → 调用 callback

2. VoiceInputLoop._on_hotkey()
   └─ next_on_toggle(IDLE) → RECORDING
   └─ Recorder.start() → sounddevice InputStream 开始采集
      └─ 参数: 16kHz, 单声道, int16
      └─ callback 流式写入临时 raw 文件
   └─ play_beep_start() → 440Hz 短促提示音

3. 用户松开右 Ctrl → KeyPress 事件再次触发 callback
   └─ next_on_toggle(RECORDING) → TRANSCRIBING

4. VoiceInputLoop._stop_and_transcribe()
   └─ Recorder.stop() → 停止采集，raw→WAV 转换，返回 WAV 路径
   └─ play_beep_stop() → 两声 600Hz 提示音
   └─ Transcriber.transcribe(wav_path)
      └─ FunASR AutoModel.generate(input=wav_path)
      └─ rich_transcription_postprocess → 返回干净文本
   └─ injector(text)
      └─ xclip 写入剪贴板
      └─ xdotool 模拟 Ctrl+Shift+V 粘贴
   └─ Recorder.cleanup() → 删除 WAV 临时文件
   └─ 状态恢复 IDLE
```

## 各模块详解

### 1. HotkeyListener (`hotkey.py`)

基于 pynput 的全局热键监听器，支持单键和组合键两种模式。

**设计要点：**
- 使用原始 `Key` 对象比较，**不经过 `canonical()`**，因为 `canonical()` 会将 `Key.ctrl_r` 合并为 `Key.ctrl`，导致无法区分左右 Ctrl
- listener 线程设为 `daemon=True`，进程退出时自动清理，无需 join
- `stop()` 仅清空引用，不阻塞

**热键配置：** 通过 `~/.config/funasr-flow/config.yaml` 中的 `hotkey` 字段配置，默认为 `<ctrl_r>`。支持 pynput 格式的单键和组合键（如 `<ctrl>+<alt>+r`）。

### 2. VoiceInputLoop (`loop.py`)

热键驱动的核心回路，串联 hotkey → recorder → transcriber → injector。

**依赖注入设计：** 所有外部依赖通过构造函数传入，便于测试时 mock：

```python
VoiceInputLoop(
    hotkey,        # HotkeyListener 实例
    recorder,      # Recorder 实例
    transcriber,   # Transcriber 实例
    injector,      # Callable[[str], None]
    on_recording_start,  # 可选回调
    on_recording_stop,   # 可选回调
    on_state_change,     # 可选回调
)
```

**工厂函数** `make_voice_input_loop()` 创建完整的生产环境实例，接受 `hotkey_spec` 和 `device` 参数（从配置文件读取）。`grab_key()` 在构造时完成，`start()` 只负责启动监听。

**启用/禁用：** `disable()` 会立即停止正在进行的录音并清理状态。

### 3. Recorder (`recorder.py`)

音频采集器，使用 sounddevice InputStream。

- **格式：** 16kHz 单声道 16-bit PCM
- **存储：** 流式写入临时 raw 文件，stop 时转为 WAV
- **超时：** 默认最长 300 秒自动停止
- **清理：** `cleanup()` 删除 WAV 临时文件

### 4. Transcriber (`transcriber.py`)

基于 FunASR SenseVoice-Small 的语音识别器。

- **模型：** `iic/SenseVoiceSmall`，通过 ModelScope 下载
- **缓存目录：** `~/.cache/funasr-flow/models/`
- **推理设备：** 通过配置文件 `transcriber.device` 指定（`cpu` / `cuda` / `cuda:0` / `mps` / `npu:0`），默认为 `cpu`。设备不可用时 FunASR AutoModel 自动回退 CPU
- **配置：** `use_itn=True`（逆文本正则化），`disable_update=True`
- **后处理：** `rich_transcription_postprocess` 清理识别结果

`download_model()` 被提取为独立的模块级函数，`cmd_install` 可提前下载模型而不必加载整个 Transcriber。

### 5. Injector (`injector.py`)

文本注入模块，将识别文本输入到当前光标位置。

**策略：**
1. **X11 注入器**（需要 xclip + xdotool）：写入剪贴板 → 模拟 Ctrl+Shift+V
2. **仅剪贴板降级**（只有 xclip）：写入剪贴板，用户手动粘贴

`detect_injector()` 在模块加载时自动检测环境，选择最佳策略。模块级 `inject` 是默认注入器实例。

### 6. TrayIcon (`tray.py`)

PyQt5 QSystemTrayIcon 系统托盘图标。

**三种视觉状态：**

| 状态 | 图标 | 颜色 | 说明 |
|------|------|------|------|
| idle | mic_idle.png | 灰色 #dfdbd2 | 等待录音 |
| recording | mic_recording.png | 红色 #ef5350 | 正在录音 |
| disabled | mic_disabled.png | 灰色半透明 | 已禁用 |

**右键菜单：**
- 启用（仅在禁用时可见）
- 禁用（仅在启用时可见）
- 退出

`_refresh_icon()` 在 disabled 状态下覆写所有图标为禁用态，与 `_active_icon` 分离管理。

### 7. Notifier (`notifier.py`)

用户反馈提示音模块。

- `play_beep_start()` — 440Hz，150ms 短促音
- `play_beep_stop()` — 两声 600Hz，各 100ms

音频设备不可用时静默失败。

### 8. Lock (`lock.py`)

单实例进程锁，通过 PID 文件确保同一时间只有一个守护进程运行。

- **锁文件：** `~/.cache/funasr-flow/daemon.pid`
- `acquire()` — 检查锁文件中的 PID 是否存活，存活则拒绝启动返回 `False`，否则写入当前 PID 返回 `True`
- `release()` — 退出时删除锁文件（仅删除自己写入的）
- **死锁恢复：** 如果之前的进程异常退出（PID 已死），新进程自动覆盖锁文件
- **集成点：** `cmd_daemon()` 启动时立即调用 `acquire()`，失败则打印错误并 `sys.exit(1)`

### 9. Config (`config.py`)

YAML 配置文件管理模块，遵循 XDG 规范。

- **配置文件：** `~/.config/funasr-flow/config.yaml`
- **数据类：** `Config(hotkey, transcriber_device)` 封装配置值
- `load_config()` — 加载配置，不存在时自动生成默认文件
- **容错策略：** YAML 解析失败 / key 缺失 / 值非法 → 使用默认值 + stderr warning，程序始终可启动

**配置文件格式：**

```yaml
# FunASR Flow 配置文件
hotkey: "<ctrl_r>"       # 全局热键，pynput 格式

transcriber:
  device: "cpu"          # cpu | cuda | cuda:0 | mps | npu:0
```

**配置优先级（仅配置文件，不支持 CLI 参数）：**

```
配置文件 > 硬编码默认值
```

修改配置后需重启守护进程生效。

## 系统依赖详解

### Python 依赖 (pyproject.toml)

| 包名 | 版本要求 | 用途 |
|------|----------|------|
| `funasr` | ≥ 1.0.0 | 语音识别模型加载与推理 |
| `sounddevice` | ≥ 0.4.0 | 音频采集和提示音播放 |
| `evdev-binary` | ≥ 1.3.0 (仅 Linux) | pynput 在 Linux 下的后端 |
| `pynput` | ≥ 1.7.0 | 全局键盘事件监听 |
| `numpy` | ≥ 1.24.0 | 音频数据处理（提示音波形） |
| `torch` | ≥ 2.0.0 | FunASR 模型推理后端 |
| `torchaudio` | ≥ 2.0.0 | PyTorch 音频处理 |
| `PyQt5` | ≥ 5.15.0 | 系统托盘图标 |
| `Pillow` | ≥ 10.0.0 | 图像处理（构建时 PNG 生成） |

### 系统级依赖 (apt)

| 包名 | 用途 | 必需 |
|------|------|------|
| `xclip` | 将文本写入 X11 剪贴板 | 推荐 |
| `xdotool` | 模拟键盘粘贴 (`Ctrl+Shift+V`) | 推荐 |
| `ffmpeg` | FunASR 音频编解码（读取 WAV/MP3 等格式） | 必需 |
| `portaudio19-dev` | sounddevice 的 C 后端编译依赖 | 必需 |
| `python3-dev` | Python C 扩展编译头文件 | 必需 |
| `libportaudio2` | sounddevice 运行时库 | 必需 |

### 桌面自启

使用 XDG autostart 规范，desktop 文件安装到：

```
~/.local/share/applications/funasr-flow.desktop
```

桌面环境（GNOME/KDE/XFCE 等）登录时自动读取并启动 `funasr-flow daemon`。

## 测试架构

```
tests/
├── test_hotkey.py       # 77 个测试：热键注册、单键/组合键、stop 清理
├── test_loop.py         # VoiceInputLoop 状态转换、回调、错误恢复
├── test_recorder.py     # 音频采集、WAV 格式、超时、清理
├── test_transcriber.py  # 模型下载、加载、识别
├── test_state.py        # State 枚举完整性
├── test_transition.py   # 状态转换逻辑
├── test_injector.py     # X11 注入器、环境检测
├── test_notifier.py     # 提示音播放
├── test_cli.py          # CLI 命令、desktop 文件生成
├── test_lock.py         # 单实例锁、PID 存活检测、死锁恢复
├── test_config.py       # 配置文件加载、默认生成、容错降级
└── test_integration.py  # 完整生命周期集成测试
```

所有外部依赖（pynput, sounddevice, funasr, modelscope, subprocess）均通过 mock 隔离。测试完全在内存中运行，不依赖真实音频设备、GPU 或外部命令。
