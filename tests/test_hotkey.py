from unittest.mock import MagicMock, patch

import pytest

from funasr_flow.hotkey import HotkeyListener


@pytest.fixture
def mock_pynput():
    """mock pynput.keyboard.Listener + HotKey。

    返回 (mock_listener, mock_hotkey) 两个 mock 类：
      - mock_listener() 返回 mock_listener.return_value（MagicMock 实例）
      - mock_listener.call_args 捕获 Listener(...) 的调用参数
      - mock_hotkey.call_args 捕获 HotKey(...) 的调用参数
    """
    with patch("funasr_flow.hotkey.Listener") as mock_listener, \
         patch("funasr_flow.hotkey.HotKey") as mock_hotkey:
        mock_listener.return_value = MagicMock()
        mock_hotkey.return_value = MagicMock()
        yield mock_listener, mock_hotkey


# ── grab_key ──────────────────────────────────────────────────────────────

class TestGrabKey:
    def test_grab_key_stores_spec(self):
        """grab_key 保存热键规格字符串。"""
        listener = HotkeyListener()
        listener.grab_key("<ctrl_r>")
        assert listener._key_spec == "<ctrl_r>"

    def test_grab_key_twice_raises(self):
        """重复 grab 抛出 RuntimeError。"""
        listener = HotkeyListener()
        listener.grab_key("<ctrl_r>")
        with pytest.raises(RuntimeError, match="already grabbed"):
            listener.grab_key("<ctrl>+a")

    def test_grab_key_supports_combo(self):
        """grab_key 支持组合键规格。"""
        listener = HotkeyListener()
        listener.grab_key("<ctrl>+<alt>+r")
        assert listener._key_spec == "<ctrl>+<alt>+r"


# ── start (单键) ───────────────────────────────────────────────────────────

class TestStartSingle:
    def test_start_requires_grab_first(self):
        """未 grab 就 start 抛出 RuntimeError。"""
        listener = HotkeyListener()
        with pytest.raises(RuntimeError, match="grab_key"):
            listener.start(MagicMock())

    def test_starts_listener_with_on_press(self, mock_pynput):
        """单键模式：创建 Listener 只传 on_press。"""
        mock_listener, mock_hotkey = mock_pynput

        listener = HotkeyListener()
        listener.grab_key("<ctrl_r>")
        listener.start(MagicMock())

        assert mock_listener.call_args is not None
        kwargs = mock_listener.call_args[1]
        assert "on_press" in kwargs
        assert "on_release" not in kwargs
        mock_listener.return_value.start.assert_called_once()

    def test_single_key_triggers_callback(self, mock_pynput):
        """单键按下时触发 callback。"""
        mock_listener, mock_hotkey = mock_pynput

        listener = HotkeyListener()
        listener.grab_key("<ctrl_r>")

        callback = MagicMock()
        listener.start(callback)

        on_press = mock_listener.call_args[1]["on_press"]
        from pynput.keyboard import Key
        on_press(Key.ctrl_r)

        callback.assert_called_once()

    def test_single_key_wrong_key_ignored(self, mock_pynput):
        """非目标键（左 Ctrl、Shift 等）不触发 callback。"""
        mock_listener, mock_hotkey = mock_pynput

        listener = HotkeyListener()
        listener.grab_key("<ctrl_r>")

        callback = MagicMock()
        listener.start(callback)

        on_press = mock_listener.call_args[1]["on_press"]
        from pynput.keyboard import Key
        on_press(Key.ctrl_l)
        on_press(Key.ctrl)
        on_press(Key.shift)

        callback.assert_not_called()

    def test_single_key_directly_uses_key_object(self, mock_pynput):
        """单键模式不使用 HotKey，直接用 Listener 匹配原始 Key 对象。"""
        mock_listener, mock_hotkey = mock_pynput

        listener = HotkeyListener()
        listener.grab_key("<ctrl_r>")
        listener.start(MagicMock())

        # HotKey 没有被创建（单键不经过 _start_combo）
        mock_hotkey.assert_not_called()


# ── start (组合键) ─────────────────────────────────────────────────────────

class TestStartCombo:
    def test_parses_hotkey_spec(self, mock_pynput):
        """组合键模式：用 HotKey.parse 解析键规格。"""
        mock_listener, mock_hotkey = mock_pynput

        listener = HotkeyListener()
        listener.grab_key("<ctrl>+a")

        with patch("funasr_flow.hotkey.HotKey.parse") as mock_parse:
            mock_parse.return_value = {MagicMock(), MagicMock()}
            listener.start(MagicMock())

        mock_parse.assert_called_once_with("<ctrl>+a")

    def test_passes_callback_to_hotkey(self, mock_pynput):
        """组合键模式：callback 传给 HotKey 构造器。"""
        mock_listener, mock_hotkey = mock_pynput

        listener = HotkeyListener()
        listener.grab_key("<ctrl>+<alt>+h")

        callback = MagicMock()
        listener.start(callback)

        assert mock_hotkey.call_args is not None
        pos_args = mock_hotkey.call_args[0]
        assert pos_args[1] is callback

    def test_listener_has_on_press_and_on_release(self, mock_pynput):
        """组合键模式：Listener 同时传 on_press 和 on_release。"""
        mock_listener, mock_hotkey = mock_pynput

        listener = HotkeyListener()
        listener.grab_key("<ctrl>+<alt>+h")
        listener.start(MagicMock())

        assert mock_listener.call_args is not None
        kwargs = mock_listener.call_args[1]
        assert "on_press" in kwargs
        assert "on_release" in kwargs


# ── stop ───────────────────────────────────────────────────────────────────

class TestStop:
    def test_stop_clears_state(self, mock_pynput):
        """stop 清理内部状态（listener 是 daemon 线程，不需 join）。"""
        mock_listener, mock_hotkey = mock_pynput

        listener = HotkeyListener()
        listener.grab_key("<ctrl_r>")
        listener.start(MagicMock())
        listener.stop()

        assert listener._listener is None
        assert listener._hotkey is None

    def test_stop_before_start_is_safe(self):
        """未 start 时 stop 不报错。"""
        listener = HotkeyListener()
        listener.stop()
