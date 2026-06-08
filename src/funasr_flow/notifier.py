"""用户反馈：提示音。"""

import numpy as np

_SAMPLE_RATE = 16000


def _beep(frequency: float, duration_ms: int) -> None:
    """生成一个短促正弦提示音。"""
    try:
        import sounddevice as sd
        samples = int(_SAMPLE_RATE * duration_ms / 1000)
        t = np.linspace(0, duration_ms / 1000, samples, endpoint=False)
        wave = (0.5 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
        sd.play(wave, samplerate=_SAMPLE_RATE, blocking=True)
    except Exception:
        pass  # 音频设备不可用时静默


def play_beep_start() -> None:
    """开始录音提示音：440Hz 短促声。"""
    _beep(440, 150)


def play_beep_stop() -> None:
    """停止录音提示音：两声短促 600Hz。"""
    _beep(600, 100)
    _beep(600, 100)

