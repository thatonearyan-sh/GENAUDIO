"""
Audio Generator Engine for GENAUDIO
Handles single-call Text-to-Speech synthesis, model routing, voice presets, and auto-failover key balancing.
"""
from __future__ import annotations
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Union
import requests
from .account_manager import AccountManager

SUPPORTED_MODELS = [
    {"id": "eleven_v3_conversational", "name": "Eleven v3 Conversational", "desc": "Latest v3 with full expressive emotion & pacing tags [whispers, gasps, excited]"},
    {"id": "eleven_v3", "name": "Eleven v3 Standard", "desc": "High-fidelity expressive v3 audio model"},
    {"id": "eleven_multilingual_v2", "name": "Eleven Multilingual v2", "desc": "Industry-standard multilingual stability (English, Hindi, etc.)"},
    {"id": "eleven_turbo_v2_5", "name": "Eleven Turbo v2.5", "desc": "Ultra low-latency high-speed model (32 languages)"},
    {"id": "eleven_flash_v2_5", "name": "Eleven Flash v2.5", "desc": "Lightweight, fastest rendering engine"}
]

VOICE_PRESETS = {
    "expressive": {
        "name": "🎭 Ultra-Expressive / Dramatic",
        "desc": "High dynamic range, maximizes [whispers, gasps, laughs, shouts] tags",
        "settings": {"stability": 0.35, "similarity_boost": 0.80, "style": 0.30, "use_speaker_boost": True}
    },
    "conversational": {
        "name": "🎙️ Natural Conversational",
        "desc": "Balanced tone for walkthroughs, tutorials, and casual chat",
        "settings": {"stability": 0.48, "similarity_boost": 0.80, "style": 0.15, "use_speaker_boost": True}
    },
    "narration": {
        "name": "📻 Audiobook / Documentary",
        "desc": "Calm, consistent, and highly articulate delivery",
        "settings": {"stability": 0.65, "similarity_boost": 0.85, "style": 0.05, "use_speaker_boost": True}
    },
    "asmr": {
        "name": "🤫 ASMR / Intimate Whisper",
        "desc": "Soft, breathy, close-mic effect",
        "settings": {"stability": 0.30, "similarity_boost": 0.75, "style": 0.40, "use_speaker_boost": True}
    }
}

class AudioGenerator:
    def __init__(self, account_mgr: AccountManager):
        self.account_mgr = account_mgr

    def get_audio_duration(self, file_path: Path) -> float:
        """Probe audio duration in seconds using ffprobe."""
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return float(res.stdout.strip())
        except Exception:
            return 0.0

    def synthesize(
        self,
        text: str,
        voice_id: str = "cgSgspJ2msm6clMCkdW9",
        model_id: str = "eleven_v3_conversational",
        voice_settings: Optional[Dict[str, Any]] = None,
        output_file: Optional[Path] = None,
        max_retries: int = 10
    ) -> Dict[str, Any]:
        """
        Synthesize text to speech with automatic failover key balancing.
        """
        text = text.strip()
        if not text:
            return {"success": False, "error": "Empty text provided."}

        settings = voice_settings or VOICE_PRESETS["expressive"]["settings"]
        out_path = output_file or (Path("/tmp") / f"genaudio_{int(time.time())}.mp3")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        chars_len = len(text)
        tried_keys = set()
        last_error = "Unknown error"

        for attempt in range(max_retries):
            # Pick best active key
            acc = self.account_mgr.get_best_key(min_chars=chars_len)
            if not acc or acc["api_key"] in tried_keys:
                # Fallback to any remaining active key not yet tried
                available = [a for a in self.account_mgr.data["accounts"] if a["api_key"] not in tried_keys and a.get("status") in ("active", "unverified")]
                if not available:
                    return {"success": False, "error": "All active API keys in the pool have been exhausted or rate limited."}
                acc = available[0]

            api_key = acc["api_key"]
            tried_keys.add(api_key)

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }
            payload = {
                "text": text,
                "model_id": model_id,
                "voice_settings": settings
            }

            try:
                res = requests.post(url, json=payload, headers=headers, timeout=90)
                if res.status_code == 200:
                    with open(out_path, "wb") as f:
                        f.write(res.content)
                    
                    dur = self.get_audio_duration(out_path)
                    kb = out_path.stat().st_size // 1024
                    self.account_mgr.record_usage(api_key, chars_len)

                    return {
                        "success": True,
                        "file": out_path,
                        "duration": dur,
                        "size_kb": kb,
                        "chars": chars_len,
                        "key_used": acc.get("name", "Key"),
                        "key_id": acc["id"]
                    }
                elif res.status_code in (401, 429):
                    last_error = f"HTTP {res.status_code}: {res.text}"
                    self.account_mgr.mark_key_failed(api_key, reason=f"HTTP_{res.status_code}")
                    time.sleep(1)
                else:
                    last_error = f"HTTP {res.status_code}: {res.text}"
                    time.sleep(1)
            except Exception as e:
                last_error = str(e)
                time.sleep(2)

        return {"success": False, "error": f"Failed after {max_retries} attempts: {last_error}"}

# Stream chunking implementation

# Exponential retry backoff on 5xx
