"""
AI Expressive Tag Auto-Injector for GENAUDIO
Contextually analyzes plain text scripts and injects ElevenLabs v3 emotional & pacing tags.
"""
from __future__ import annotations
import re

EXCITED_KEYWORDS = {"insane", "amazing", "crazy", "unbelievable", "boom", "welcome", "huge", "shandar", "zabardast", "less go", "lets go", "super", "fire"}
WHISPER_KEYWORDS = {"secret", "sunno", "sunna", "listen closely", "quietly", "nobody knows", "chupke", "khufiya", "secretly"}
GASP_KEYWORDS = {"shocking", "wait", "hold on", "omg", "wtff", "zara socho", "can you believe", "impossible"}
PROUD_KEYWORDS = {"best", "guarantee", "perfect", "masterpiece", "crown jewel", "beast", "empire", "institutional-grade", "enterprise"}
SARCASM_KEYWORDS = {"baaki bots", "dusre bots", "manual", "amateur", "try karo", "boring", "obviously"}
SLOW_KEYWORDS = {"percent", "%", "crore", "lakh", "rupees", "milliseconds", "pure profit", "autopilot"}
OUTRO_KEYWORDS = {"thanks", "thank you", "bye", "byeee", "see you", "milte hain", "next video"}

class TagInjector:
    @staticmethod
    def inject_tags(script_text: str, intensity: str = "balanced") -> str:
        """
        Contextually injects expressive tags into a raw script.
        Intensity: 'subtle', 'balanced', 'dramatic'
        """
        lines = script_text.splitlines()
        processed_lines = []

        for line in lines:
            trimmed = line.strip()
            # If line is header or already has tags, preserve as-is
            if not trimmed or trimmed.startswith("#") or trimmed.startswith("**"):
                processed_lines.append(line)
                continue

            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', trimmed)
            tagged_sentences = []

            for idx, sentence in enumerate(sentences):
                s_lower = sentence.lower()
                
                # Skip if already tagged
                if re.match(r'^\s*\[[a-zA-Z,\s_-]+\]', sentence):
                    tagged_sentences.append(sentence)
                    continue

                tags_to_add = []

                # Rule 1: Whispers / Secrets
                if any(k in s_lower for k in WHISPER_KEYWORDS):
                    tags_to_add.append("[whispers]")
                # Rule 2: Gasps / Shock
                elif any(k in s_lower for k in GASP_KEYWORDS):
                    tags_to_add.append("[gasps]")
                # Rule 3: Sarcasm / Jabs
                elif any(k in s_lower for k in SARCASM_KEYWORDS):
                    tags_to_add.append("[sarcastically]")
                # Rule 4: Excited / Hype
                elif any(k in s_lower for k in EXCITED_KEYWORDS) or sentence.endswith("!"):
                    tags_to_add.append("[excited]")
                # Rule 5: Proud / Confident
                elif any(k in s_lower for k in PROUD_KEYWORDS):
                    tags_to_add.append("[proud]")
                # Rule 6: Slow stats
                elif any(k in s_lower for k in SLOW_KEYWORDS):
                    tags_to_add.append("[slowly]")
                # Rule 7: Outro / Thanks
                elif any(k in s_lower for k in OUTRO_KEYWORDS):
                    tags_to_add.append("[delighted]")
                else:
                    if intensity == "dramatic" and idx % 2 == 0:
                        tags_to_add.append("[confident]")

                if tags_to_add:
                    tag_str = " ".join(tags_to_add)
                    tagged_sentences.append(f"{tag_str} {sentence}")
                else:
                    tagged_sentences.append(sentence)

            processed_lines.append(" ".join(tagged_sentences))

        return "\n".join(processed_lines)

# Conversational v3 expression tags
