from funasr_flow.state import State
from funasr_flow.transition import next_on_toggle


class TestNextOnToggle:
    def test_idle_to_recording(self):
        """IDLE 状态下热键 → RECORDING。"""
        assert next_on_toggle(State.IDLE) == State.RECORDING

    def test_recording_to_transcribing(self):
        """RECORDING 状态下热键 → TRANSCRIBING。"""
        assert next_on_toggle(State.RECORDING) == State.TRANSCRIBING

    def test_transcribing_ignored(self):
        """TRANSCRIBING 状态下热键被忽略，返回 None。"""
        assert next_on_toggle(State.TRANSCRIBING) is None

    def test_returns_none_only_for_transcribing(self):
        """只有 TRANSCRIBING 状态返回 None。"""
        assert next_on_toggle(State.IDLE) is not None
        assert next_on_toggle(State.RECORDING) is not None
