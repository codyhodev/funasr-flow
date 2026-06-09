import os
import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

from funasr_flow.cli import (
    APPLICATIONS_DIR,
    DESKTOP_FILE_NAME,
    desktop_file_content,
    cmd_install,
    cmd_uninstall,
    cmd_daemon,
)


def test_desktop_file_contains_key_fields():
    """desktop 文件包含必要字段。"""
    content = desktop_file_content()
    assert "Type=Application" in content
    assert "Name=FunASR Flow" in content
    assert "Exec=" in content
    assert "Icon=" in content
    assert "app.png" in content
    assert " daemon" in content
    assert "Terminal=false" in content
    assert "Categories=Utility;" in content


def test_desktop_file_execstart_points_to_funasr_flow():
    """Exec 指向 funasr-flow 可执行文件。"""
    import shutil
    content = desktop_file_content()
    expected = shutil.which("funasr-flow") or os.path.abspath("funasr-flow")
    assert f"Exec={expected} daemon" in content


class TestInstall:
    def test_install_writes_desktop_file(self, tmp_path):
        apps_dir = tmp_path / "applications"
        apps_dir.mkdir(parents=True)

        with patch("funasr_flow.cli.APPLICATIONS_DIR", str(apps_dir)), \
             patch("funasr_flow.cli._download_model"):
            cmd_install()

        desktop_file = apps_dir / DESKTOP_FILE_NAME
        assert desktop_file.is_file()
        assert "Type=Application" in desktop_file.read_text()


class TestUninstall:
    def test_uninstall_removes_desktop_file(self, tmp_path):
        apps_dir = tmp_path / "applications"
        apps_dir.mkdir(parents=True)
        desktop_file = apps_dir / DESKTOP_FILE_NAME
        desktop_file.write_text("[Desktop Entry]\n")

        with patch("funasr_flow.cli.APPLICATIONS_DIR", str(apps_dir)):
            cmd_uninstall()

        assert not desktop_file.exists()

    def test_uninstall_noop_when_no_file(self, tmp_path):
        apps_dir = tmp_path / "applications"
        apps_dir.mkdir(parents=True)

        with patch("funasr_flow.cli.APPLICATIONS_DIR", str(apps_dir)):
            cmd_uninstall()  # 不应抛异常


class TestDaemon:
    def test_cmd_daemon_registers_signal_handlers(self):
        """cmd_daemon 注册 SIGTERM 和 SIGINT 信号处理。"""
        mock_loop = MagicMock()
        mock_app = MagicMock()

        mock_config = MagicMock()
        mock_config.hotkey = "<ctrl_r>"
        mock_config.transcriber_device = "cpu"

        with patch("funasr_flow.config.load_config", return_value=mock_config), \
             patch("funasr_flow.cli.signal.signal") as mock_signal, \
             patch("PyQt5.QtWidgets.QApplication", return_value=mock_app), \
             patch("funasr_flow.loop.make_voice_input_loop", return_value=mock_loop), \
             patch("funasr_flow.tray.TrayIcon"):
            cmd_daemon()

        assert mock_signal.call_count >= 2
        called_signals = {c.args[0] for c in mock_signal.call_args_list}
        assert signal.SIGTERM in called_signals
        assert signal.SIGINT in called_signals
        mock_loop.start.assert_called_once()
        mock_app.exec_.assert_called_once()
