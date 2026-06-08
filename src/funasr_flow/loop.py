"""热键录音回路 —— 串联 hotkey → recorder → transcriber → injector。"""

import time
from collections.abc import Callable

from funasr_flow.state import State
from funasr_flow.transition import next_on_toggle

HOTKEY_SPEC = "<ctrl_r>"


class VoiceInputLoop:
    """热键驱动的录音 → 识别 → 注入回路。"""

    def __init__(
        self,
        hotkey,
        recorder,
        transcriber,
        injector: Callable[[str], None],
        *,
        on_recording_start: Callable[[], None] | None = None,
        on_recording_stop: Callable[[], None] | None = None,
        on_state_change: Callable[["State"], None] | None = None,
    ):
        self._hotkey = hotkey
        self._recorder = recorder
        self._transcriber = transcriber
        self._injector = injector
        self._on_recording_start = on_recording_start
        self._on_recording_stop = on_recording_stop
        self._on_state_change = on_state_change
        self.state = State.IDLE
        self._enabled = True
        self._start_time: float = 0.0

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False
        # 如果正在录音，停止录音并清理，避免残留状态
        if self.state == State.RECORDING:
            self._recorder.stop()
            self._recorder.cleanup()
            self._set_state(State.IDLE)

    def _set_state(self, state: State) -> None:
        self.state = state
        if self._on_state_change:
            self._on_state_change(state)

    def _on_hotkey(self) -> None:
        if not self._enabled:
            return
        nxt = next_on_toggle(self.state)
        if nxt == State.RECORDING:
            self._set_state(State.RECORDING)
            self._start_time = time.monotonic()
            if self._on_recording_start:
                self._on_recording_start()
            self._recorder.start()
        elif nxt == State.TRANSCRIBING:
            self._stop_and_transcribe()

    def _stop_and_transcribe(self) -> None:
        wav_path = self._recorder.stop()
        if self._on_recording_stop:
            self._on_recording_stop()
        self._set_state(State.TRANSCRIBING)

        try:
            text = self._transcriber.transcribe(wav_path)
            self._injector(text)
        except Exception:
            pass
        finally:
            self._recorder.cleanup()
            self._set_state(State.IDLE)

    def start(self) -> None:
        """启动热键监听（非阻塞）。配合 Qt 等外部事件循环使用。"""
        self._hotkey.grab_key(HOTKEY_SPEC)
        self._hotkey.start(self._on_hotkey)

    def stop(self) -> None:
        """停止热键监听。"""
        self._hotkey.stop()

    def run(self) -> None:
        """启动并阻塞直到停止。适用于没有外部事件循环的场景。"""
        self.start()
        # 阻塞等待：在新线程等 join
        import threading
        self._hotkey._listener.join()


def make_voice_input_loop(
    *,
    on_recording_start: Callable[[], None] | None = None,
    on_recording_stop: Callable[[], None] | None = None,
    on_state_change: Callable[[State], None] | None = None,
    injector: Callable[[str], None] | None = None,
) -> VoiceInputLoop:
    """工厂函数：创建并返回一个完全初始化好的 VoiceInputLoop。"""
    from funasr_flow.hotkey import HotkeyListener
    from funasr_flow.injector import inject as _default_injector
    from funasr_flow.recorder import Recorder
    from funasr_flow.transcriber import Transcriber

    transcriber = Transcriber()
    transcriber.load_model()

    return VoiceInputLoop(
        hotkey=HotkeyListener(),
        recorder=Recorder(),
        transcriber=transcriber,
        injector=injector or _default_injector,
        on_recording_start=on_recording_start,
        on_recording_stop=on_recording_stop,
        on_state_change=on_state_change,
    )
