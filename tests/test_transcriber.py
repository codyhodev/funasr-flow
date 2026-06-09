import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from funasr_flow.transcriber import (
    Transcriber,
    MODEL_ID,
    DEFAULT_CACHE_DIR,
    download_model,
    _model_dir_exists,
)


# ---- helpers ----

def _seed_mock_modelscope():
    """在 sys.modules 中注入 mock modelscope。"""
    mock_ms = MagicMock()
    mock_ms.__path__ = []
    mock_sd = MagicMock()
    mock_sd.return_value = "/tmp/test-models/iic/SenseVoiceSmall"

    mock_hub = MagicMock()
    mock_hub.snapshot_download = mock_sd
    mock_ms.hub = mock_hub

    mock_sd_mod = MagicMock()
    mock_sd_mod.snapshot_download = mock_sd
    mock_ms.hub.snapshot_download = mock_sd_mod

    with patch.dict(sys.modules, {
        "modelscope": mock_ms,
        "modelscope.hub": mock_ms.hub,
        "modelscope.hub.snapshot_download": mock_sd_mod,
    }):
        yield mock_sd


def _seed_mock_funasr():
    """在 sys.modules 中注入 mock funasr，含完整包层级。"""
    mock_funasr = MagicMock()
    mock_funasr.__path__ = []
    mock_model = MagicMock()
    mock_model.generate.return_value = [{"text": "你好世界"}]
    mock_funasr.AutoModel.return_value = mock_model

    mock_utils = MagicMock()
    mock_utils.__path__ = []
    mock_ppu = MagicMock()
    mock_ppu.rich_transcription_postprocess = lambda x: x
    mock_utils.postprocess_utils = mock_ppu
    mock_funasr.utils = mock_utils

    with patch.dict(sys.modules, {
        "funasr": mock_funasr,
        "funasr.utils": mock_utils,
        "funasr.utils.postprocess_utils": mock_ppu,
    }):
        yield mock_funasr, mock_model


# ---- download_model (standalone function) ----

class TestDownloadModel:
    def test_calls_snapshot_download(self):
        """download_model 调用 modelscope snapshot_download。"""
        for mock_sd in _seed_mock_modelscope():
            with patch("funasr_flow.transcriber._model_dir_exists", return_value=False):
                download_model(cache_dir="/tmp/test-models")

        mock_sd.assert_called_once()
        assert mock_sd.call_args[1]["cache_dir"] == "/tmp/test-models"

    def test_skips_if_exists(self):
        """模型已存在时跳过下载。"""
        for mock_sd in _seed_mock_modelscope():
            with patch("funasr_flow.transcriber._model_dir_exists", return_value=True):
                download_model(cache_dir="/tmp/test-models")

        assert mock_sd.call_count == 0

    def test_returns_model_dir(self):
        """download_model 返回模型目录路径。"""
        for mock_sd in _seed_mock_modelscope():
            with patch("funasr_flow.transcriber._model_dir_exists", return_value=False):
                result = download_model(cache_dir="/tmp/test-models")

        assert "SenseVoiceSmall" in result

    def test_no_dependency_on_transcriber(self):
        """download_model 不依赖 Transcriber 类。"""
        # 直接调用，不需要实例化 Transcriber
        for mock_sd in _seed_mock_modelscope():
            with patch("funasr_flow.transcriber._model_dir_exists", return_value=False):
                result = download_model()
        assert isinstance(result, str)


# ---- _model_dir_exists ----

class TestModelDirExists:
    def test_checks_config_file(self, tmp_path):
        """_model_dir_exists 检查模型目录中的 config.yaml。"""
        model_dir = tmp_path / "SenseVoiceSmall"
        model_dir.mkdir()
        (model_dir / "config.yaml").write_text("model: SenseVoiceSmall")
        assert _model_dir_exists(str(model_dir))

    def test_returns_false_when_dir_missing(self, tmp_path):
        """模型目录不存在时返回 False。"""
        assert not _model_dir_exists(str(tmp_path / "nonexistent"))


# ---- Transcriber ----

