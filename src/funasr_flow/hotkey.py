"""全局热键监听器（基于 pynput，跨平台）。"""

from pynput.keyboard import HotKey, Key, KeyCode, Listener


def _resolve_key(key_spec: str):
    """将 key_spec 解析为 pynput Key 或 KeyCode 对象。"""
    name = key_spec.strip("<>")
    if hasattr(Key, name):
        return getattr(Key, name)
    elif len(name) == 1:
        return KeyCode.from_char(name)
    else:
        raise ValueError(f"Unknown key: {key_spec}")


class HotkeyListener:
    """监听全局热键，按键时触发回调。"""

    def __init__(self):
        self._listener: Listener | None = None
        self._hotkey: HotKey | None = None
        self._key_spec: str | None = None

    def grab_key(self, key_spec: str) -> None:
        """注册全局热键。必须在 start() 之前调用。

        key_spec 格式示例：
          - 单键: '<ctrl_r>', '<ctrl_l>', 'a', '<f1>'
          - 组合: '<ctrl>+<alt>+r', '<shift>+a'
        """
        if self._key_spec is not None:
            raise RuntimeError("Hotkey already grabbed")
        self._key_spec = key_spec

    def start(self, callback) -> None:
        """开始监听。按键按下时触发 callback。"""
        if self._key_spec is None:
            raise RuntimeError("Must call grab_key() before start()")

        if "+" in self._key_spec:
            self._start_combo(callback)
        else:
            self._start_single(callback)

    def _start_combo(self, callback) -> None:
        """组合键模式：用 HotKey 状态机匹配多键组合。"""
        self._hotkey = HotKey(
            HotKey.parse(self._key_spec),
            callback,
        )

        def _on_press(k):
            self._hotkey.press(self._listener.canonical(k))

        def _on_release(k):
            self._hotkey.release(self._listener.canonical(k))

        self._listener = Listener(
            on_press=_on_press,
            on_release=_on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def _start_single(self, callback) -> None:
        """单键模式：直接用 Listener 匹配。"""
        target = _resolve_key(self._key_spec)

        def on_press(key):
            if key == target:
                callback()

        self._listener = Listener(on_press=on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """停止监听。监听线程是 daemon，进程退出时自动清理。"""
        self._listener = None
        self._hotkey = None
