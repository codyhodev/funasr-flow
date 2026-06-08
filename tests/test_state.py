from funasr_flow.state import State


def test_state_has_three_values():
    """State 枚举包含 IDLE, RECORDING, TRANSCRIBING 三个值。"""
    assert State.IDLE.value == "idle"
    assert State.RECORDING.value == "recording"
    assert State.TRANSCRIBING.value == "transcribing"


def test_state_values_are_unique():
    """State 枚举的值互不相同。"""
    values = [s.value for s in State]
    assert len(values) == len(set(values))


def test_state_is_enum():
    """State 是 Python Enum 类型。"""
    assert isinstance(State.IDLE, State)
