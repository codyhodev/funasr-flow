"""集成测试：mock 所有外部依赖，验证完整状态转换链路。"""

import sys
import threading
from unittest.mock import MagicMock, patch

import pytest

from funasr_flow.state import State


@pytest.fixture
def mocks():
    """mock 所有外部依赖，返回组装好的 VoiceInputLoop。"""
    from funasr_flow.loop import VoiceInputLoop

    hotkey = MagicMock()
    recorder = MagicMock()
    recorder.stop.return_value = "/tmp/funasr-flow/test.wav"
    on_rec_start = MagicMock()
    on_rec_stop = MagicMock()
    transcriber = MagicMock()
    transcriber.transcribe.return_value = "集成测试文本"
    injector = MagicMock()

    loop = VoiceInputLoop(
        hotkey,
        recorder,
        transcriber,
        injector,
        on_recording_start=on_rec_start,
        on_recording_stop=on_rec_stop,
    )
    return {
        "loop": loop,
        "hotkey": hotkey,
        "recorder": recorder,
        "on_rec_start": on_rec_start,
        "on_rec_stop": on_rec_stop,
        "transcriber": transcriber,
        "injector": injector,
    }


class TestFullLifecycle:
    def test_complete_happy_path(self, mocks):
        """完整成功路径：按热键→录音→按热键→识别→注入→清理。"""
        lo = mocks["loop"]

        # 初始状态
        assert lo.state == State.IDLE

        # 第一次热键：开始录音
        lo._on_hotkey()
        assert lo.state == State.RECORDING
        mocks["on_rec_start"].assert_called_once()
        mocks["recorder"].start.assert_called_once()

        # 第二次热键：停止并处理
        lo._on_hotkey()
        assert lo.state == State.IDLE
        mocks["recorder"].stop.assert_called_once()
        mocks["on_rec_stop"].assert_called_once()
        mocks["transcriber"].transcribe.assert_called_once_with("/tmp/funasr-flow/test.wav")
        mocks["injector"].assert_called_once_with("集成测试文本")
        mocks["recorder"].cleanup.assert_called_once()

    def test_ignore_hotkey_while_transcribing(self, mocks):
        """识别期间热键被忽略，状态不应被破坏。"""
        lo = mocks["loop"]

        lo.state = State.TRANSCRIBING
        lo._on_hotkey()

        assert lo.state == State.TRANSCRIBING
        mocks["recorder"].start.assert_not_called()
        mocks["recorder"].stop.assert_not_called()

    def test_error_recovery_sets_idle(self, mocks):
        """识别失败后恢复 IDLE，不注入，清理仍执行。"""
        lo = mocks["loop"]
        mocks["transcriber"].transcribe.side_effect = RuntimeError("模拟错误")

        lo._on_hotkey()   # IDLE → RECORDING
        lo._on_hotkey()   # RECORDING → TRANSCRIBING → (error) → IDLE

        assert lo.state == State.IDLE
        mocks["injector"].assert_not_called()
        mocks["recorder"].cleanup.assert_called_once()

    def test_multiple_record_cycles(self, mocks):
        """多次录音循环，每次状态正确恢复。"""
        lo = mocks["loop"]

        for i in range(3):
            assert lo.state == State.IDLE
            lo._on_hotkey()
            assert lo.state == State.RECORDING
            lo._on_hotkey()
            assert lo.state == State.IDLE

        assert mocks["recorder"].start.call_count == 3
        assert mocks["recorder"].stop.call_count == 3
        assert mocks["transcriber"].transcribe.call_count == 3
        assert mocks["injector"].call_count == 3
        assert mocks["recorder"].cleanup.call_count == 3

    def test_state_transitions_are_strict(self, mocks):
        """状态机转换严格：只能 IDLE→RECORDING→TRANSCRIBING→IDLE。"""
        lo = mocks["loop"]

        # IDLE → RECORDING
        lo._on_hotkey()
        assert lo.state == State.RECORDING

        # RECORDING → TRANSCRIBING (temporarily, then → IDLE)
        lo._on_hotkey()
        # State should be IDLE by now (transcribe happens in _stop_and_transcribe)
        assert lo.state == State.IDLE

        # IDLE → RECORDING (can start again)
        lo._on_hotkey()
        assert lo.state == State.RECORDING

    def test_start_method_wiring(self, mocks):
        """start 方法正确连接 hotkey 参数。"""
        lo = mocks["loop"]
        lo.start()

        from funasr_flow.loop import HOTKEY_SPEC
        mocks["hotkey"].grab_key.assert_called_once_with(HOTKEY_SPEC)
        mocks["hotkey"].start.assert_called_once_with(lo._on_hotkey)
