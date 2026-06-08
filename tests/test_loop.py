from unittest.mock import MagicMock

from funasr_flow.state import State


class TestVoiceInputLoop:
    def _make_loop(self, on_rec_start=None, on_rec_stop=None):
        from funasr_flow.loop import VoiceInputLoop
        hotkey = MagicMock()
        recorder = MagicMock()
        transcriber = MagicMock()
        transcriber.transcribe.return_value = "你好世界"
        injector = MagicMock()
        lo = VoiceInputLoop(
            hotkey,
            recorder,
            transcriber,
            injector,
            on_recording_start=on_rec_start or MagicMock(),
            on_recording_stop=on_rec_stop or MagicMock(),
        )
        return lo, hotkey, recorder, transcriber, injector

    def test_first_hotkey_starts_recording(self):
        """首次热键：回调 on_recording_start → 状态变为 RECORDING → 开始录音。"""
        on_start = MagicMock()
        lo, hotkey, rec, tc, inj = self._make_loop(on_rec_start=on_start)
        lo._on_hotkey()

        on_start.assert_called_once()
        rec.start.assert_called_once()
        assert lo.state == State.RECORDING

    def test_second_hotkey_stops_and_transcribes(self):
        """再次热键：停止录音 → 识别 → 注入文本。"""
        on_stop = MagicMock()
        lo, hotkey, rec, tc, inj = self._make_loop(on_rec_stop=on_stop)
        rec.stop.return_value = "/tmp/test.wav"

        lo._on_hotkey()
        lo._on_hotkey()

        rec.stop.assert_called_once()
        on_stop.assert_called_once()
        tc.transcribe.assert_called_once_with("/tmp/test.wav")
        assert lo.state == State.IDLE

    def test_transcribed_text_is_injected(self):
        """识别文本被注入到光标位置。"""
        lo, hotkey, rec, tc, inj = self._make_loop()
        rec.stop.return_value = "/tmp/test.wav"
        tc.transcribe.return_value = "今天天气真好"

        lo._on_hotkey()
        lo._on_hotkey()

        inj.assert_called_once_with("今天天气真好")

    def test_start_registers_hotkey(self):
        """start 调用 grab_key + hotkey.start（非阻塞）。"""
        from funasr_flow.loop import HOTKEY_SPEC
        lo, hotkey, rec, tc, inj = self._make_loop()
        lo.start()

        hotkey.grab_key.assert_called_once_with(HOTKEY_SPEC)
        hotkey.start.assert_called_once_with(lo._on_hotkey)
        hotkey._listener.join.assert_not_called()

    def test_stop_calls_hotkey_stop(self):
        """stop 调用 hotkey.stop()。"""
        lo, hotkey, rec, tc, inj = self._make_loop()
        lo.stop()
        hotkey.stop.assert_called_once()

    def test_cleanup_called_after_transcribe(self):
        """识别和注入完成后调用 recorder.cleanup。"""
        lo, hotkey, rec, tc, inj = self._make_loop()
        lo._on_hotkey()
        lo._on_hotkey()

        rec.cleanup.assert_called_once()

    def test_hotkey_when_transcribing_is_ignored(self):
        """TRANSCRIBING 状态下热键被忽略。"""
        on_start = MagicMock()
        lo, hotkey, rec, tc, inj = self._make_loop(on_rec_start=on_start)
        lo.state = State.TRANSCRIBING
        lo._on_hotkey()

        on_start.assert_not_called()
        rec.start.assert_not_called()

    def test_transcribe_error_recovers(self):
        """识别出错时恢复 IDLE，不注入。"""
        lo, hotkey, rec, tc, inj = self._make_loop()
        rec.stop.return_value = "/tmp/test.wav"
        tc.transcribe.side_effect = RuntimeError("识别失败")

        lo._on_hotkey()
        lo._on_hotkey()

        assert lo.state == State.IDLE
        inj.assert_not_called()
        rec.cleanup.assert_called_once()

    def test_on_recording_callbacks_are_optional(self):
        """on_recording_start 和 on_recording_stop 为 None 时不报错。"""
        lo, hotkey, rec, tc, inj = self._make_loop(on_rec_start=None, on_rec_stop=None)
        rec.stop.return_value = "/tmp/test.wav"

        lo._on_hotkey()
        assert lo.state == State.RECORDING

        lo._on_hotkey()
        assert lo.state == State.IDLE
        inj.assert_called_once()
