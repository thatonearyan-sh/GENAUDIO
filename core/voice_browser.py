"""
Voice Browser & Explorer for GENAUDIO
Fetches, caches, filters, and previews ElevenLabs voices.
"""
from __future__ import annotations
import json
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from .account_manager import AccountManager

CACHE_FILE = Path(__file__).resolve().parent / ".voices_cache.json"

# Popular curated presets for fast access
POPULAR_VOICES = [
    {"id": "cgSgspJ2msm6clMCkdW9", "name": "Jessica", "gender": "female", "accent": "american", "desc": "Playful, Bright, Warm (Best for v3 Conversational)"},
    {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male", "accent": "american", "desc": "Deep, Authoritative, Clear (Best for Narration)"},
    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "gender": "female", "accent": "american", "desc": "Mature, Reassuring, Confident"},
    {"id": "FGY2WhTYpPnrIDTdsKH5", "name": "Laura", "gender": "female", "accent": "american", "desc": "Enthusiast, Quirky, Dynamic"},
    {"id": "XrExE9yKIg1WjnnlVkGX", "name": "Matilda", "gender": "female", "accent": "american", "desc": "Knowledgeable, Professional Educator"},
    {"id": "hpp4J3VqNfWAUOO0d1Us", "name": "Bella", "gender": "female", "accent": "american", "desc": "Warm, Professional, Expressive"},
    {"id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily", "gender": "female", "accent": "british", "desc": "Velvety, Calm, Cinematic"},
    {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male", "accent": "american", "desc": "Well-rounded, Smooth, Storyteller"},
    {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male", "accent": "american", "desc": "Crisp, Energetic, Commercials"}
]

PREVIEWS_DIR = Path(__file__).resolve().parent / "voice_previews"
PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

class VoiceBrowser:
    def __init__(self, account_mgr: AccountManager):
        self.account_mgr = account_mgr
        self.voices: List[Dict[str, Any]] = []
        self.load_cache()

    def load_cache(self) -> None:
        """Load voices from cache if less than 24h old."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if time.time() - data.get("timestamp", 0) < 86400:
                        self.voices = data.get("voices", [])
            except Exception:
                self.voices = []

    def save_cache(self) -> None:
        """Save voices to local cache."""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "voices": self.voices}, f, indent=2)
        except Exception:
            pass

    def fetch_all_voices(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Fetch all available voices from ElevenLabs API."""
        if self.voices and not force_refresh:
            return self.voices

        acc = self.account_mgr.get_best_key()
        if not acc:
            return POPULAR_VOICES

        url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": acc["api_key"]}
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                raw_voices = res.json().get("voices", [])
                parsed = []
                for v in raw_voices:
                    labels = v.get("labels", {})
                    vid = v.get("voice_id")
                    parsed.append({
                        "id": vid,
                        "name": v.get("name"),
                        "gender": labels.get("gender", "unknown").lower(),
                        "accent": labels.get("accent", "unknown").lower(),
                        "age": labels.get("age", "unknown").lower(),
                        "use_case": labels.get("use_case", "general").lower(),
                        "desc": labels.get("description") or v.get("category", "premade"),
                        "preview_url": v.get("preview_url")
                    })
                self.voices = parsed
                self.save_cache()
                return self.voices
        except Exception:
            pass

        return POPULAR_VOICES

    def filter_voices(
        self,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filter voices by gender, accent, or keyword search."""
        all_v = self.fetch_all_voices()
        results = []
        for v in all_v:
            if gender and gender.lower() != "all" and v.get("gender") != gender.lower():
                continue
            if accent and accent.lower() != "all" and accent.lower() not in v.get("accent", ""):
                continue
            if search_query:
                q = search_query.lower()
                matches = (
                    q in v.get("name", "").lower() or
                    q in v.get("desc", "").lower() or
                    q in v.get("accent", "").lower() or
                    q in v.get("use_case", "").lower()
                )
                if not matches:
                    continue
            results.append(v)
        return results

    def play_preview(self, voice: Dict[str, Any]) -> bool:
        """Play voice preview audio via AudioPlayer with instant stop and local caching."""
        vid = voice.get("id")
        if not vid:
            return False

        from .output_manager import AudioPlayer
        local_file = PREVIEWS_DIR / f"{vid}.mp3"
        
        # 1. Check local cache first (0ms instant playback)
        if local_file.exists() and local_file.stat().st_size > 1000:
            return AudioPlayer.play(local_file)

        # 2. Download from preview_url if missing locally
        preview_url = voice.get("preview_url")
        if preview_url:
            try:
                res = requests.get(preview_url, timeout=6)
                if res.status_code == 200:
                    with open(local_file, "wb") as f:
                        f.write(res.content)
                    return AudioPlayer.play(local_file)
            except Exception:
                pass

        return False

# Filter voices by gender, accent, age
