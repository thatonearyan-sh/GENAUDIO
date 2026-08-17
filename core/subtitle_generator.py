"""
Subtitle & Caption Generator for GENAUDIO
Generates synchronized .SRT and .VTT subtitle files for video editors (Premiere, DaVinci, CapCut, Final Cut).
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import List, Dict, Any

class SubtitleGenerator:
    @staticmethod
    def format_timestamp_srt(seconds: float) -> str:
        """Format seconds into SRT timestamp 00:00:00,000."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def format_timestamp_vtt(seconds: float) -> str:
        """Format seconds into VTT timestamp 00:00:00.000."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"

    @classmethod
    def generate_subtitles(
        cls,
        segments: List[Dict[str, Any]], # list of {"text": ..., "duration": ...}
        output_srt_path: Path,
        generate_vtt: bool = True
    ) -> Dict[str, Any]:
        """
        Generates .srt (and optionally .vtt) subtitle files.
        """
        output_srt_path.parent.mkdir(parents=True, exist_ok=True)
        srt_lines = []
        vtt_lines = ["WEBVTT\n"]
        current_time = 0.0

        for idx, seg in enumerate(segments, 1):
            dur = seg.get("duration", 3.0)
            start_time = current_time
            end_time = current_time + dur
            current_time = end_time

            # Strip emotion tags from captions
            clean_text = re.sub(r'\[[a-zA-Z,\s_-]+\]', '', seg.get("text", "")).strip()

            # SRT entry
            srt_lines.append(str(idx))
            srt_lines.append(f"{cls.format_timestamp_srt(start_time)} --> {cls.format_timestamp_srt(end_time)}")
            srt_lines.append(clean_text)
            srt_lines.append("") # Blank line separator

            # VTT entry
            vtt_lines.append(str(idx))
            vtt_lines.append(f"{cls.format_timestamp_vtt(start_time)} --> {cls.format_timestamp_vtt(end_time)}")
            vtt_lines.append(clean_text)
            vtt_lines.append("")

        srt_content = "\n".join(srt_lines)
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        vtt_path = None
        if generate_vtt:
            vtt_path = output_srt_path.with_suffix(".vtt")
            with open(vtt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(vtt_lines))

        return {
            "success": True,
            "srt_file": output_srt_path,
            "vtt_file": vtt_path,
            "total_subtitles": len(segments)
        }
