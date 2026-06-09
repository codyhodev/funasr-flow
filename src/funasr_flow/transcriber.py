"""FunASR SenseVoice-Small 语音识别模块。"""

import os
from pathlib import Path

MODEL_ID = "iic/SenseVoiceSmall"
DEFAULT_CACHE_DIR = os.path.expanduser("~/.cache/funasr-flow/models")


def download_model(cache_dir: str = DEFAULT_CACHE_DIR) -> str:
    """下载模型到缓存目录。已存在则跳过。返回模型目录路径。"""
    from modelscope.hub.snapshot_download import snapshot_download

    os.makedirs(cache_dir, exist_ok=True)

    model_dir = os.path.join(cache_dir, "iic", "SenseVoiceSmall")
    if _model_dir_exists(model_dir):
        return model_dir

    return snapshot_download(MODEL_ID, cache_dir=cache_dir)


# FunASR rich_transcription_postprocess 会转换的情感/事件 emoji
_FUNASR_EMOJIS = {
    "😊", "😔", "😡", "😰", "🤢", "😮",  # emotion
    "🎼", "👏", "😀", "😭", "🤧", "😷",  # event
}


def _strip_emojis(text: str) -> str:
    """去除 FunASR 后处理引入的情感/事件 emoji。"""
    for emoji in _FUNASR_EMOJIS:
        text = text.replace(emoji, "")
    return text


def _model_dir_exists(model_dir: str) -> bool:
    p = Path(model_dir)
    return p.is_dir() and (p / "config.yaml").exists()


class Transcriber:
    """SenseVoice-Small 语音识别器。"""

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR, device: str = "cpu"):
        self._cache_dir = cache_dir
        self._device = device
        self._model = None

    def _model_dir(self) -> str:
        return os.path.join(self._cache_dir, "iic", "SenseVoiceSmall")

    def load_model(self) -> None:
        """加载模型到内存。优先使用本地缓存。"""
        if self._model is not None:
            return

        from funasr import AutoModel

        model_dir = self._model_dir()
        model_path = model_dir if _model_dir_exists(model_dir) else MODEL_ID

        self._model = AutoModel(
            model=model_path,
            device=self._device,
            disable_update=True,
            disable_pbar=True,
            use_itn=True,
        )

    def transcribe(self, wav_path: str) -> str:
        """识别 WAV 文件，返回干净文本。"""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        result = self._model.generate(input=wav_path)
        if result and len(result) > 0:
            text = result[0].get("text", "")
            from funasr.utils.postprocess_utils import rich_transcription_postprocess
            text = rich_transcription_postprocess(text)
            text = _strip_emojis(text)
            return text
        return ""

    @property
    def is_loaded(self) -> bool:
        return self._model is not None
