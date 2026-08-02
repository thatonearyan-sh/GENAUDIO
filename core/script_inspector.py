"""
Script Inspector & Pre-Flight Telemetry for GENAUDIO
Analyzes scripts for character count, word count, estimated runtime, sentence balance, and quota impact.
"""
from __future__ import annotations
import re
from typing import Dict, Any, List

class ScriptInspector:
    @staticmethod
    def inspect(script_text: str, wpm: int = 145) -> Dict[str, Any]:
        """
        Calculates detailed pre-flight telemetry for any script.
        """
        raw_text = script_text.strip()
        if not raw_text:
            return {
                "chars": 0,
                "words": 0,
                "sentences": 0,
                "est_duration_sec": 0.0,
                "est_duration_str": "0s",
                "tag_count": 0,
                "tags_found": [],
                "warnings": ["Script is empty."]
            }

        # Count tags
        tags = re.findall(r'\[[a-zA-Z,\s_-]+\]', raw_text)
        
        # Clean text without tags for accurate word count
        clean_text = re.sub(r'\[[a-zA-Z,\s_-]+\]', '', raw_text)
        clean_text = re.sub(r'[#*`_~]', '', clean_text)
        
        words = re.findall(r'\b\w+\b', clean_text)
        word_count = len(words)
        char_count = len(raw_text)
        
        # Split sentences
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', clean_text) if s.strip()]
        sentence_count = len(sentences)

        # Estimate duration: average 145 words per minute + 0.4s pause per sentence + tag pauses
        base_sec = (word_count / wpm) * 60
        pause_sec = sentence_count * 0.4
        tag_pause_sec = len(tags) * 0.3
        est_sec = base_sec + pause_sec + tag_pause_sec

        mins = int(est_sec // 60)
        secs = int(est_sec % 60)
        dur_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

        # Warnings
        warnings = []
        if char_count > 10000:
            warnings.append(f"Script is {char_count:,} chars; batch auto-chunking will be used.")
        
        long_sentences = [s for s in sentences if len(s.split()) > 35]
        if long_sentences:
            warnings.append(f"{len(long_sentences)} sentences are very long (>35 words); consider breaking them up for better speech pacing.")

        return {
            "chars": char_count,
            "words": word_count,
            "sentences": sentence_count,
            "est_duration_sec": round(est_sec, 1),
            "est_duration_str": dur_str,
            "tag_count": len(tags),
            "tags_found": list(set(tags)),
            "warnings": warnings
        }
