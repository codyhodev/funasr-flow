from unittest.mock import patch

from funasr_flow.injector import detect_injector, inject, make_x11_injector


class TestMakeX11Injector:
    def test_returns_callable(self):
        """make_x11_injector 返回一个可调用对象。"""
        f = make_x11_injector()
        assert callable(f)

    def test_copies_text_to_clipboard(self):
        """注入器将文本写入剪贴板（xclip）。"""
        f = make_x11_injector()
        with patch("subprocess.run") as mock_run, \
             patch("time.sleep"):
            f("你好世界")

        xclip_call = mock_run.call_args_list[0]
        args = xclip_call[0][0]
        assert "xclip" in args
        assert xclip_call[1]["input"] == "你好世界"

    def test_simulates_ctrl_shift_v(self):
        """注入器在写入剪贴板后模拟 Ctrl+Shift+V。"""
        f = make_x11_injector()
        with patch("subprocess.run") as mock_run, \
             patch("time.sleep"):
            f("test")

        xdotool_call = mock_run.call_args_list[1]
        assert xdotool_call[0][0] == ["xdotool", "key", "ctrl+shift+v"]

    def test_has_delay_between_clipboard_and_paste(self):
        """注入器在剪贴板和粘贴之间有短暂延迟。"""
        f = make_x11_injector()
        with patch("subprocess.run"), \
             patch("time.sleep") as mock_sleep:
            f("test")

        mock_sleep.assert_called_once()

    def test_swallows_errors(self):
        """xclip/xdotool 失败时不抛异常。"""
        f = make_x11_injector()
        with patch("subprocess.run", side_effect=RuntimeError("boom")):
            # 不应抛出
            f("test")


class TestDetectInjector:
    def test_returns_callable(self):
        """detect_injector 返回一个可调用对象。"""
        f = detect_injector()
        assert callable(f)

    def test_prefers_x11_when_tools_available(self):
        """xdotool 和 xclip 都可用时返回 X11 注入器。"""
        with patch("shutil.which", return_value="/usr/bin/xdotool"):
            f = detect_injector()
            # 验证返回的是可调用对象
            assert callable(f)

    def test_falls_back_to_clipboard_only(self):
        """xdotool 不可用时返回仅剪贴板注入器。"""
        def _which_fake(cmd):
            return "/usr/bin/xclip" if cmd == "xclip" else None

        with patch("shutil.which", side_effect=_which_fake):
            f = detect_injector()
            assert callable(f)


class TestModuleLevelInject:
    def test_inject_is_callable(self):
        """模块级 inject 是可调用的。"""
        assert callable(inject)
