import os
import shutil
import signal
import sys
from pathlib import Path

DESKTOP_FILE_NAME = "funasr-flow.desktop"
APPLICATIONS_DIR = str(Path.home() / ".local/share/applications")


def _exec_path() -> str:
    return shutil.which("funasr-flow") or os.path.abspath(sys.argv[0])


def _icon_path() -> str:
    """返回应用图标 (app.png) 的绝对路径。"""
    return str(Path(__file__).resolve().parent / "icons" / "app.png")


def desktop_file_content() -> str:
    return f"""[Desktop Entry]
Type=Application
Name=FunASR Flow
Comment=语音输入服务（右 Ctrl 开始/停止录音）
Exec={_exec_path()} daemon
Icon={_icon_path()}
Terminal=false
Categories=Utility;
"""


def _download_model() -> None:
    from funasr_flow.transcriber import download_model
    print("正在下载 SenseVoice-Small 模型...")
    model_dir = download_model()
    print(f"模型已就绪: {model_dir}")


def cmd_install() -> None:
    _download_model()

    apps_dir = Path(APPLICATIONS_DIR)
    apps_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = apps_dir / DESKTOP_FILE_NAME
    desktop_file.write_text(desktop_file_content())
    print(f"已安装: {desktop_file}")


def cmd_uninstall() -> None:
    desktop_file = Path(APPLICATIONS_DIR) / DESKTOP_FILE_NAME
    if desktop_file.exists():
        desktop_file.unlink()
        print("已移除桌面自启文件")


def cmd_daemon() -> None:
    """前台运行守护进程，由桌面 autostart 管理生命周期。"""
    from PyQt5.QtWidgets import QApplication

    from funasr_flow.loop import make_voice_input_loop
    from funasr_flow.notifier import play_beep_start, play_beep_stop
    from funasr_flow.state import State
    from funasr_flow.tray import TrayIcon

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    loop = make_voice_input_loop(
        on_recording_start=play_beep_start,
        on_recording_stop=play_beep_stop,
        on_state_change=lambda s: (
            tray.set_recording() if s == State.RECORDING else tray.set_idle()
        ),
    )

    tray = TrayIcon(
        app,
        on_enable=lambda: (loop.enable(), tray.set_enabled_state(True)),
        on_disable=lambda: (loop.disable(), tray.set_enabled_state(False)),
        on_quit=loop.stop,
    )
    tray.start()

    def _do_quit():
        loop.stop()
        tray.stop()
        app.quit()

    def _handle_sigterm(signum, frame):
        _do_quit()

    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT, _handle_sigterm)

    loop.start()
    app.exec_()
    _do_quit()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="FunASR Flow 语音输入服务")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("install", help="安装到桌面自启并下载模型")
    sub.add_parser("uninstall", help="移除桌面自启文件")
    sub.add_parser("daemon", help="前台运行守护进程")

    args = parser.parse_args()

    if args.command == "install":
        cmd_install()
    elif args.command == "uninstall":
        cmd_uninstall()
    elif args.command == "daemon":
        cmd_daemon()
