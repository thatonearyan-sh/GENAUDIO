"""
ElevenLabs Voice Isolator & Noise Remover for GENAUDIO
Removes background noise, room echo, and unwanted ambient sounds using ElevenLabs Audio Isolation API.
"""
from __future__ import annotations
import time
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from .account_manager import AccountManager

class VoiceIsolator:
    def __init__(self, account_mgr: AccountManager):
        self.account_mgr = account_mgr

    def isolate_voice(
        self,
        input_audio: Path,
        output_file: Optional[Path] = None,
        max_retries: int = 5
    ) -> Dict[str, Any]:
        """
        Isolates vocal audio from background noise.
        """
        if not input_audio.exists():
            return {"success": False, "error": f"Audio file not found: {input_audio}"}

        out_path = output_file or (input_audio.parent / f"{input_audio.stem}_isolated.mp3")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        url = "https://api.elevenlabs.io/v1/audio-isolation"
        tried_keys = set()
        last_error = "Unknown error"

        for attempt in range(max_retries):
            acc = self.account_mgr.get_best_key(min_chars=100)
            if not acc or acc["api_key"] in tried_keys:
                available = [
                    a for a in self.account_mgr.data["accounts"]
                    if a["api_key"] not in tried_keys and a.get("status") in ("active", "unverified")
                ]
                if not available:
                    return {"success": False, "error": f"All active keys exhausted. Last error: {last_error}"}
                acc = available[0]

            api_key = acc["api_key"]
            tried_keys.add(api_key)

            headers = {"xi-api-key": api_key}

            try:
                with open(input_audio, "rb") as audio_file:
                    files = {"audio": (input_audio.name, audio_file, "audio/mpeg")}
                    res = requests.post(url, headers=headers, files=files, timeout=90)

                if res.status_code == 200:
                    with open(out_path, "wb") as f:
                        f.write(res.content)
                    
                    kb = out_path.stat().st_size // 1024
                    return {
                        "success": True,
                        "file": out_path,
                        "size_kb": kb,
                        "key_used": acc.get("name", "Key")
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

        return {"success": False, "error": f"Voice isolation failed: {last_error}"}
