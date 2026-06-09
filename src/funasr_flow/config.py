"""配置文件管理 —— YAML 格式，首次启动自动生成默认配置。"""

import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CONFIG_DIR = Path.home() / ".config" / "funasr-flow"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_HOTKEY = "<ctrl_r>"
DEFAULT_DEVICE = "cpu"

DEFAULT_YAML = f"""# FunASR Flow 配置文件
hotkey: "{DEFAULT_HOTKEY}"     # 全局热键，pynput 格式

transcriber:
  device: "{DEFAULT_DEVICE}"   # cpu | cuda | cuda:0 | mps | npu:0
"""


@dataclass
class Config:
    hotkey: str = DEFAULT_HOTKEY
    transcriber_device: str = DEFAULT_DEVICE


def load_config() -> Config:
    """加载配置文件，不存在则自动生成默认配置。

    容错策略：YAML 损坏或 key 缺失时打印 warning 并使用默认值，
    确保程序始终可以启动。
    """
    if not CONFIG_FILE.exists():
        return _generate_default()

    try:
        raw = yaml.safe_load(CONFIG_FILE.read_text()) or {}
    except yaml.YAMLError as e:
        print(f"配置文件解析失败: {e}，使用默认值", file=sys.stderr)
        return Config()

    hotkey = _str_or_default(raw.get("hotkey"), DEFAULT_HOTKEY, "hotkey")
    transcriber = raw.get("transcriber") or {}
    device = _str_or_default(transcriber.get("device"), DEFAULT_DEVICE, "transcriber.device")

    return Config(hotkey=hotkey, transcriber_device=device)


def _str_or_default(value, default: str, key_name: str) -> str:
    """校验值为非空字符串，否则使用默认值并打印 warning。"""
    if isinstance(value, str) and value.strip():
        return value.strip()
    print(f"配置项 '{key_name}' 值无效，使用默认值 '{default}'", file=sys.stderr)
    return default


def _generate_default() -> Config:
    """生成默认配置文件并返回默认 Config。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(DEFAULT_YAML)
    return Config()
