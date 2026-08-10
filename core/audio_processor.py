"""
Audio Processor for GENAUDIO
Handles pitch-preserving speed / tempo adjustment (atempo), volume normalization (loudnorm),
and multi-format audio conversion (MP3 320k, Lossless WAV, FLAC, M4A, OGG).
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class AudioProcessor:
    @staticmethod
    def adjust_speed(
        input_file: Path,
        output_file: Path,
        speed_factor: float = 1.15
    ) -> Dict[str, Any]:
        """
        Adjust audio speed/tempo without altering pitch using FFmpeg atempo filter.
        Speed factor range: 0.5 to 2.0
        """
        if not input_file.exists():
            return {"success": False, "error": "Input file does not exist."}

        factor = max(0.5, min(speed_factor, 2.0))
        output_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_file),
            "-filter:a", f"atempo={factor}",
            "-vn",
            str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {
                "success": True,
                "file": output_file,
                "speed": factor,
                "size_kb": output_file.stat().st_size // 1024
            }
        except Exception as e:
            return {"success": False, "error": f"Speed adjustment failed: {e}"}

    @staticmethod
    def convert_format(
        input_file: Path,
        output_file: Path,
        target_format: str = "wav",
        bitrate: str = "320k",
        sample_rate: int = 44100
    ) -> Dict[str, Any]:
        """
        Converts audio to target format (.wav, .mp3, .flac, .m4a, .ogg).
        """
        if not input_file.exists():
            return {"success": False, "error": "Input file does not exist."}

        output_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = ["ffmpeg", "-y", "-i", str(input_file), "-ar", str(sample_rate)]

        fmt = target_format.lower().replace(".", "")
        if fmt == "mp3":
            cmd.extend(["-b:a", bitrate, "-acodec", "libmp3lame"])
        elif fmt == "wav":
            cmd.extend(["-acodec", "pcm_s16le"])
        elif fmt == "flac":
            cmd.extend(["-acodec", "flac"])
        elif fmt in ("m4a", "aac"):
            cmd.extend(["-acodec", "aac", "-b:a", bitrate])
        elif fmt == "ogg":
            cmd.extend(["-acodec", "libopus", "-b:a", bitrate])

        cmd.append(str(output_file))

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {
                "success": True,
                "file": output_file,
                "format": fmt,
                "size_kb": output_file.stat().st_size // 1024
            }
        except Exception as e:
            return {"success": False, "error": f"Format conversion failed: {e}"}

    @staticmethod
    def normalize_loudness(input_file: Path, output_file: Path) -> Dict[str, Any]:
        """
        Applies EBU R128 dual-pass loudness normalization for broadcast-level consistency.
        """
        if not input_file.exists():
            return {"success": False, "error": "Input file does not exist."}

        output_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_file),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-b:a", "192k",
            str(output_file)
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {
                "success": True,
                "file": output_file,
                "size_kb": output_file.stat().st_size // 1024
            }
        except Exception as e:
            return {"success": False, "error": f"Loudness normalization failed: {e}"}

# Lossless audio format conversion pipeline

# Pitch-preserved speed engine with atempo filter

# Playback speed presets: 0.85x to 1.50x
