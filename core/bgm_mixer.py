"""
Background Music (BGM) Auto-Duck & Audio Mixer for GENAUDIO
Mixes voiceovers with ambient background music using FFmpeg automatic sidechain compression / audio ducking.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

BGM_DIR = Path(__file__).resolve().parent / "bgm"
BGM_DIR.mkdir(parents=True, exist_ok=True)

class BGMMixer:
    def __init__(self, bgm_dir: Optional[Path] = None):
        self.bgm_dir = bgm_dir or BGM_DIR
        self.bgm_dir.mkdir(parents=True, exist_ok=True)

    def list_bgm_tracks(self) -> List[Path]:
        """List all available BGM tracks."""
        return list(self.bgm_dir.glob("*.mp3")) + list(self.bgm_dir.glob("*.wav"))

    def mix_voice_and_bgm(
        self,
        voice_audio: Path,
        bgm_audio: Path,
        output_file: Path,
        voice_volume: float = 1.0,
        bgm_volume: float = 0.18,
        ducking_threshold: float = 0.08,
        fade_out_seconds: float = 2.0
    ) -> Dict[str, Any]:
        """
        Mixes voiceover with BGM using FFmpeg sidechain compression (auto-ducking).
        BGM volume automatically drops when voice is active.
        """
        if not voice_audio.exists():
            return {"success": False, "error": f"Voice file not found: {voice_audio}"}
        if not bgm_audio.exists():
            return {"success": False, "error": f"BGM file not found: {bgm_audio}"}

        output_file.parent.mkdir(parents=True, exist_ok=True)

        # FFmpeg filter:
        # 1. Loop BGM infinitely
        # 2. Adjust BGM base volume
        # 3. Apply sidechaincompress keyed to voice track
        # 4. Fade out BGM at end of voice track
        # 5. Mix both together
        filter_complex = (
            f"[1:a]aloop=loop=-1:size=2e+09,volume={bgm_volume}[bgm_loop];"
            f"[bgm_loop][0:a]sidechaincompress=threshold={ducking_threshold}:ratio=6:attack=20:release=350[ducked_bgm];"
            f"[0:a]volume={voice_volume}[voice_adj];"
            f"[voice_adj][ducked_bgm]amix=inputs=2:duration=first:dropout_transition=2[out]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(voice_audio),
            "-i", str(bgm_audio),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-ac", "2",
            "-b:a", "192k",
            str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            size_kb = output_file.stat().st_size // 1024
            return {
                "success": True,
                "file": output_file,
                "size_kb": size_kb,
                "voice_track": str(voice_audio),
                "bgm_track": str(bgm_audio)
            }
        except Exception as e:
            return {"success": False, "error": f"FFmpeg BGM mix failed: {e}"}
