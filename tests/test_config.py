"""测试配置文件管理。"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from funasr_flow.config import (
    CONFIG_DIR,
    CONFIG_FILE,
    Config,
    DEFAULT_HOTKEY,
    DEFAULT_DEVICE,
    DEFAULT_YAML,
    load_config,
)


class TestConfig:
    """测试 Config 数据类。"""

    def test_default_values(self):
        """Config 默认值。"""
        c = Config()
        assert c.hotkey == DEFAULT_HOTKEY
        assert c.transcriber_device == DEFAULT_DEVICE

    def test_custom_values(self):
        """Config 自定义值。"""
        c = Config(hotkey="<ctrl_l>", transcriber_device="cuda")
        assert c.hotkey == "<ctrl_l>"
        assert c.transcriber_device == "cuda"


class TestLoadConfigDefault:
    """测试配置文件不存在时自动生成。"""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """每个测试前后清理配置文件。"""
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        yield
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

    def test_generates_default_when_no_file(self):
        """配置文件不存在时自动生成并返回默认值。"""
        assert not CONFIG_FILE.exists()
        config = load_config()
        assert CONFIG_FILE.exists()
        assert config.hotkey == DEFAULT_HOTKEY
        assert config.transcriber_device == DEFAULT_DEVICE

    def test_generated_file_has_expected_content(self):
        """自动生成的配置文件包含热键和 transcriber 配置。"""
        load_config()
        content = CONFIG_FILE.read_text()
        assert f'hotkey: "{DEFAULT_HOTKEY}"' in content
        assert f'device: "{DEFAULT_DEVICE}"' in content

    def test_config_dir_is_created(self):
        """自动生成时创建配置目录。"""
        # 清理整个目录以测试自动创建
        import shutil
        if CONFIG_DIR.exists():
            shutil.rmtree(CONFIG_DIR)
        load_config()
        assert CONFIG_DIR.is_dir()
        assert CONFIG_FILE.is_file()


class TestLoadConfigExisting:
    """测试配置文件已存在时的加载。"""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        yield
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

    def test_loads_existing_config(self):
        """加载已有配置文件。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text("hotkey: '<ctrl_l>'\ntranscriber:\n  device: 'cuda'\n")
        config = load_config()
        assert config.hotkey == "<ctrl_l>"
        assert config.transcriber_device == "cuda"

    def test_missing_hotkey_uses_default(self):
        """hotkey 缺失时使用默认值。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text("transcriber:\n  device: 'cuda'\n")
        config = load_config()
        assert config.hotkey == DEFAULT_HOTKEY
        assert config.transcriber_device == "cuda"

    def test_missing_device_uses_default(self):
        """transcriber.device 缺失时使用默认值。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text("hotkey: '<ctrl_l>'\n")
        config = load_config()
        assert config.hotkey == "<ctrl_l>"
        assert config.transcriber_device == DEFAULT_DEVICE

    def test_empty_hotkey_uses_default(self):
        """hotkey 为空字符串时使用默认值。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text("hotkey:\ntranscriber:\n  device: 'cuda'\n")
        config = load_config()
        assert config.hotkey == DEFAULT_HOTKEY

    def test_broken_yaml_returns_defaults(self):
        """YAML 格式损坏时返回默认值。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text("hotkey: [bad: yaml: here\n")
        config = load_config()
        assert config.hotkey == DEFAULT_HOTKEY
        assert config.transcriber_device == DEFAULT_DEVICE

    def test_empty_file_returns_defaults(self):
        """空配置文件返回默认值。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text("")
        config = load_config()
        assert config.hotkey == DEFAULT_HOTKEY
        assert config.transcriber_device == DEFAULT_DEVICE

    def test_missing_transcriber_section_uses_default_device(self):
        """整个 transcriber 段缺失时，device 使用默认值。"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text("hotkey: '<ctrl_l>'\n")
        config = load_config()
        assert config.transcriber_device == DEFAULT_DEVICE