class TestTranscriberLoad:
    def test_load_creates_automodel(self):
        """load_model 创建 FunASR AutoModel。"""
        t = Transcriber()
        with patch("funasr_flow.transcriber._model_dir_exists", return_value=False):
            for mock_funasr, _ in _seed_mock_funasr():
                t.load_model()

        mock_funasr.AutoModel.assert_called_once()
        kwargs = mock_funasr.AutoModel.call_args[1]
        assert kwargs["model"] == MODEL_ID

    def test_load_sets_loaded_flag(self):
        """加载后 is_loaded 返回 True。"""
        t = Transcriber()
        with patch("funasr_flow.transcriber._model_dir_exists", return_value=False):
            for _, _ in _seed_mock_funasr():
                t.load_model()

        assert t.is_loaded

    def test_load_twice_is_noop(self):
        """重复加载不重复创建模型。"""
        t = Transcriber()
        with patch("funasr_flow.transcriber._model_dir_exists", return_value=False):
            for mock_funasr, _ in _seed_mock_funasr():
                t.load_model()
                t.load_model()

        mock_funasr.AutoModel.assert_called_once()


class TestTranscriberTranscribeEmojiStrip:
    """验证 transcribe 会去除 rich_transcription_postprocess 引入的 emoji。

    生产环境中 rich_transcription_postprocess 将情感/事件标签转为 emoji。
    这里直接生成带 emoji 的文本来模拟其输出。
    """

    def test_strips_sad_emoji(self):
        """😔（SAD）被去除。"""
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            mock_model.generate.return_value = [{"text": "开始测试。😔"}]
            t.load_model()
            result = t.transcribe("/tmp/test.wav")
        assert "😔" not in result
        assert result == "开始测试。"

    def test_strips_happy_emoji(self):
        """😊（HAPPY）被去除。"""
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            mock_model.generate.return_value = [{"text": "你好。😊"}]
            t.load_model()
            result = t.transcribe("/tmp/test.wav")
        assert "😊" not in result
        assert result == "你好。"

    def test_strips_angry_emoji(self):
        """😡（ANGRY）被去除。"""
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            mock_model.generate.return_value = [{"text": "不行。😡"}]
            t.load_model()
            result = t.transcribe("/tmp/test.wav")
        assert "😡" not in result

    def test_strips_multiple_emojis(self):
        """多个情感 emoji 全部去除。"""
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            mock_model.generate.return_value = [{"text": "大家好。😊今天天气不错。😔"}]
            t.load_model()
            result = t.transcribe("/tmp/test.wav")
        assert "😊" not in result
        assert "😔" not in result
        assert result == "大家好。今天天气不错。"

    def test_strips_event_emojis(self):
        """事件 emoji（鼓掌等）也被去除。"""
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            mock_model.generate.return_value = [{"text": "谢谢大家。👏"}]
            t.load_model()
            result = t.transcribe("/tmp/test.wav")
        assert "👏" not in result
        assert result == "谢谢大家。"

    def test_strips_all_funasr_emojis(self):
        """FunASR 定义的所有 emotion/event emoji 全部去除。"""
        all_emojis = "😊😔😡😰🤢😮🎼👏😀😭🤧😷"
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            mock_model.generate.return_value = [{"text": f"测试{all_emojis}文本"}]
            t.load_model()
            result = t.transcribe("/tmp/test.wav")
        for ch in all_emojis:
            assert ch not in result, f"emoji {ch} 未被去除"
        assert result == "测试文本"

    def test_no_emoji_unchanged(self):
        """无 emoji 的文本保持不变。"""
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            mock_model.generate.return_value = [{"text": "今天天气真好"}]
            t.load_model()
            result = t.transcribe("/tmp/test.wav")
        assert result == "今天天气真好"

    def test_empty_result(self):
        """空结果不抛异常。"""
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            mock_model.generate.return_value = []
            t.load_model()
            result = t.transcribe("/tmp/test.wav")
        assert result == ""


class TestTranscriberTranscribe:
    def test_transcribe_returns_text(self):
        """transcribe 返回识别文本。"""
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            mock_model.generate.return_value = [{"text": "你好世界"}]
            t.load_model()
            result = t.transcribe("/tmp/test.wav")

        assert result == "你好世界"

    def test_transcribe_passes_wav_path_to_model(self):
        """transcribe 将 WAV 路径传给模型。"""
        t = Transcriber()
        for mock_funasr, mock_model in _seed_mock_funasr():
            t.load_model()
            t.transcribe("/tmp/audio.wav")

        mock_model.generate.assert_called_once()
        kwargs = mock_model.generate.call_args[1]
        assert kwargs["input"] == "/tmp/audio.wav"

    def test_transcribe_requires_loaded_model(self):
        """未加载模型时调用 transcribe 抛出异常。"""
        t = Transcriber()
        with pytest.raises(RuntimeError, match="not loaded"):
            t.transcribe("/tmp/test.wav")
