"""
Sound Effects (SFX) Generator for GENAUDIO
Generates cinematic ambient sounds, foley, whooshes, and extended soundscapes via ElevenLabs Sound Generation API
with multi-key automatic failover, load balancing, and FFmpeg seamless extended crossfade looper (up to 10+ minutes).
"""
from __future__ import annotations
import math
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from .account_manager import AccountManager

class SFXGenerator:
    def __init__(self, account_mgr: AccountManager):
        self.account_mgr = account_mgr

    def generate_sfx(
        self,
        prompt: str,
        duration_seconds: Optional[float] = None,
        prompt_influence: float = 0.3,
        output_file: Optional[Path] = None,
        max_retries: int = 10
    ) -> Dict[str, Any]:
        """
        Generate sound effect from text prompt with automatic failover key balancing.
        Supports extended durations (e.g. 60s, 120s, 300s) via seamless FFmpeg looping.
        """
        prompt = prompt.strip()
        if not prompt:
            return {"success": False, "error": "Empty prompt provided."}

        target_dur = float(duration_seconds or 4.0)
        # ElevenLabs max raw API limit is 22.0s
        api_duration = min(target_dur, 20.0) if target_dur > 22.0 else max(target_dur, 0.5)

        out_path = output_file or (Path("/tmp") / f"sfx_{int(time.time())}.mp3")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Temp raw file if we need to extend
        raw_temp_file = out_path.parent / f"raw_base_{out_path.name}" if target_dur > 22.0 else out_path

        url = "https://api.elevenlabs.io/v1/sound-generation"
        payload: Dict[str, Any] = {
            "text": prompt,
            "duration_seconds": api_duration,
            "prompt_influence": prompt_influence
        }

        tried_keys = set()
        last_error = "Unknown error"

        for attempt in range(max_retries):
            # Pick best active key
            acc = self.account_mgr.get_best_key(min_chars=len(prompt))
            if not acc or acc["api_key"] in tried_keys:
                available = [
                    a for a in self.account_mgr.data["accounts"]
                    if a["api_key"] not in tried_keys and a.get("status") in ("active", "unverified")
                ]
                if not available:
                    return {"success": False, "error": f"All active API keys failed. Last error: {last_error}"}
                acc = available[0]

            api_key = acc["api_key"]
            tried_keys.add(api_key)

            headers = {
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            }

            try:
                res = requests.post(url, json=payload, headers=headers, timeout=60)
                if res.status_code == 200:
                    with open(raw_temp_file, "wb") as f:
                        f.write(res.content)
                    
                    self.account_mgr.record_usage(api_key, len(prompt))

                    # If extended duration was requested, seamlessly loop with FFmpeg
                    if target_dur > 22.0:
                        self.extend_audio_loop(raw_temp_file, target_dur, out_path)
                        raw_temp_file.unlink(missing_ok=True)

                    kb = out_path.stat().st_size // 1024
                    return {
                        "success": True,
                        "file": out_path,
                        "size_kb": kb,
                        "prompt": prompt,
                        "duration": target_dur,
                        "key_used": acc.get("name", "Key"),
                        "was_extended": target_dur > 22.0
                    }
                elif res.status_code in (401, 429):
                    last_error = f"HTTP {res.status_code}: {res.text}"
                    self.account_mgr.mark_key_failed(api_key, reason=f"HTTP_{res.status_code}")
                    time.sleep(0.5)
                else:
                    last_error = f"HTTP {res.status_code}: {res.text}"
                    time.sleep(0.5)
            except Exception as e:
                last_error = str(e)
                time.sleep(1)

        return {"success": False, "error": f"Failed after {max_retries} attempts: {last_error}"}

    @staticmethod
    def extend_audio_loop(input_path: Path, target_duration: float, output_path: Path) -> bool:
        """
        Seamlessly loops audio with fade-out up to target_duration (e.g. 60s, 120s, 300s).
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fade_dur = min(2.0, target_duration / 5.0)
        fade_start = max(0.0, target_duration - fade_dur)

        filter_str = f"[0:a]aloop=loop=-1:size=2e+09,atrim=0:{target_duration},afade=t=out:st={fade_start:.1f}:d={fade_dur:.1f}[out]"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-filter_complex", filter_str,
            "-map", "[out]",
            "-ac", "2",
            "-b:a", "192k",
            str(output_path)
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False
