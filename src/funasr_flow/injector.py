"""文本注入模块 —— 将识别文本写入剪贴板并模拟粘贴。"""

import shutil
import subprocess
import time
from collections.abc import Callable


def make_x11_injector() -> Callable[[str], None]:
    """返回使用 xclip + xdotool 的文本注入器（X11 环境）。

    返回的 inject(text) 将文本写入剪贴板，然后模拟 Ctrl+Shift+V 粘贴。
    如果 xclip 或 xdotool 不可用，函数调用时会静默失败。
    """

    def inject(text: str) -> None:
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard", "-in"],
                input=text, text=True, timeout=2,
            )
            time.sleep(0.05)
            subprocess.run(
                ["xdotool", "key", "ctrl+shift+v"],
                timeout=2,
            )
        except Exception:
            pass  # 注入失败不抛异常，用户可手动粘贴

    return inject


def detect_injector() -> Callable[[str], None]:
    """检测环境，返回合适的文本注入器。"""
    if shutil.which("xdotool") and shutil.which("xclip"):
        return make_x11_injector()

    # 降级：仅复制到剪贴板，不自动粘贴
    def clipboard_only(text: str) -> None:
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard", "-in"],
                input=text, text=True, timeout=2,
            )
        except Exception:
            pass

    return clipboard_only


# 默认实例：模块加载时检测环境
inject = detect_injector()
