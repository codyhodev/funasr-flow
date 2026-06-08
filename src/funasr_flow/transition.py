"""状态机：定义 VoiceInputLoop 的合法状态转换。"""

from funasr_flow.state import State


def next_on_toggle(current: State) -> State | None:
    """热键按下时，返回下一个状态。无合法转换返回 None（事件被忽略）。

    IDLE       → RECORDING
    RECORDING  → TRANSCRIBING
    其他       → None（TRANSCRIBING 期间忽略热键）
    """
    if current == State.IDLE:
        return State.RECORDING
    if current == State.RECORDING:
        return State.TRANSCRIBING
    return None
