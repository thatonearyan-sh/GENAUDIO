"""
Batch Folder Synthesizer & Queue Processor for GENAUDIO
Scans a folder for all .txt/.md script files and processes them in a continuous batch queue.
"""
from __future__ import annotations
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from .long_form_engine import LongFormEngine
from .generator import AudioGenerator
from .account_manager import AccountManager

class BatchQueueProcessor:
    def __init__(self, long_form: LongFormEngine, generator: AudioGenerator, account_mgr: AccountManager):
        self.long_form = long_form
        self.generator = generator
        self.account_mgr = account_mgr

    def scan_folder(self, folder_path: Path) -> List[Path]:
        """Scan directory for script files."""
        if not folder_path.exists() or not folder_path.is_dir():
            return []
        files = list(folder_path.glob("*.md")) + list(folder_path.glob("*.txt"))
        files.sort()
        return files

    def process_queue(
        self,
        script_files: List[Path],
        output_dir: Path,
        voice_id: str = "cgSgspJ2msm6clMCkdW9",
        model_id: str = "eleven_v3_conversational",
        voice_settings: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int, str, Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Processes a queue of multiple script files sequentially.
        """
        batch_id = f"batch_{int(time.time())}"
        batch_dir = output_dir / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        results = []
        total_files = len(script_files)

        for idx, file_path in enumerate(script_files, 1):
            if progress_callback:
                progress_callback(idx, total_files, file_path.name, {"status": "starting"})

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                res = self.long_form.synthesize_long_form(
                    script_text=content,
                    project_name=file_path.stem,
                    output_dir=batch_dir,
                    voice_id=voice_id,
                    model_id=model_id,
                    voice_settings=voice_settings
                )

                if res.get("success"):
                    results.append({"file": file_path.name, "success": True, "output": res.get("master_file"), "duration": res.get("total_duration")})
                    if progress_callback:
                        progress_callback(idx, total_files, file_path.name, {"status": "done", "duration": res.get("total_duration")})
                else:
                    results.append({"file": file_path.name, "success": False, "error": res.get("error")})
                    if progress_callback:
                        progress_callback(idx, total_files, file_path.name, {"status": "failed", "error": res.get("error")})
            except Exception as e:
                results.append({"file": file_path.name, "success": False, "error": str(e)})

        successful = sum(1 for r in results if r["success"])
        return {
            "success": successful > 0,
            "batch_id": batch_id,
            "batch_dir": batch_dir,
            "total_files": total_files,
            "successful_files": successful,
            "failed_files": total_files - successful,
            "results": results
        }
