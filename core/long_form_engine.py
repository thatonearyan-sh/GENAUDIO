"""
Long-Form Script Engine for GENAUDIO
Splits large scripts at natural sentence & scene boundaries, synthesizes parts with rotating keys, and merges with ffmpeg.
"""
from __future__ import annotations
import re
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from .generator import AudioGenerator
from .account_manager import AccountManager

class LongFormEngine:
    def __init__(self, generator: AudioGenerator, account_mgr: AccountManager):
        self.generator = generator
        self.account_mgr = account_mgr

    def parse_script_into_scenes(self, script_text: str, max_chunk_chars: int = 1200) -> List[Dict[str, Any]]:
        """
        Parses script text into clean, synthesizable scenes/chunks.
        Detects markdown headers (## Scene 1), or splits by natural paragraphs & sentence boundaries.
        """
        script_text = script_text.strip()
        if not script_text:
            return []

        # Check if structured with markdown headers
        has_headers = bool(re.search(r'^(?:#+|\*\*Scene|\bSection\b)', script_text, re.MULTILINE | re.IGNORECASE))
        raw_sections = []

        if has_headers:
            lines = script_text.splitlines()
            curr_title = "Introduction"
            curr_text = []

            for line in lines:
                header_match = re.match(r'^(?:#{1,4}|\*\*)\s*(.+?)(?:\*\*|:)?\s*$', line.strip())
                if header_match and not line.strip().startswith("["):
                    if curr_text:
                        body = "\n".join(curr_text).strip()
                        if body:
                            raw_sections.append({"title": curr_title, "text": body})
                        curr_text = []
                    curr_title = header_match.group(1).strip("#* :")
                else:
                    curr_text.append(line)

            if curr_text:
                body = "\n".join(curr_text).strip()
                if body:
                    raw_sections.append({"title": curr_title, "text": body})
        else:
            # Split by double newlines into paragraphs
            paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
            for idx, p in enumerate(paragraphs, 1):
                raw_sections.append({"title": f"Part {idx}", "text": p})

        # Further chunk any section exceeding max_chunk_chars at sentence boundaries
        final_chunks = []
        for sec in raw_sections:
            text = sec["text"]
            title = sec["title"]
            
            # Clean out triple backticks or markdown code fences if present
            text = re.sub(r'```(?:markdown)?\n?', '', text)
            text = text.replace('```', '').strip()

            if len(text) <= max_chunk_chars:
                final_chunks.append({
                    "id": f"part_{len(final_chunks) + 1:02d}",
                    "title": title,
                    "text": text
                })
            else:
                # Split by sentence boundaries (. / ! / ? / \n)
                sentences = re.split(r'(?<=[.!?\n])\s+', text)
                buffer = []
                buffer_len = 0
                sub_idx = 1

                for s in sentences:
                    s = s.strip()
                    if not s:
                        continue
                    if buffer_len + len(s) > max_chunk_chars and buffer:
                        chunk_text = " ".join(buffer).strip()
                        final_chunks.append({
                            "id": f"part_{len(final_chunks) + 1:02d}",
                            "title": f"{title} (Part {sub_idx})",
                            "text": chunk_text
                        })
                        buffer = [s]
                        buffer_len = len(s)
                        sub_idx += 1
                    else:
                        buffer.append(s)
                        buffer_len += len(s)

                if buffer:
                    chunk_text = " ".join(buffer).strip()
                    final_chunks.append({
                        "id": f"part_{len(final_chunks) + 1:02d}",
                        "title": f"{title} (Part {sub_idx})" if sub_idx > 1 else title,
                        "text": chunk_text
                    })

        return final_chunks

    def synthesize_long_form(
        self,
        script_text: str,
        project_name: str,
        output_dir: Path,
        voice_id: str = "cgSgspJ2msm6clMCkdW9",
        model_id: str = "eleven_v3_conversational",
        voice_settings: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int, str, Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes full long-form script pipeline:
        1. Parses script into optimal chunks
        2. Synthesizes each chunk with rotating active keys
        3. Losslessly merges all audio chunks into master track via ffmpeg
        """
        clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', project_name).strip('_') or "project"
        project_dir = output_dir / clean_name
        sections_dir = project_dir / "sections"
        sections_dir.mkdir(parents=True, exist_ok=True)

        chunks = self.parse_script_into_scenes(script_text)
        if not chunks:
            return {"success": False, "error": "No valid text chunks found in script."}

        part_files = []
        total_chunks = len(chunks)
        total_chars = sum(len(c["text"]) for c in chunks)

        for idx, chunk in enumerate(chunks):
            out_file = sections_dir / f"{chunk['id']}_{re.sub(r'[^a-zA-Z0-9]', '_', chunk['title'])[:20]}.mp3"
            
            if progress_callback:
                progress_callback(idx + 1, total_chunks, chunk["title"], {"status": "synthesizing", "chars": len(chunk["text"])})

            res = self.generator.synthesize(
                text=chunk["text"],
                voice_id=voice_id,
                model_id=model_id,
                voice_settings=voice_settings,
                output_file=out_file
            )

            if not res.get("success"):
                return {
                    "success": False,
                    "error": f"Failed synthesizing chunk [{chunk['title']}]: {res.get('error')}",
                    "failed_at": idx + 1
                }

            part_files.append(out_file)
            if progress_callback:
                progress_callback(idx + 1, total_chunks, chunk["title"], {"status": "done", "duration": res.get("duration", 0), "size_kb": res.get("size_kb", 0)})

        # Concatenate using ffmpeg
        master_file = project_dir / f"{clean_name}_master.mp3"
        concat_txt = project_dir / "concat_list.txt"

        with open(concat_txt, "w", encoding="utf-8") as f:
            for pf in part_files:
                f.write(f"file '{pf.resolve()}'\n")

        try:
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(master_file)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            concat_txt.unlink(missing_ok=True)
        except Exception as e:
            return {"success": False, "error": f"FFmpeg concatenation failed: {e}", "parts": part_files}

        total_dur = self.generator.get_audio_duration(master_file)
        size_mb = master_file.stat().st_size / (1024 * 1024)

        return {
            "success": True,
            "master_file": master_file,
            "project_dir": project_dir,
            "total_parts": len(part_files),
            "total_chars": total_chars,
            "total_duration": total_dur,
            "size_mb": round(size_mb, 2),
            "parts": part_files
        }

# Markdown scene boundary recognition

# Lossless audio chunk stitching via ffmpeg
