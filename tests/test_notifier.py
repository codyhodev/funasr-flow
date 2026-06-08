import sys
from unittest.mock import MagicMock, patch

import pytest

from funasr_flow.notifier import play_beep_start, play_beep_stop


@pytest.fixture
def mock_sd():
    """注入 mock sounddevice。"""
    mock = MagicMock()
    with patch.dict(sys.modules, {"sounddevice": mock}):
        yield mock


class TestBeep:
    def test_play_beep_start_calls_sd_play(self, mock_sd):
        """play_beep_start 调用 sounddevice.play。"""
        play_beep_start()
        mock_sd.play.assert_called_once()

    def test_play_beep_stop_calls_sd_play_twice(self, mock_sd):
        """play_beep_stop 调用两次 sounddevice.play。"""
        play_beep_stop()
        assert mock_sd.play.call_count == 2
