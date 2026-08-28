"""
Project History Manager for GENAUDIO
Catalogs all audio synthesis projects in history.json for auditing, 1-tap playback, and re-generation.
"""
from __future__ import annotations
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

HISTORY_FILE = Path(__file__).resolve().parent / "history.json"

class HistoryManager:
    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or HISTORY_FILE
        self.data: List[Dict[str, Any]] = []
        self.load_history()

    def load_history(self) -> None:
        """Load history from JSON file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = []
        else:
            self.data = []

    def save_history(self) -> None:
        """Save history to JSON file."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def add_entry(
        self,
        project_type: str, # "quick_tts", "long_form", "dialogue", "sfx", "isolated"
        title: str,
        voice_name: str,
        model_id: str,
        duration: float,
        file_path: Path,
        script_snippet: str = ""
    ) -> Dict[str, Any]:
        """Record a completed audio project into history."""
        entry = {
            "id": len(self.data) + 1,
            "type": project_type,
            "title": title,
            "voice": voice_name,
            "model": model_id,
            "duration_sec": round(duration, 1),
            "file_path": str(file_path.resolve()),
            "script_snippet": script_snippet[:150],
            "timestamp": datetime.now().isoformat(),
            "date_str": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.data.insert(0, entry) # Prepend newest
        # Cap at 100 entries
        if len(self.data) > 100:
            self.data = self.data[:100]
        self.save_history()
        return entry

    def list_entries(self, limit: int = 30) -> List[Dict[str, Any]]:
        """List past generation projects."""
        return self.data[:limit]

    def clear_history(self) -> None:
        """Clear all historical logs."""
        self.data = []
        self.save_history()
