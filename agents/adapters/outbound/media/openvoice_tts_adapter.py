"""
OpenVoiceTTSAdapter — Gemini for media understanding + OpenVoice v2 for TTS.

Audio transcription, image/video description and image generation all delegate to
GeminiMediaAdapter. Only synthesize_speech() is replaced: it uses OpenVoice v2 +
MeloTTS to clone the voice from a reference audio sample.

Requirements:
    pip install git+https://github.com/myshell-ai/OpenVoice.git
    pip install git+https://github.com/myshell-ai/MeloTTS.git

Checkpoints (OpenVoice v2 converter) must be present at checkpoints_dir/converter/:
    config.json
    checkpoint.pth

Download script (run once):
    python -c "
    from huggingface_hub import snapshot_download
    snapshot_download('myshell-ai/OpenVoice', local_dir='checkpoints_v2')
    "
"""
from __future__ import annotations

import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from adapters.outbound.media.gemini_media_adapter import GeminiMediaAdapter

logger = logging.getLogger(__name__)


class OpenVoiceTTSAdapter(GeminiMediaAdapter):
    """
    Extends GeminiMediaAdapter with OpenVoice v2 voice cloning for TTS.

    Args:
        voice_sample_path: Path to reference audio (.ogg/.wav/.mp3, 3–30 s).
        language:          MeloTTS language code — "PT" for pt-BR.
        device:            "cpu" or "cuda".
        checkpoints_dir:   Dir containing OpenVoice v2 converter checkpoints.
        **gemini_kwargs:   Forwarded to GeminiMediaAdapter (audio_model, etc.).
    """

    def __init__(
        self,
        *,
        voice_sample_path: str,
        language: str = "PT",
        device: str = "cpu",
        checkpoints_dir: str = "checkpoints_v2",
        **gemini_kwargs,
    ) -> None:
        super().__init__(**gemini_kwargs)
        self._voice_sample = voice_sample_path
        self._language = language
        self._device = device
        self._ckpt_dir = checkpoints_dir

        # Lazy-loaded — heavy models loaded on first synthesis request
        self._tts = None
        self._converter = None
        self._target_se = None
        self._models_loaded = False

    # ------------------------------------------------------------------
    # Model loading (lazy, thread-safe via executor)
    # ------------------------------------------------------------------

    def _load_models(self) -> None:
        """Load MeloTTS + OpenVoice converter on first call."""
        if self._models_loaded:
            return

        try:
            from melo.api import TTS
            from openvoice import se_extractor
            from openvoice.api import ToneColorConverter
        except ImportError as exc:
            raise RuntimeError(
                "OpenVoice not installed. Run:\n"
                "  pip install git+https://github.com/myshell-ai/OpenVoice.git\n"
                "  pip install git+https://github.com/myshell-ai/MeloTTS.git"
            ) from exc

        logger.info("Loading MeloTTS (language=%s, device=%s)…", self._language, self._device)
        self._tts = TTS(language=self._language, device=self._device)

        ckpt_dir = Path(self._ckpt_dir) / "converter"
        if not (ckpt_dir / "config.json").exists():
            logger.warning(
                "OpenVoice checkpoints not found at %s — "
                "run: python -c \"from huggingface_hub import snapshot_download; "
                "snapshot_download('myshell-ai/OpenVoice', local_dir='checkpoints_v2')\"",
                ckpt_dir,
            )
            raise FileNotFoundError(f"OpenVoice checkpoints missing at {ckpt_dir}")

        logger.info("Loading OpenVoice converter from %s…", ckpt_dir)
        self._converter = ToneColorConverter(
            str(ckpt_dir / "config.json"), device=self._device
        )
        self._converter.load_ckpt(str(ckpt_dir / "checkpoint.pth"))

        if not Path(self._voice_sample).exists():
            raise FileNotFoundError(f"Voice sample not found: {self._voice_sample}")

        logger.info("Extracting speaker embedding from %s…", self._voice_sample)
        self._target_se, _ = se_extractor.get_se(
            self._voice_sample, self._converter, vad=True
        )

        self._models_loaded = True
        logger.info("OpenVoice v2 ready.")

    # ------------------------------------------------------------------
    # Synthesis (blocking — runs in thread pool)
    # ------------------------------------------------------------------

    def _synthesize_sync(self, text: str) -> Optional[bytes]:
        """Blocking synthesis pipeline: MeloTTS → tone conversion → OGG."""
        try:
            self._load_models()

            from openvoice import se_extractor

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp = Path(tmpdir)
                src_wav = tmp / "src.wav"
                out_wav = tmp / "out.wav"
                out_ogg = tmp / "out.ogg"

                # 1. Base speech via MeloTTS
                speaker_id = list(self._tts.hps.data.spk2id.values())[0]
                self._tts.tts_to_file(text, speaker_id, str(src_wav), speed=1.0)

                # 2. Source speaker embedding
                src_se, _ = se_extractor.get_se(
                    str(src_wav), self._converter, vad=False
                )

                # 3. Clone tone/timbre from reference voice
                self._converter.convert(
                    audio_src_path=str(src_wav),
                    src_se=src_se,
                    tgt_se=self._target_se,
                    output_path=str(out_wav),
                )

                # 4. Encode to OGG/Opus for WhatsApp
                result = subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-i", str(out_wav),
                        "-c:a", "libopus",
                        "-b:a", "32k",
                        str(out_ogg),
                        "-loglevel", "error",
                    ],
                    capture_output=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    logger.error(
                        "ffmpeg OGG encoding failed: %s",
                        result.stderr.decode(errors="replace"),
                    )
                    return None

                audio = out_ogg.read_bytes()
                logger.info(
                    "OpenVoice synthesized %d chars → %d bytes OGG",
                    len(text), len(audio),
                )
                return audio

        except Exception:
            logger.exception("OpenVoice synthesis failed for: %r", text[:80])
            return None

    # ------------------------------------------------------------------
    # MediaPort override
    # ------------------------------------------------------------------

    async def synthesize_speech(
        self,
        text: str,
        voice: str = "",
        voice_clone_sample: str = "",
    ) -> Optional[bytes]:
        """Offload blocking synthesis to thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._synthesize_sync, text)
