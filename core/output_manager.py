"""
Output Manager & Audio Playback Controller for GENAUDIO
Manages generated audio files, real-time playback control, instant stop/kill, Finder reveals, and exports.
"""
from __future__ import annotations
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
DESKTOP_DIR = Path.home() / "Desktop"

class AudioPlayer:
    _current_proc: Optional[subprocess.Popen] = None

    @classmethod
    def play(cls, file_path: Path) -> bool:
        """Play audio file and track process for instant stop/kill."""
        cls.stop()
        if not file_path.exists():
            return False
        try:
            cls._current_proc = subprocess.Popen(
                ["afplay", str(file_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            return False

    @classmethod
    def stop(cls) -> None:
        """Immediately stop and kill all audio playback."""
        if cls._current_proc is not None:
            try:
                cls._current_proc.terminate()
                cls._current_proc.kill()
            except Exception:
                pass
            cls._current_proc = None
        
        # Kill any lingering afplay process to guarantee instant silence
        try:
            subprocess.run(["killall", "-9", "afplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["pkill", "-9", "-f", "afplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    @classmethod
    def is_playing(cls) -> bool:
        """Check if audio is currently playing."""
        if cls._current_proc is None:
            return False
        return cls._current_proc.poll() is None


class OutputManager:
    def __init__(self, outputs_dir: Optional[Path] = None):
        self.outputs_dir = outputs_dir or OUTPUTS_DIR
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.player = AudioPlayer

    def list_outputs(self, limit: int = 30) -> List[Dict[str, Any]]:
        """List all generated master audio files and clips."""
        items = []
        for p in self.outputs_dir.rglob("*.mp3"):
            if not p.is_file():
                continue
            stat = p.stat()
            items.append({
                "path": p,
                "name": p.name,
                "rel_path": p.relative_to(self.outputs_dir),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "mtime": stat.st_mtime,
                "date_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        items.sort(key=lambda x: x["mtime"], reverse=True)
        return items[:limit]

    def play_audio(self, file_path: Path) -> bool:
        """Play audio file via tracked AudioPlayer."""
        return self.player.play(file_path)

    def stop_audio(self) -> None:
        """Stop any playing audio immediately."""
        self.player.stop()

    def reveal_in_finder(self, file_path: Path) -> bool:
        """Reveal file or folder in macOS Finder."""
        try:
            if file_path.is_file():
                subprocess.run(["open", "-R", str(file_path)], check=True)
            else:
                subprocess.run(["open", str(file_path)], check=True)
            return True
        except Exception:
            return False

    def copy_to_desktop(self, file_path: Path) -> Optional[Path]:
        """Copy target audio file to user's Desktop."""
        if not file_path.exists():
            return None
        dest = DESKTOP_DIR / file_path.name
        try:
            shutil.copy2(file_path, dest)
            return dest
        except Exception:
            return None
