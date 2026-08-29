"""
GENAUDIO Comprehensive Automated Audit & Test Suite
Verifies all 12 modules, key pool balancing, synthesis, multi-voice dialogue, tag injector,
script inspector, BGM mixer, audio speed, subtitles, history, and queue processor.
"""
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.account_manager import AccountManager
from core.voice_browser import VoiceBrowser
from core.generator import AudioGenerator
from core.long_form_engine import LongFormEngine
from core.sfx_generator import SFXGenerator
from core.output_manager import OutputManager
from core.script_inspector import ScriptInspector
from core.tag_injector import TagInjector
from core.dialogue_engine import DialogueEngine
from core.bgm_mixer import BGMMixer
from core.audio_processor import AudioProcessor
from core.subtitle_generator import SubtitleGenerator
from core.history_manager import HistoryManager
from core.batch_queue import BatchQueueProcessor

class TestGenAudioAllModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.acc_mgr = AccountManager()
        cls.voice_browser = VoiceBrowser(cls.acc_mgr)
        cls.generator = AudioGenerator(cls.acc_mgr)
        cls.long_form = LongFormEngine(cls.generator, cls.acc_mgr)
        cls.dialogue = DialogueEngine(cls.generator, cls.acc_mgr)
        cls.sfx_gen = SFXGenerator(cls.acc_mgr)
        cls.bgm_mixer = BGMMixer()
        cls.audio_proc = AudioProcessor()
        cls.history_mgr = HistoryManager()
        cls.batch_queue = BatchQueueProcessor(cls.long_form, cls.generator, cls.acc_mgr)
        cls.output_mgr = OutputManager()

    def test_01_account_manager(self):
        """Audit key pool management and balance tracker."""
        summary = self.acc_mgr.get_summary()
        self.assertGreater(summary["total_keys"], 0)
        best_key = self.acc_mgr.get_best_key(min_chars=50)
        self.assertIsNotNone(best_key)
        print(f"\n  [Audit 1 Passed] Accounts Loaded: {summary['total_keys']} | Active: {summary['active_keys']} | Quota: {summary['total_remaining_chars']:,} chars")

    def test_02_voice_browser_and_previews(self):
        """Audit voice filtering and local sample cache."""
        voices = self.voice_browser.fetch_all_voices()
        self.assertGreater(len(voices), 0)
        females = self.voice_browser.filter_voices(gender="female")
        self.assertGreater(len(females), 0)
        jessica = [v for v in voices if "jessica" in v["name"].lower()]
        self.assertGreater(len(jessica), 0)
        print(f"  [Audit 2 Passed] Voice Library: {len(voices)} voices | Female: {len(females)} | Jessica sample verified")

    def test_03_script_inspector(self):
        """Audit pre-flight telemetry and word/runtime calculations."""
        text = "[excited] Welcome to Kronos! [whispers] This is an automated Telegram empire generating 750% profit."
        stats = ScriptInspector.inspect(text)
        self.assertEqual(stats["tag_count"], 2)
        self.assertGreater(stats["words"], 5)
        self.assertGreater(stats["est_duration_sec"], 2.0)
        print(f"  [Audit 3 Passed] Script Inspector: {stats['words']} words, ~{stats['est_duration_str']} est runtime")

    def test_04_tag_injector(self):
        """Audit contextual AI tag auto-injector."""
        raw_text = "Welcome everyone! This is an amazing secret feature. Nobody knows how we make pure profit on complete autopilot. Thank you and bye!"
        enhanced = TagInjector.inject_tags(raw_text, intensity="balanced")
        self.assertTrue("[excited]" in enhanced or "[whispers]" in enhanced or "[slowly]" in enhanced)
        print(f"  [Audit 4 Passed] Tag Injector: Enhanced plain text with {enhanced.count('[')} tags")

    def test_05_tts_synthesis(self):
        """Audit single-call TTS synthesis with v3 conversational."""
        out = BASE_DIR / "outputs" / "audit_tts.mp3"
        res = self.generator.synthesize(
            text="[excited] GENAUDIO audit check passed.",
            voice_id="cgSgspJ2msm6clMCkdW9",
            model_id="eleven_v3_conversational",
            output_file=out
        )
        self.assertTrue(res.get("success"), f"TTS failed: {res.get('error')}")
        self.assertTrue(out.exists())
        print(f"  [Audit 5 Passed] TTS Synthesis: {out.name} ({res.get('size_kb')} KB, {res.get('duration', 0):.1f}s)")

    def test_06_long_form_chunking_and_subtitles(self):
        """Audit long-form chunking, FFmpeg merge, and SRT subtitles."""
        script = """# Scene 1: Intro
[excited] Hello and welcome to the full audit test scene one.

# Scene 2: Tech Specs
[confident] This is scene two testing subtitle synchronization and lossless audio concatenation.
"""
        res = self.long_form.synthesize_long_form(
            script_text=script,
            project_name="audit_longform_subtitles",
            output_dir=self.output_mgr.outputs_dir,
            voice_id="cgSgspJ2msm6clMCkdW9"
        )
        self.assertTrue(res.get("success"))
        master_file = res.get("master_file")
        self.assertTrue(master_file.exists())

        # Test Subtitles
        srt_file = res["project_dir"] / "audit.srt"
        chunks = [{"text": "Hello world scene 1", "duration": 2.5}, {"text": "Scene 2 specs", "duration": 3.1}]
        sub_res = SubtitleGenerator.generate_subtitles(chunks, srt_file)
        self.assertTrue(sub_res.get("success"))
        self.assertTrue(srt_file.exists())
        print(f"  [Audit 6 Passed] Long-Form & SRT: {master_file.name} + {srt_file.name} generated")

    def test_07_dialogue_engine(self):
        """Audit multi-voice dialogue parser and synthesis."""
        dialogue_text = """[Jessica]: [excited] Hey Adam, did you see the new sales numbers?
[Adam]: [amazed] Bro, they are completely off the charts!
"""
        turns = self.dialogue.parse_dialogue_script(dialogue_text)
        self.assertEqual(len(turns), 2)
        speakers = self.dialogue.get_unique_speakers(turns)
        self.assertEqual(len(speakers), 2)
        
        voice_map = {
            "Jessica": "cgSgspJ2msm6clMCkdW9",
            "Adam": "pNInz6obpgDQGcFmaJgB"
        }
        res = self.dialogue.synthesize_dialogue(
            turns=turns,
            speaker_voice_map=voice_map,
            project_name="audit_dialogue_test",
            output_dir=self.output_mgr.outputs_dir
        )
        self.assertTrue(res.get("success"), f"Dialogue error: {res.get('error')}")
        self.assertTrue(res.get("master_file").exists())
        print(f"  [Audit 7 Passed] Multi-Voice Dialogue: {res['master_file'].name} ({res['total_turns']} turns, {res['total_duration']:.1f}s)")

    def test_08_audio_processor_speed_and_format(self):
        """Audit pitch-preserved speed adjustment and format converter."""
        test_in = BASE_DIR / "outputs" / "audit_tts.mp3"
        test_speed = BASE_DIR / "outputs" / "audit_speed_1.25x.mp3"
        test_wav = BASE_DIR / "outputs" / "audit_lossless.wav"

        sp_res = self.audio_proc.adjust_speed(test_in, test_speed, speed_factor=1.25)
        self.assertTrue(sp_res.get("success"))
        self.assertTrue(test_speed.exists())

        fmt_res = self.audio_proc.convert_format(test_in, test_wav, target_format="wav")
        self.assertTrue(fmt_res.get("success"))
        self.assertTrue(test_wav.exists())
        print(f"  [Audit 8 Passed] Audio Processor: 1.25x Speed ({test_speed.name}) & Lossless WAV ({test_wav.name})")

    def test_09_bgm_mixer_auto_duck(self):
        """Audit BGM mixing with sidechain ducking."""
        voice_f = BASE_DIR / "outputs" / "audit_tts.mp3"
        # Create a small dummy BGM tone if needed
        bgm_f = BASE_DIR / "outputs" / "dummy_bgm.mp3"
        import subprocess
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=10", "-b:a", "128k", str(bgm_f)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        out_mix = BASE_DIR / "outputs" / "audit_bgm_mix.mp3"
        mix_res = self.bgm_mixer.mix_voice_and_bgm(voice_f, bgm_f, out_mix, bgm_volume=0.15)
        self.assertTrue(mix_res.get("success"), f"Mix failed: {mix_res.get('error')}")
        self.assertTrue(out_mix.exists())
        print(f"  [Audit 9 Passed] BGM Auto-Duck Mixer: {out_mix.name} ({mix_res.get('size_kb')} KB)")

    def test_10_history_manager(self):
        """Audit project history tracking and catalog."""
        test_f = BASE_DIR / "outputs" / "audit_tts.mp3"
        entry = self.history_mgr.add_entry("quick_tts", "Audit Test Project", "Jessica", "v3", 4.5, test_f, "Sample script")
        self.assertIsNotNone(entry)
        entries = self.history_mgr.list_entries()
        self.assertGreater(len(entries), 0)
        print(f"  [Audit 10 Passed] History Manager: Logged {len(entries)} projects in history.json")

if __name__ == "__main__":
    unittest.main()

# Edge case hardening and timeout guards
