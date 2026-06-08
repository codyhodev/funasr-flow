import os
import struct
import tempfile
import threading
import wave

import numpy as np


class Recorder:
    """音频采集器：16kHz 单声道 16-bit PCM，流式写入磁盘，输出 WAV。"""

    def __init__(
        self,
        tmp_dir: str = "/tmp/funasr-flow",
        max_duration: float = 300.0,
    ):
        self.tmp_dir = tmp_dir
        self.max_duration = max_duration
        self._stream = None
        self._raw_file = None
        self._raw_path: str | None = None
        self._wav_path: str | None = None
        self._timer: threading.Timer | None = None
        self._frame_count = 0

    def _get_sd(self):
        import sounddevice as sd
        return sd

    def _callback(self, indata: np.ndarray, frames, time_info, status) -> None:
        if self._raw_file is not None:
            self._raw_file.write(indata.tobytes())
            self._frame_count += frames

    def start(self) -> None:
        if self._stream is not None:
            raise RuntimeError("Recorder is already recording")

        os.makedirs(self.tmp_dir, exist_ok=True)

        # 创建临时 raw 文件用于流式写入
        fd, self._raw_path = tempfile.mkstemp(suffix=".raw", dir=self.tmp_dir)
        self._raw_file = os.fdopen(fd, "wb")
        self._frame_count = 0

        sd = self._get_sd()
        self._stream = sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype="int16",
            callback=self._callback,
        )
        self._stream.start()

        if self.max_duration > 0:
            self._timer = threading.Timer(self.max_duration, self._on_timeout)
            self._timer.start()

    def _on_timeout(self) -> None:
        if self._stream is not None:
            self.stop()

    def stop(self) -> str:
        if self._stream is None:
            raise RuntimeError("Recorder is not recording")

        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

        self._stream.stop()
        self._stream.close()
        self._stream = None

        # 关闭 raw 文件
        if self._raw_file:
            self._raw_file.close()
            self._raw_file = None

        # 将 raw PCM 转为 WAV
        self._wav_path = self._raw_to_wav()
        return self._wav_path

    def is_recording(self) -> bool:
        return self._stream is not None

    def _raw_to_wav(self) -> str:
        fd, wav_path = tempfile.mkstemp(suffix=".wav", dir=self.tmp_dir)
        os.close(fd)

        with open(self._raw_path, "rb") as rf, wave.open(wav_path, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(16000)
            # 流式读取 raw 数据写入 WAV，避免一次性加载
            while True:
                chunk = rf.read(64000)  # 64KB per read
                if not chunk:
                    break
                wf.writeframesraw(chunk)

        # 删除 raw 文件
        if self._raw_path:
            os.unlink(self._raw_path)
            self._raw_path = None

        return wav_path

    def cleanup(self) -> None:
        if self._wav_path and os.path.exists(self._wav_path):
            os.unlink(self._wav_path)
            self._wav_path = None
