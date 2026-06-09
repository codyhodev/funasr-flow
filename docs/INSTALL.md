# 安装与卸载

## 环境要求

- **操作系统：** Linux（X11 桌面环境）
- **Python：** ≥ 3.10
- **包管理器：** uv（推荐）或 pip

## 系统依赖安装

### Debian/Ubuntu

```bash
sudo apt install -y xclip xdotool ffmpeg portaudio19-dev python3-dev
```

### Arch Linux

```bash
sudo pacman -S xclip xdotool ffmpeg portaudio python
```

### Fedora

```bash
sudo dnf install xclip xdotool ffmpeg portaudio-devel python3-devel
```

### 说明

| 依赖 | 用途 | 缺失时的降级行为 |
|------|------|-----------------|
| `xclip` | 将识别文本写入 X11 剪贴板 | 自动降级为仅复制到剪贴板，不自动粘贴 |
| `xdotool` | 模拟 Ctrl+Shift+V 粘贴操作 | 同上 |
| `ffmpeg` | FunASR 音频编解码后端 | 程序无法启动 |
| `libportaudio` | sounddevice 音频采集后端 | 程序无法启动 |

## Python 环境安装

```bash
# 克隆项目
git clone <repo-url> funasr-flow
cd funasr-flow

# 创建虚拟环境
uv venv
source .venv/bin/activate

# 安装项目（编辑模式，方便开发）
uv pip install -e . -i https://mirrors.aliyun.com/pypi/simple/

# 或从 wheel 安装（生产环境）
uv pip install dist/funasr_flow-0.1.0-py3-none-any.whl \
    -i https://mirrors.aliyun.com/pypi/simple/
```

`-i https://mirrors.aliyun.com/pypi/simple/` 使用阿里云 PyPI 镜像加速下载。

## 安装到桌面自启

```bash
funasr-flow install
```

### install 执行步骤

```
1. 下载 SenseVoice-Small 模型
   └─ 检查 ~/.cache/funasr-flow/models/iic/SenseVoiceSmall/
      如果 config.yaml 存在 → 跳过下载
      否则 → ModelScope snapshot_download 下载到缓存目录
      模型大小约 300MB

2. 写入 XDG desktop 文件
   └─ 路径: ~/.local/share/applications/funasr-flow.desktop
   └─ 内容:
      [Desktop Entry]
      Type=Application
      Name=FunASR Flow
      Comment=语音输入服务（右 Ctrl 开始/停止录音）
      Exec=funasr-flow daemon
      Icon=<安装目录>/icons/app.png
      Terminal=false
      Categories=Utility;
```

### desktop 文件关键字段

- **Exec:** 使用 `shutil.which("funasr-flow")` 解析可执行路径，确保登录时能找到
- **Icon:** 指向安装目录下的 `app.png`（128×128）
- **Terminal=false:** 不显示终端窗口
- **Categories=Utility:** 在应用菜单中归类为工具

### 验证安装

```bash
# 检查 desktop 文件是否存在
ls -l ~/.local/share/applications/funasr-flow.desktop

# 手动测试启动（不在 autostart 中）
funasr-flow daemon
# 应出现系统托盘图标，按下右 Ctrl 应发出提示音
```

桌面环境（GNOME、KDE、XFCE 等）会在下次登录时自动启动守护进程。

## 配置文件

配置文件位于 `~/.config/funasr-flow/config.yaml`，首次启动自动生成。格式：

```yaml
# FunASR Flow 配置文件
hotkey: "<ctrl_r>"       # 全局热键，pynput 格式

transcriber:
  device: "cpu"          # cpu | cuda | cuda:0 | mps | npu:0
```

### 修改热键

```yaml
hotkey: "<ctrl_l>"       # 改用左 Ctrl
hotkey: "<ctrl>+<alt>+r" # 使用组合键
```

支持 pynput 格式的单键和组合键。

### 启用 CUDA 加速

```yaml
transcriber:
  device: "cuda"
```

- 需要安装 CUDA 版 PyTorch：`pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121`
- 如果 CUDA 不可用，FunASR 会自动回退到 CPU，不会崩溃
- 多 GPU 环境可指定设备：`device: "cuda:0"` / `device: "cuda:1"`

修改配置后需重启守护进程生效。

### 重新登录或手动启动

安装后不会自动启动当前进程。可以：

1. **重新登录** — 桌面环境会自动启动
2. **手动启动** — 终端运行 `funasr-flow daemon`
3. **从应用菜单启动** — 搜索 "FunASR Flow"

## 卸载

```bash
funasr-flow uninstall
```

### uninstall 执行步骤

```
1. 删除 desktop 文件
   └─ 路径: ~/.local/share/applications/funasr-flow.desktop
      文件存在 → 删除，输出 "已移除桌面自启文件"
      文件不存在 → 无操作（幂等）
```

### 注意事项

- **不杀死进程：** uninstall 只移除 desktop 自启文件。如果有正在运行的实例，需要手动终止或从托盘菜单退出。
- **不删除模型：** 模型缓存在 `~/.cache/funasr-flow/models/` 保留。如需彻底清理，手动删除该目录。
- **不删除临时文件：** 运行时录音临时文件在 `/tmp/funasr-flow/`，可手动清理。
- **不删除配置文件：** 配置文件在 `~/.config/funasr-flow/config.yaml` 保留。

### 彻底清理

```bash
# 卸载自启
funasr-flow uninstall

# 删除模型缓存（约 300MB）
rm -rf ~/.cache/funasr-flow/

# 删除配置文件
rm -rf ~/.config/funasr-flow/

# 删除临时录音文件
rm -rf /tmp/funasr-flow/

# 删除虚拟环境和项目
deactivate
rm -rf /path/to/funasr-flow/.venv
rm -rf /path/to/funasr-flow
```

## 守护进程生命周期

```
系统登录
    │
    ▼
桌面环境读取 ~/.local/share/applications/funasr-flow.desktop
    │
    ▼
执行 funasr-flow daemon
    │
    ├─ 获取进程锁 (lock.acquire)，已有实例则退出
    ├─ 加载配置文件 (~/.config/funasr-flow/config.yaml)
    ├─ 创建 QApplication
    ├─ 初始化 HotkeyListener + Recorder + Transcriber + Injector
    ├─ 创建系统托盘图标
    ├─ 注册 SIGTERM / SIGINT 信号处理
    └─ 进入 Qt 事件循环 (app.exec_())
    │
    ▼ (用户退出)
托盘右键 → 退出
    │
    ├─ loop.stop() → 停止热键监听
    ├─ tray.stop() → 隐藏托盘图标
    └─ app.quit() → 退出事件循环
```

**信号处理：** `SIGTERM` 和 `SIGINT` 会优雅退出，执行与"退出"菜单相同的清理流程。

## 开发模式

```bash
# 安装开发依赖
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]" -i https://mirrors.aliyun.com/pypi/simple/

# 运行测试
pytest

# 直接运行守护进程（无需安装 desktop 文件）
python -m funasr_flow.cli daemon
```
