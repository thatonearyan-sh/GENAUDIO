"""
Multi-Voice Dialogue & Podcast Engine for GENAUDIO
Parses multi-character scripts, assigns distinct ElevenLabs voices to each character,
synthesizes dialogue turns, and merges into a conversational podcast track via FFmpeg.
"""
from __future__ import annotations
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from .generator import AudioGenerator
from .account_manager import AccountManager

class DialogueEngine:
    def __init__(self, generator: AudioGenerator, account_mgr: AccountManager):
        self.generator = generator
        self.account_mgr = account_mgr

    def parse_dialogue_script(self, script_text: str) -> List[Dict[str, str]]:
        """
        Parses script with speaker prefixes into dialogue turns.
        Supports:
        [SpeakerName]: Text here...
        SpeakerName: Text here...
        """
        turns = []
        lines = script_text.strip().splitlines()
        curr_speaker = "Narrator"
        curr_text = []

        pattern = re.compile(r'^(?:\[([^\]]+)\]|([A-Za-z0-9_\-\s]{2,25}))\s*:\s*(.*)$')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            # Make sure it's a speaker tag and not an emotion tag like [whispers]
            if match and not any(tag in line.lower() for tag in ["[whispers]", "[excited]", "[gasps]", "[amazed]", "[delighted]"] if line.lower().startswith(tag)):
                if curr_text:
                    turns.append({
                        "speaker": curr_speaker,
                        "text": " ".join(curr_text).strip()
                    })
                    curr_text = []
                speaker = (match.group(1) or match.group(2)).strip()
                curr_speaker = speaker
                body = match.group(3).strip()
                if body:
                    curr_text.append(body)
            else:
                curr_text.append(line)

        if curr_text:
            turns.append({
                "speaker": curr_speaker,
                "text": " ".join(curr_text).strip()
            })

        return turns

    def get_unique_speakers(self, turns: List[Dict[str, str]]) -> List[str]:
        """Extract sorted list of unique speaker names."""
        speakers = []
        seen = set()
        for t in turns:
            sp = t["speaker"]
            if sp not in seen:
                seen.add(sp)
                speakers.append(sp)
        return speakers

    def synthesize_dialogue(
        self,
        turns: List[Dict[str, str]],
        speaker_voice_map: Dict[str, str], # speaker_name -> voice_id
        project_name: str,
        output_dir: Path,
        model_id: str = "eleven_v3_conversational",
        pause_seconds: float = 0.4,
        progress_callback: Optional[Callable[[int, int, str, Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes each dialogue line with assigned voice and merges with FFmpeg.
        """
        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', project_name).strip('_') or "dialogue"
        project_dir = output_dir / clean_name
        lines_dir = project_dir / "lines"
        lines_dir.mkdir(parents=True, exist_ok=True)

        part_files = []
        total_turns = len(turns)
        total_chars = sum(len(t["text"]) for t in turns)

        # Generate a small silence file for natural conversational pacing
        silence_file = project_dir / "pause.mp3"
        try:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono", "-t", str(pause_seconds), "-q:a", "9", "-acodec", "libmp3lame", str(silence_file)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            silence_file = None

        for idx, turn in enumerate(turns, 1):
            sp = turn["speaker"]
            v_id = speaker_voice_map.get(sp, "cgSgspJ2msm6clMCkdW9") # default Jessica
            line_file = lines_dir / f"line_{idx:03d}_{re.sub(r'[^a-zA-Z0-9]', '_', sp)[:15]}.mp3"

            if progress_callback:
                progress_callback(idx, total_turns, sp, {"status": "synthesizing", "chars": len(turn["text"])})

            res = self.generator.synthesize(
                text=turn["text"],
                voice_id=v_id,
                model_id=model_id,
                output_file=line_file
            )

            if not res.get("success"):
                return {"success": False, "error": f"Failed on Turn {idx} ({sp}): {res.get('error')}"}

            part_files.append(line_file)
            if progress_callback:
                progress_callback(idx, total_turns, sp, {"status": "done", "duration": res.get("duration", 0), "size_kb": res.get("size_kb", 0)})

        # Concatenate dialogue with silence pauses
        master_file = project_dir / f"{clean_name}_dialogue_master.mp3"
        concat_txt = project_dir / "concat_dialogue.txt"

        with open(concat_txt, "w", encoding="utf-8") as f:
            for i, pf in enumerate(part_files):
                f.write(f"file '{pf.resolve()}'\n")
                if silence_file and silence_file.exists() and i < len(part_files) - 1:
                    f.write(f"file '{silence_file.resolve()}'\n")

        try:
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(master_file)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            concat_txt.unlink(missing_ok=True)
            if silence_file and silence_file.exists():
                silence_file.unlink(missing_ok=True)
        except Exception as e:
            return {"success": False, "error": f"Dialogue concatenation failed: {e}", "parts": part_files}

        total_dur = self.generator.get_audio_duration(master_file)
        size_mb = round(master_file.stat().st_size / (1024 * 1024), 2)

        return {
            "success": True,
            "master_file": master_file,
            "project_dir": project_dir,
            "total_turns": total_turns,
            "total_chars": total_chars,
            "total_duration": total_dur,
            "size_mb": size_mb,
            "parts": part_files
        }

# Assign custom voices per speaker tag
