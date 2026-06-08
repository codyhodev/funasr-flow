import sys
import time
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from funasr_flow.recorder import Recorder


@pytest.fixture
def mock_sd():
    """在 sys.modules 中注入 mock sounddevice。"""
    mock_sd_mod = MagicMock()
    mock_stream = MagicMock()
    mock_sd_mod.InputStream.return_value = mock_stream

    with patch.dict(sys.modules, {"sounddevice": mock_sd_mod}):
        yield mock_sd_mod, mock_stream


class TestRecorderStart:
    def test_start_opens_input_stream(self, mock_sd):
        """start 打开 sounddevice InputStream。"""
        mock_sd_mod, mock_stream = mock_sd
        rec = Recorder()
        rec.start()

        mock_sd_mod.InputStream.assert_called_once()
        mock_stream.start.assert_called_once()

    def test_start_with_correct_audio_params(self, mock_sd):
        """start 使用正确的音频参数。"""
        mock_sd_mod, _ = mock_sd
        rec = Recorder()
        rec.start()

        kwargs = mock_sd_mod.InputStream.call_args[1]
        assert kwargs["samplerate"] == 16000
        assert kwargs["channels"] == 1
        assert kwargs["dtype"] == "int16"

    def test_is_recording_returns_true_after_start(self, mock_sd):
        """start 后 is_recording 返回 True。"""
        rec = Recorder()
        rec.start()
        assert rec.is_recording()

    def test_start_when_already_recording_raises(self, mock_sd):
        """已在录音时再次调用 start 抛出异常。"""
        rec = Recorder()
        rec.start()
        with pytest.raises(RuntimeError, match="already recording"):
            rec.start()


class TestRecorderStop:
    def test_stop_returns_wav_file_path(self, mock_sd):
        """stop 返回 WAV 文件路径。"""
        rec = Recorder()
        rec.start()
        wav_path = rec.stop()

        assert wav_path.endswith(".wav")
        assert wav_path.startswith(rec.tmp_dir)

    def test_stop_when_not_recording_raises(self, mock_sd):
        """未在录音时调用 stop 抛出异常。"""
        rec = Recorder()
        with pytest.raises(RuntimeError, match="not recording"):
            rec.stop()

    def test_is_recording_false_after_stop(self, mock_sd):
        """stop 后 is_recording 返回 False。"""
        rec = Recorder()
        rec.start()
        rec.stop()
        assert not rec.is_recording()


class TestRecorderWavOutput:
    def test_stop_writes_valid_wav(self, tmp_path, mock_sd):
        """stop 输出格式正确的 WAV 文件。"""
        mock_sd_mod, mock_stream = mock_sd
        rec = Recorder(tmp_dir=str(tmp_path))

        rec.start()
        # 注入一帧模拟音频数据到 raw 文件
        fake_data = np.zeros(16000, dtype=np.int16)
        rec._callback(fake_data, 16000, None, None)
        wav_path = rec.stop()

        with wave.open(wav_path, "r") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2  # 16-bit
            assert wf.getframerate() == 16000

    def test_empty_recording_still_valid_wav(self, tmp_path, mock_sd):
        """空录音仍产生合法 WAV 文件。"""
        rec = Recorder(tmp_dir=str(tmp_path))
        rec.start()
        wav_path = rec.stop()

        with wave.open(wav_path, "r") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 16000

    def test_raw_file_deleted_after_stop(self, tmp_path, mock_sd):
        """stop 后 raw 文件被删除。"""
        rec = Recorder(tmp_dir=str(tmp_path))
        rec.start()
        raw_path = rec._raw_path
        assert Path(raw_path).exists()

        rec.stop()
        assert not Path(raw_path).exists()

    def test_cleanup_deletes_wav_file(self, tmp_path, mock_sd):
        """cleanup 删除 WAV 文件。"""
        rec = Recorder(tmp_dir=str(tmp_path))
        rec.start()
        wav_path = rec.stop()

        assert Path(wav_path).exists()
        rec.cleanup()
        assert not Path(wav_path).exists()

    def test_callback_writes_to_raw_file(self, tmp_path, mock_sd):
        """callback 将音频数据流式写入 raw 文件。"""
        rec = Recorder(tmp_dir=str(tmp_path))
        rec.start()

        fake_data = np.ones(8000, dtype=np.int16)
        rec._callback(fake_data, 8000, None, None)
        rec._callback(fake_data, 8000, None, None)

        # 检查 raw 文件大小：16000 帧 × 2 bytes = 32000
        assert Path(rec._raw_path).stat().st_size == 32000

        rec.stop()


class TestRecorderTimeout:
    def test_recording_stops_after_max_duration(self, mock_sd):
        """录音达到最大时长后自动停止。"""
        rec = Recorder(max_duration=0.1)
        rec.start()
        assert rec.is_recording()

        time.sleep(0.2)
        assert not rec.is_recording()
