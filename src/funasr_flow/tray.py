"""系统托盘图标 (PyQt5) —— idle/recording/disabled 状态，右键菜单。"""

from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QSystemTrayIcon

_ICONS_DIR = Path(__file__).resolve().parent / "icons"


class TrayIcon:
    """系统托盘图标管理器 (PyQt5 QSystemTrayIcon)。"""

    def __init__(self, app, *, on_enable=None, on_disable=None, on_quit=None):
        self._app = app
        self._on_enable = on_enable
        self._on_disable = on_disable
        self._on_quit = on_quit
        self._idle_icon = QIcon(str(_ICONS_DIR / "mic_idle.png"))
        self._recording_icon = QIcon(str(_ICONS_DIR / "mic_recording.png"))
        self._disabled_icon = QIcon(str(_ICONS_DIR / "mic_disabled.png"))
        self._tray = None
        self._enabled = True
        self._active_icon = self._idle_icon

    def start(self) -> None:
        if self._tray is not None:
            return

        self._tray = QSystemTrayIcon()
        self._tray.setIcon(self._idle_icon)
        self._tray.setToolTip("FunASR Flow")

        self._action_enable = QAction("启用")
        self._action_enable.triggered.connect(self._handle_enable)

        self._action_disable = QAction("禁用")
        self._action_disable.triggered.connect(self._handle_disable)

        menu = QMenu()
        menu.addAction(self._action_enable)
        menu.addAction(self._action_disable)
        menu.addSeparator()
        menu.addAction("退出", self._handle_quit)
        self._tray.setContextMenu(menu)

        self._tray.show()
        self.set_enabled_state(True)

    def set_enabled_state(self, enabled: bool) -> None:
        self._enabled = enabled
        self._action_enable.setVisible(not enabled)
        self._action_disable.setVisible(enabled)
        self._refresh_icon()
        if self._tray:
            label = "FunASR Flow" if enabled else "FunASR Flow [已禁用]"
            self._tray.setToolTip(label)

    def set_idle(self) -> None:
        self._active_icon = self._idle_icon
        self._refresh_icon()

    def set_recording(self) -> None:
        self._active_icon = self._recording_icon
        self._refresh_icon()

    def _refresh_icon(self) -> None:
        if self._tray:
            icon = self._disabled_icon if not self._enabled else self._active_icon
            self._tray.setIcon(icon)

    def stop(self) -> None:
        if self._tray:
            self._tray.hide()
            self._tray = None

    def _handle_enable(self) -> None:
        if self._on_enable:
            self._on_enable()
        self.set_enabled_state(True)

    def _handle_disable(self) -> None:
        if self._on_disable:
            self._on_disable()
        self.set_enabled_state(False)

    def _handle_quit(self) -> None:
        if self._on_quit:
            self._on_quit()
        self._app.quit()
