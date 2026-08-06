#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║               👑 GENAUDIO — ElevenLabs Command Center 👑             ║
║      Multi-Account Pool · Voice Studio · Long-Form Script Merger     ║
╚══════════════════════════════════════════════════════════════════════╝
"""
from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure package path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.align import Align
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

from core.account_manager import AccountManager
from core.voice_browser import VoiceBrowser, POPULAR_VOICES
from core.generator import AudioGenerator, SUPPORTED_MODELS, VOICE_PRESETS
from core.long_form_engine import LongFormEngine
from core.sfx_generator import SFXGenerator
from core.output_manager import OutputManager
from core.script_inspector import ScriptInspector
from core.tag_injector import TagInjector
from core.dialogue_engine import DialogueEngine
from core.bgm_mixer import BGMMixer
from core.audio_processor import AudioProcessor
from core.voice_isolator import VoiceIsolator
from core.stem_separator import StemSeparator
from core.subtitle_generator import SubtitleGenerator
from core.history_manager import HistoryManager
from core.batch_queue import BatchQueueProcessor

console = Console()

BANNER_ART = """[bold cyan]
  ██████╗ ███████╗███╗   ██╗ █████╗ ██╗   ██╗██████╗ ██╗ ██████╗ 
 ██╔════╝ ██╔════╝████╗  ██║██╔══██╗██║   ██║██╔══██╗██║██╔═══██╗
 ██║  ███╗█████╗  ██╔██╗ ██║███████║██║   ██║██║  ██║██║██║   ██║
 ██║   ██║██╔══╝  ██║╚██╗██║██╔══██║██║   ██║██║  ██║██║██║   ██║
 ╚██████╔╝███████╗██║ ╚████║██║  ██║╚██████╔╝██████╔╝██║╚██████╔╝
  ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝ [/bold cyan]
           [bold yellow]⚡ ElevenLabs Enterprise Interactive Audio Studio ⚡[/bold yellow]
"""

TAG_OPTIONS = [
    ("[excited]", "High excitement & energy"),
    ("[whispers]", "Soft intimate whisper"),
    ("[gasps]", "Shock / sharp intake of breath"),
    ("[shouts]", "Loud intense shout"),
    ("[amazed]", "Astonished, mind-blown tone"),
    ("[proud]", "Confident, boasting delivery"),
    ("[delighted]", "Warm, happy tone"),
    ("[slowly]", "Deliberate slow dramatic pacing"),
    ("[urgently]", "Fast pressing tone / FOMO"),
    ("[nervously]", "Tense, building suspense"),
    ("[laughs]", "Natural light laugh"),
    ("[sighs]", "Relieved exhale"),
    ("[sarcastically]", "Witty sarcastic delivery")
]

class GenAudioApp:
    def __init__(self):
        self.account_mgr = AccountManager()
        self.voice_browser = VoiceBrowser(self.account_mgr)
        self.generator = AudioGenerator(self.account_mgr)
        self.long_form = LongFormEngine(self.generator, self.account_mgr)
        self.dialogue = DialogueEngine(self.generator, self.account_mgr)
        self.sfx_gen = SFXGenerator(self.account_mgr)
        self.isolator = VoiceIsolator(self.account_mgr)
        self.stem_sep = StemSeparator(self.account_mgr)
        self.bgm_mixer = BGMMixer()
        self.audio_proc = AudioProcessor()
        self.history_mgr = HistoryManager()
        self.batch_queue = BatchQueueProcessor(self.long_form, self.generator, self.account_mgr)
        self.output_mgr = OutputManager()
        self.scripts_dir = BASE_DIR / "scripts"
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

    def print_header(self, subtitle: str = "") -> None:
        """Render standard branded header with live account telemetry and stop any playing audio."""
        self.output_mgr.stop_audio()
        console.clear()
        console.print(BANNER_ART)
        
        summary = self.account_mgr.get_summary()
        telemetry = (
            f"[bold green]🔑 Active Keys:[/bold green] {summary['active_keys']}/{summary['total_keys']}  |  "
            f"[bold yellow]📊 Remaining Pool:[/bold yellow] {summary['total_remaining_chars']:,} chars  |  "
            f"[bold magenta]📁 Outputs:[/bold magenta] GENAUDIO/outputs"
        )
        console.print(Panel(Align.center(telemetry), border_style="dim blue", padding=(0, 1)))
        
        if subtitle:
            console.print(f"\n[bold underline white]▶ {subtitle}[/bold underline white]\n")

    def run(self) -> None:
        """Master Application Event Loop."""
        while True:
            self.print_header()
            
            action = inquirer.select(
                message="Select an action to proceed:",
                choices=[
                    Choice(value="quick_tts", name="🎙️  1. Quick Text-to-Speech (Instant Generation)"),
                    Choice(value="long_form", name="📜  2. Long-Form Script Studio (Auto-Chunk, SRT & Merge)"),
                    Choice(value="dialogue", name="👥  3. Multi-Voice Dialogue & Podcast Studio"),
                    Choice(value="tag_injector", name="🪄  4. AI Expressive Tag Auto-Injector (Polish Raw Text)"),
                    Choice(value="sfx", name="🔊  5. Sound Effects (SFX) Generator"),
                    Choice(value="voice_isolator", name="🧼  6. VOCALCLEAN — Studio Voice Isolator & Noise Remover"),
                    Choice(value="bgm_mixer", name="🎶  7. Background Music (BGM) Auto-Duck Mixer"),
                    Choice(value="audio_tools", name="🎚️   8. Audio Speed & Multi-Format Converter (WAV/FLAC/MP3)"),
                    Choice(value="batch_queue", name="📦  9. Batch Folder Synthesizer (Queue Mode)"),
                    Choice(value="voice_browser", name="🎭 10. Voice Explorer & 5-Sec Audio Previews"),
                    Choice(value="accounts", name="🔑 11. API Key Pool & Account Health Manager"),
                    Choice(value="history", name="🗃️  12. Project History & Re-Generator"),
                    Choice(value="outputs", name="📂 13. Output Gallery & Audio Player"),
                    Choice(value="tag_helper", name="🏷️  14. Audio Expression Tag Cheat Sheet"),
                    Separator(),
                    Choice(value="exit", name="🚪 15. Exit GENAUDIO")
                ],
                default="quick_tts",
                pointer="👉"
            ).execute()

            if action == "quick_tts":
                self.handle_quick_tts()
            elif action == "long_form":
                self.handle_long_form()
            elif action == "dialogue":
                self.handle_dialogue()
            elif action == "tag_injector":
                self.handle_tag_injector()
            elif action == "sfx":
                self.handle_sfx()
            elif action == "voice_isolator":
                self.handle_voice_isolator()
            elif action == "bgm_mixer":
                self.handle_bgm_mixer()
            elif action == "audio_tools":
                self.handle_audio_tools()
            elif action == "batch_queue":
                self.handle_batch_queue()
            elif action == "voice_browser":
                self.handle_voice_browser()
            elif action == "accounts":
                self.handle_accounts()
            elif action == "history":
                self.handle_history()
            elif action == "outputs":
                self.handle_outputs()
            elif action == "tag_helper":
                self.handle_tag_helper()
            elif action == "exit":
                console.print("\n[bold cyan]Thank you for using GENAUDIO! Have a great day! 👋[/bold cyan]\n")
                sys.exit(0)

    # ─── 1. QUICK TTS (STEP-BY-STEP WIZARD WITH BACK/DONE) ───────────────────
    def handle_quick_tts(self) -> None:
        step = 1
        text = ""
        voice_choice = None
        model_choice = "eleven_v3_conversational"
        preset_choice = VOICE_PRESETS["expressive"]
        file_name = f"quick_tts_{int(time.time())}.mp3"

        while step > 0:
            if step == 1:
                self.print_header("Quick Text-to-Speech (Step 1/5: Enter Text)")
                if text:
                    console.print(f"[bold cyan]Current Text:[/bold cyan] [dim]{text[:120]}...[/dim]\n")
                
                txt_input = inquirer.text(
                    message="Enter or paste text to synthesize ([excited], [whispers] tags supported) [or type ':cancel']:",
                    default=text
                ).execute()

                if txt_input.strip() == ":cancel":
                    return
                if not txt_input.strip():
                    console.print("[red]Text cannot be empty.[/red]")
                    time.sleep(1)
                    continue

                text = txt_input.strip()
                step = 2

            elif step == 2:
                self.print_header("Quick Text-to-Speech (Step 2/5: Select Voice)")
                voice_res = self.select_voice_flow()
                if voice_res == "__BACK__":
                    step = 1
                    continue
                if not voice_res:
                    return
                voice_choice = voice_res
                step = 3

            elif step == 3:
                self.print_header("Quick Text-to-Speech (Step 3/5: Select AI Model)")
                model_res = self.select_model_flow(allow_back=True)
                if model_res == "__BACK__":
                    step = 2
                    continue
                model_choice = model_res
                step = 4

            elif step == 4:
                self.print_header("Quick Text-to-Speech (Step 4/5: Select Performance Preset)")
                preset_res = self.select_preset_flow(allow_back=True)
                if preset_res == "__BACK__":
                    step = 3
                    continue
                preset_choice = preset_res
                step = 5

            elif step == 5:
                self.print_header("Quick Text-to-Speech (Step 5/5: Review & Generate)")
                # Pre-flight inspection
                stats = ScriptInspector.inspect(text)
                console.print(Panel(
                    f"[bold white]📝 Text:[/bold white] {text[:150]}... ({stats['chars']} chars, {stats['words']} words)\n"
                    f"[bold white]⏱️  Est Duration:[/bold white] ~{stats['est_duration_str']}\n"
                    f"[bold white]🎙️  Voice:[/bold white] {voice_choice['name']} ({voice_choice.get('gender')}, {voice_choice.get('accent')})\n"
                    f"[bold white]🤖 Model:[/bold white] {model_choice}\n"
                    f"[bold white]🎭 Preset:[/bold white] {preset_choice['name']}",
                    border_style="cyan",
                    title="Pre-Flight Generation Review"
                ))

                confirm_action = inquirer.select(
                    message="Choose action to proceed:",
                    choices=[
                        Choice(value="done", name="✅ 1. Done & Start Synthesizing Now"),
                        Choice(value="back", name="🔙 2. Back (Go 1 Step Back to Change Preset)"),
                        Choice(value="cancel", name="❌ 3. Cancel (Return to Main Menu)")
                    ],
                    default="done"
                ).execute()

                if confirm_action == "back":
                    step = 4
                    continue
                elif confirm_action == "cancel":
                    return
                
                out_path = self.output_mgr.outputs_dir / file_name
                console.print("\n[bold yellow]⚡ Synthesizing with ElevenLabs...[/bold yellow]")
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                    progress.add_task("Connecting to ElevenLabs API...", total=None)
                    res = self.generator.synthesize(
                        text=text,
                        voice_id=voice_choice["id"],
                        model_id=model_choice,
                        voice_settings=preset_choice["settings"],
                        output_file=out_path
                    )

                if res.get("success"):
                    dur = res.get("duration", 0)
                    console.print(f"\n[bold green]✅ Audio Generated Successfully![/bold green]")
                    console.print(Panel(
                        f"[bold white]📁 File:[/bold white] {out_path}\n"
                        f"[bold white]⏱️  Duration:[/bold white] {dur:.1f} seconds\n"
                        f"[bold white]📊 File Size:[/bold white] {res.get('size_kb', 0)} KB\n"
                        f"[bold white]🔑 Key Used:[/bold white] {res.get('key_used')}",
                        border_style="green",
                        title="Generation Summary"
                    ))
                    
                    # Record history
                    self.history_mgr.add_entry("quick_tts", file_name, voice_choice["name"], model_choice, dur, out_path, text)
                    self.post_audio_actions(out_path)
                    return
                else:
                    console.print(f"\n[bold red]❌ Synthesis Failed:[/bold red] {res.get('error')}")
                    Prompt.ask("\nPress Enter to return to main menu")
                    return

    # ─── 2. LONG-FORM SCRIPT STUDIO ──────────────────────────────────────────
    def handle_long_form(self) -> None:
        step = 1
        script_text = ""
        project_name = f"longform_{int(time.time())}"
        voice_choice = None
        model_choice = "eleven_v3_conversational"
        preset_choice = VOICE_PRESETS["expressive"]

        while step > 0:
            if step == 1:
                self.print_header("Long-Form Studio (Step 1/5: Select Script Source)")
                script_source = inquirer.select(
                    message="Choose script source:",
                    choices=[
                        Choice(value="vault", name="📁 1. Browse Script Vault (GENAUDIO/scripts/ folder)"),
                        Choice(value="file_path", name="📂 2. Enter File Path / Drag & Drop (.txt, .md)"),
                        Choice(value="paste", name="📋 3. Paste Script Directly in Terminal"),
                        Separator(),
                        Choice(value="back", name="🔙 Cancel / Return to Main Menu")
                    ]
                ).execute()

                if script_source == "back":
                    return

                if script_source == "vault":
                    files = list(self.scripts_dir.glob("*.md")) + list(self.scripts_dir.glob("*.txt"))
                    if not files:
                        console.print(f"\n[yellow]No scripts found in {self.scripts_dir}. Place .txt or .md files there![/yellow]")
                        Prompt.ask("Press Enter to continue")
                        continue
                    
                    f_choices = [Choice(value=f, name=f"{f.name} ({f.stat().st_size // 1024} KB)") for f in files] + [Separator(), Choice(value="__BACK__", name="🔙 Back to Source Selection")]
                    f_choice = inquirer.select(message="Select script from vault:", choices=f_choices).execute()
                    if f_choice == "__BACK__":
                        continue
                    
                    project_name = f_choice.stem
                    with open(f_choice, "r", encoding="utf-8") as f:
                        script_text = f.read()

                elif script_source == "file_path":
                    f_path_str = inquirer.text(
                        message="Enter full path or drag & drop file here (or type ':back'):",
                    ).execute()
                    if f_path_str.strip() == ":back":
                        continue
                    f_path = Path(f_path_str.strip("'\" "))
                    if not f_path.exists():
                        console.print("[red]File does not exist.[/red]")
                        time.sleep(1)
                        continue
                    project_name = f_path.stem
                    with open(f_path, "r", encoding="utf-8") as f:
                        script_text = f.read()

                elif script_source == "paste":
                    console.print("[cyan]Paste your script below. Press Enter, type 'END', and press Enter to finish (or 'CANCEL'):[/cyan]")
                    lines = []
                    while True:
                        line = input()
                        if line.strip() == "END":
                            break
                        if line.strip() == "CANCEL":
                            lines = []
                            break
                        lines.append(line)
                    if not lines:
                        continue
                    script_text = "\n".join(lines)
                    project_name = inquirer.text(message="Enter project name:", default="my_custom_script").execute()

                if not script_text.strip():
                    console.print("[red]Script is empty.[/red]")
                    time.sleep(1)
                    continue

                step = 2

            elif step == 2:
                self.print_header("Long-Form Studio (Step 2/5: Select Voice)")
                voice_res = self.select_voice_flow()
                if voice_res == "__BACK__":
                    step = 1
                    continue
                if not voice_res:
                    return
                voice_choice = voice_res
                step = 3

            elif step == 3:
                self.print_header("Long-Form Studio (Step 3/5: Select AI Model)")
                model_res = self.select_model_flow(allow_back=True)
                if model_res == "__BACK__":
                    step = 2
                    continue
                model_choice = model_res
                step = 4

            elif step == 4:
                self.print_header("Long-Form Studio (Step 4/5: Select Performance Preset)")
                preset_res = self.select_preset_flow(allow_back=True)
                if preset_res == "__BACK__":
                    step = 3
                    continue
                preset_choice = preset_res
                step = 5

            elif step == 5:
                self.print_header("Long-Form Studio (Step 5/5: Script Breakdown & Done)")
                chunks = self.long_form.parse_script_into_scenes(script_text)
                stats = ScriptInspector.inspect(script_text)
                
                console.print(Panel(
                    f"[bold white]📁 Project Name:[/bold white] {project_name}\n"
                    f"[bold white]📝 Length:[/bold white] {stats['chars']:,} chars ({stats['words']:,} words)\n"
                    f"[bold white]⏱️  Est Runtime:[/bold white] ~{stats['est_duration_str']}\n"
                    f"[bold white]🧩 Scene Chunks:[/bold white] {len(chunks)} parts (split at sentence boundaries)\n"
                    f"[bold white]🎙️  Voice:[/bold white] {voice_choice['name']} ({voice_choice.get('gender')})\n"
                    f"[bold white]🤖 Model:[/bold white] {model_choice}\n"
                    f"[bold white]🎭 Preset:[/bold white] {preset_choice['name']}",
                    border_style="cyan",
                    title="Long-Form Project Review"
                ))

                confirm_action = inquirer.select(
                    message="Confirm long-form execution:",
                    choices=[
                        Choice(value="done", name="✅ 1. Done & Start Batch Synthesis with Auto-Merge"),
                        Choice(value="back", name="🔙 2. Back (Go 1 Step Back to Change Preset)"),
                        Choice(value="cancel", name="❌ 3. Cancel (Return to Main Menu)")
                    ],
                    default="done"
                ).execute()

                if confirm_action == "back":
                    step = 4
                    continue
                elif confirm_action == "cancel":
                    return

                console.print(f"\n[bold yellow]🚀 Starting Batch Synthesis across {len(chunks)} sections...[/bold yellow]\n")
                
                def progress_cb(curr: int, total: int, title: str, meta: Dict[str, Any]):
                    status = meta.get("status")
                    if status == "synthesizing":
                        console.print(f"[{curr}/{total}] 🎙️ Synthesizing: [bold white]{title}[/bold white] ({meta.get('chars')} chars)...")
                    elif status == "done":
                        console.print(f"   ✅ Part {curr} Complete ({meta.get('size_kb')} KB)")

                res = self.long_form.synthesize_long_form(
                    script_text=script_text,
                    project_name=project_name,
                    output_dir=self.output_mgr.outputs_dir,
                    voice_id=voice_choice["id"],
                    model_id=model_choice,
                    voice_settings=preset_choice["settings"],
                    progress_callback=progress_cb
                )

                if res.get("success"):
                    master_file = res["master_file"]
                    dur = res["total_duration"]
                    mins = int(dur // 60)
                    secs = int(dur % 60)

                    # Auto-generate Subtitles (.SRT and .VTT)
                    srt_file = res["project_dir"] / f"{project_name}.srt"
                    chunk_meta = []
                    for c, pf in zip(chunks, res["parts"]):
                        chunk_dur = self.generator.get_audio_duration(pf)
                        chunk_meta.append({"text": c["text"], "duration": chunk_dur})
                    SubtitleGenerator.generate_subtitles(chunk_meta, srt_file)

                    console.print(f"\n[bold green]🎉 LONG-FORM MASTER AUDIO COMPLETE![/bold green]")
                    console.print(Panel(
                        f"[bold white]📁 Master Audio File:[/bold white] {master_file}\n"
                        f"[bold white]📄 Subtitles (.SRT / .VTT):[/bold white] {srt_file}\n"
                        f"[bold white]📂 Parts Directory:[/bold white] {res['project_dir']}/sections\n"
                        f"[bold white]⏱️  Total Duration:[/bold white] {mins}m {secs:02d}s ({dur:.1f}s)\n"
                        f"[bold white]📊 Master Size:[/bold white] {res['size_mb']} MB\n"
                        f"[bold white]🧩 Total Parts Merged:[/bold white] {res['total_parts']}",
                        border_style="green",
                        title="Master Project Summary"
                    ))
                    
                    self.history_mgr.add_entry("long_form", project_name, voice_choice["name"], model_choice, dur, master_file, script_text)
                    self.post_audio_actions(master_file)
                    return
                else:
                    console.print(f"\n[bold red]❌ Batch Synthesis Error:[/bold red] {res.get('error')}")
                    Prompt.ask("\nPress Enter to return to main menu")
                    return

    # ─── 3. MULTI-VOICE DIALOGUE & PODCAST STUDIO ────────────────────────────
    def handle_dialogue(self) -> None:
        self.print_header("Multi-Voice Dialogue & Podcast Studio")
        console.print("[cyan]Format your script with character tags, for example:[/cyan]")
        console.print("[yellow][Jessica]: Hey Adam, what are the new numbers?\n[Adam]: [excited] We hit 750% profit margin today![/yellow]\n")

        script_text = inquirer.text(
            message="Paste or enter multi-speaker script (or type ':demo' to load a demo conversation):",
            validate=lambda x: len(x.strip()) > 0 or "Script cannot be empty."
        ).execute()

        if script_text.strip() == ":demo":
            script_text = (
                "[Jessica]: [excited] Hey everyone! Welcome to the brand new GENAUDIO podcast studio.\n"
                "[Adam]: [confident] That's right! Today we are discussing automated multi-voice synthesis.\n"
                "[Jessica]: [amazed] It automatically assigns different voices to different speakers and stitches them seamlessly!\n"
                "[Adam]: [proud] Absolute game changer for content creators!"
            )

        turns = self.dialogue.parse_dialogue_script(script_text)
        speakers = self.dialogue.get_unique_speakers(turns)

        if len(speakers) < 2:
            console.print("[yellow]Detected only 1 speaker. For standard scripts, use Quick TTS or Long-Form studio.[/yellow]")

        console.print(f"\n[bold cyan]Detected Speakers ({len(speakers)}):[/bold cyan] {', '.join(speakers)}\n")

        # Assign voice to each speaker
        speaker_voice_map = {}
        for sp in speakers:
            console.print(f"[bold white]Assign voice for character: [{sp}][/bold white]")
            v_obj = self.select_voice_flow()
            if not v_obj or v_obj == "__BACK__":
                v_obj = POPULAR_VOICES[0]
            speaker_voice_map[sp] = v_obj["id"]

        p_name = inquirer.text(message="Enter project name:", default="dialogue_project").execute()
        
        console.print(f"\n[bold yellow]🚀 Synthesizing multi-character dialogue across {len(turns)} turns...[/bold yellow]\n")
        
        def progress_cb(curr: int, total: int, speaker: str, meta: Dict[str, Any]):
            status = meta.get("status")
            if status == "synthesizing":
                console.print(f"[{curr}/{total}] 🎙️ Line for [bold white]{speaker}[/bold white] ({meta.get('chars')} chars)...")

        res = self.dialogue.synthesize_dialogue(
            turns=turns,
            speaker_voice_map=speaker_voice_map,
            project_name=p_name,
            output_dir=self.output_mgr.outputs_dir,
            progress_callback=progress_cb
        )

        if res.get("success"):
            master_file = res["master_file"]
            dur = res["total_duration"]
            console.print(f"\n[bold green]🎉 Dialogue Podcast Master Complete![/bold green]")
            console.print(Panel(
                f"[bold white]📁 File:[/bold white] {master_file}\n"
                f"[bold white]⏱️  Duration:[/bold white] {dur:.1f}s\n"
                f"[bold white]👥 Speakers:[/bold white] {len(speakers)} ({', '.join(speakers)})",
                border_style="green",
                title="Dialogue Summary"
            ))
            self.history_mgr.add_entry("dialogue", p_name, f"{len(speakers)} voices", "v3", dur, master_file, script_text)
            self.post_audio_actions(master_file)
        else:
            console.print(f"[red]Dialogue Synthesis Error: {res.get('error')}[/red]")
            Prompt.ask("Press Enter to return")

    # ─── 4. TAG AUTO-INJECTOR ────────────────────────────────────────────────
    def handle_tag_injector(self) -> None:
        self.print_header("AI Expressive Tag Auto-Injector (Polish Raw Text)")
        
        raw_text = inquirer.text(
            message="Paste raw plain-text script to automatically enhance with emotion tags:",
            validate=lambda x: len(x.strip()) > 0 or "Text cannot be empty."
        ).execute()

        intensity = inquirer.select(
            message="Select tag intensity:",
            choices=[
                Choice(value="subtle", name="🌿 Subtle (Few essential tags)"),
                Choice(value="balanced", name="⚖️  Balanced (Natural conversational pacing)"),
                Choice(value="dramatic", name="🎭 Dramatic (High energy, frequent expressions)")
            ],
            default="balanced"
        ).execute()

        enhanced = TagInjector.inject_tags(raw_text, intensity=intensity)

        console.print("\n[bold green]✨ Enhanced Script with Auto-Injected Tags:[/bold green]\n")
        console.print(Panel(enhanced, border_style="yellow", title="Enhanced Script Preview"))

        act = inquirer.select(
            message="What would you like to do with this enhanced script?",
            choices=[
                Choice(value="synthesize", name="🎙️  1. Synthesize Audio with this Enhanced Script Now"),
                Choice(value="save_vault", name="💾 2. Save to scripts/ Vault"),
                Choice(value="back", name="🔙 3. Back to Main Menu")
            ]
        ).execute()

        if act == "synthesize":
            # Pass directly to quick TTS
            v = self.select_voice_flow()
            if v and v != "__BACK__":
                out_path = self.output_mgr.outputs_dir / f"enhanced_{int(time.time())}.mp3"
                res = self.generator.synthesize(text=enhanced, voice_id=v["id"], output_file=out_path)
                if res.get("success"):
                    self.post_audio_actions(out_path)
        elif act == "save_vault":
            s_name = inquirer.text(message="Enter filename (e.g. enhanced_script.md):", default="enhanced_script.md").execute()
            if not s_name.endswith(".md"):
                s_name += ".md"
            with open(self.scripts_dir / s_name, "w", encoding="utf-8") as f:
                f.write(enhanced)
            console.print(f"[green]Saved to {self.scripts_dir / s_name}![/green]")
            Prompt.ask("Press Enter to continue")

    # ─── 5. SOUND EFFECTS (SFX) ──────────────────────────────────────────────
    def handle_sfx(self) -> None:
        step = 1
        prompt = ""
        dur = 4.0

        while step > 0:
            if step == 1:
                self.print_header("Sound Effects Generator (Step 1/3: Prompt)")
                p_in = inquirer.text(
                    message="Enter sound effect prompt (e.g. 'cinematic explosion with sub bass', 'laser blast') [or ':cancel']:",
                    default=prompt
                ).execute()
                if p_in.strip() == ":cancel":
                    return
                if not p_in.strip():
                    console.print("[red]Prompt cannot be empty.[/red]")
                    continue
                prompt = p_in.strip()
                step = 2

            elif step == 2:
                self.print_header("Sound Effects Generator (Step 2/3: Duration)")
                console.print("[dim cyan]💡 Durations > 22s will automatically use the Seamless Ambience Looper (up to 10 mins).[/dim cyan]\n")
                d_in = inquirer.number(
                    message="Enter duration in seconds (0.5 to 600.0) [e.g. 10s, 60s (1 min), 120s (2 min)]:",
                    default=dur,
                    min_allowed=0.5,
                    max_allowed=600.0,
                    float_allowed=True
                ).execute()
                dur = float(d_in)
                step = 3

            elif step == 3:
                self.print_header("Sound Effects Generator (Step 3/3: Review & Done)")
                ext_str = " (⚡ Seamless Ambience Looper)" if dur > 22.0 else ""
                console.print(Panel(
                    f"[bold white]🔊 Sound Prompt:[/bold white] {prompt}\n"
                    f"[bold white]⏱️  Duration:[/bold white] {dur} seconds{ext_str}",
                    border_style="cyan",
                    title="SFX Review"
                ))

                act = inquirer.select(
                    message="Proceed with generation?",
                    choices=[
                        Choice(value="done", name="✅ 1. Done & Generate Sound Effect"),
                        Choice(value="back", name="🔙 2. Back (Go 1 Step Back to Change Duration)"),
                        Choice(value="cancel", name="❌ 3. Cancel (Return to Main Menu)")
                    ],
                    default="done"
                ).execute()

                if act == "back":
                    step = 2
                    continue
                elif act == "cancel":
                    return

                out_name = f"sfx_{int(time.time())}.mp3"
                out_file = self.output_mgr.outputs_dir / out_name

                console.print("\n[bold yellow]⚡ Generating Sound Effect via ElevenLabs...[/bold yellow]")
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                    progress.add_task("Rendering SFX audio...", total=None)
                    res = self.sfx_gen.generate_sfx(prompt=prompt, duration_seconds=dur, output_file=out_file)

                if res.get("success"):
                    console.print(f"\n[bold green]✅ Sound Effect Generated![/bold green]")
                    console.print(f"📁 Saved to: {out_file} ({res.get('size_kb')} KB)")
                    self.history_mgr.add_entry("sfx", prompt, "SFX", "sound-gen", dur, out_file, prompt)
                    self.post_audio_actions(out_file)
                    return
                else:
                    console.print(f"\n[bold red]❌ SFX Error:[/bold red] {res.get('error')}")
                    Prompt.ask("\nPress Enter to return")
                    return

    # ─── 6. VOCALCLEAN STEM SEPARATOR & ISOLATOR ────────────────────────────
    def handle_voice_isolator(self) -> None:
        import shutil
        while True:
            self.print_header("VOCALCLEAN — Studio AI Stem & Vocal Separator")
            
            clean_act = inquirer.select(
                message="Select VOCALCLEAN mode:",
                choices=[
                    Choice(value="demo", name="🎧 1. Test with Built-in Demo Audio Track (Full 4-Stem Preview)"),
                    Choice(value="stems", name="🎼 2. Separate Audio into 4 Stems (Vocals, Drums, Bass, Instruments, Karaoke)"),
                    Choice(value="isolate", name="🧼 3. AI Voice Isolator & Speech Noise Remover (ElevenLabs)"),
                    Separator(),
                    Choice(value="back", name="🔙 Back to Main Menu")
                ]
            ).execute()

            if clean_act == "back":
                break

            if clean_act == "demo":
                demo_path = BASE_DIR / "core" / "demo_stem_track.mp3"
                if not demo_path.exists():
                    console.print("[red]Demo track not found.[/red]")
                    Prompt.ask("Press Enter")
                    continue
                self.process_stem_separation(demo_path, "demo_stem_project")

            elif clean_act == "stems":
                audio_path_str = inquirer.text(
                    message="Enter full path to song / audio file (or type ':back'):",
                ).execute()
                if audio_path_str.strip() == ":back":
                    continue
                audio_path = Path(audio_path_str.strip("'\" "))
                if not audio_path.exists():
                    console.print("[red]Audio file not found.[/red]")
                    time.sleep(1)
                    continue
                self.process_stem_separation(audio_path, audio_path.stem)

            elif clean_act == "isolate":
                audio_path_str = inquirer.text(
                    message="Enter full path to noisy voice recording to clean (or type ':back'):",
                ).execute()
                if audio_path_str.strip() == ":back":
                    continue
                audio_path = Path(audio_path_str.strip("'\" "))
                if not audio_path.exists():
                    console.print("[red]Audio file not found.[/red]")
                    time.sleep(1)
                    continue
                out_file = self.output_mgr.outputs_dir / f"{audio_path.stem}_isolated.mp3"
                console.print("\n[bold yellow]⚡ Isolating vocals and removing noise via ElevenLabs API...[/bold yellow]")
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                    progress.add_task("Cleaning audio track...", total=None)
                    res = self.isolator.isolate_voice(audio_path, out_file)
                if res.get("success"):
                    console.print(f"\n[bold green]✅ Voice Isolation Complete![/bold green]")
                    self.post_audio_actions(out_file)
                else:
                    console.print(f"\n[bold red]❌ Error: {res.get('error')}[/bold red]")
                    Prompt.ask("Press Enter to return")

    def process_stem_separation(self, audio_path: Path, project_name: str) -> None:
        import shutil
        console.print(f"\n[bold yellow]⚡ Separating stems for [{audio_path.name}] into dedicated project folder...[/bold yellow]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Splitting Vocals, Drums, Bass, and Instruments...", total=None)
            def progress_cb(msg):
                progress.update(task, description=msg)
            res = self.stem_sep.separate_stems(audio_path, self.output_mgr.outputs_dir, project_name=project_name, progress_callback=progress_cb)

        if res.get("success"):
            target_dir = res["project_dir"]
            console.print(f"\n[bold green]🎉 Stem Separation Complete![/bold green]")
            console.print(f"📁 Destination Folder: [bold cyan]{target_dir}[/bold cyan]\n")

            while True:
                table = Table(title=f"VOCALCLEAN Stems — {project_name}", border_style="cyan")
                table.add_column("#", style="dim")
                table.add_column("Stem Name", style="bold white")
                table.add_column("File Name", style="cyan")
                table.add_column("Size", justify="right", style="yellow")

                stems_list = [
                    ("🎤 Isolated Vocals", res.get("vocals")),
                    ("🎼 Instrumental (Karaoke / No Vocals)", res.get("instrumental")),
                    ("🥁 Drums & Percussion Beats", res.get("drums")),
                    ("🎸 Bass & Sub-Bass", res.get("bass")),
                    ("🎹 Other Instruments (Synths/Keys)", res.get("other")),
                ]

                valid_stems = []
                for idx, (label, stem_file) in enumerate(stems_list, 1):
                    if stem_file and Path(stem_file).exists():
                        sz_kb = Path(stem_file).stat().st_size // 1024
                        table.add_row(str(idx), label, Path(stem_file).name, f"{sz_kb} KB")
                        valid_stems.append((label, Path(stem_file)))

                console.print(table)

                choices = [
                    Choice(value=f, name=f"▶️  Play {lbl}") for lbl, f in valid_stems
                ] + [
                    Separator(),
                    Choice(value="stop", name="⏹️  Stop Audio Playback"),
                    Choice(value="finder", name="📂 Open Stems Folder in Finder"),
                    Choice(value="desktop", name="🖥️  Copy Entire Stems Folder to Desktop"),
                    Separator(),
                    Choice(value="back", name="🔙 Done / Return to Menu")
                ]

                stem_act = inquirer.select(message="Select action for separated stems:", choices=choices).execute()
                if stem_act == "back":
                    self.output_mgr.stop_audio()
                    break
                elif stem_act == "stop":
                    self.output_mgr.stop_audio()
                    console.print("[yellow]⏹️ Audio stopped.[/yellow]")
                elif stem_act == "finder":
                    self.output_mgr.reveal_in_finder(target_dir)
                elif stem_act == "desktop":
                    dest = Path.home() / "Desktop" / target_dir.name
                    shutil.copytree(target_dir, dest, dirs_exist_ok=True)
                    console.print(f"[green]✅ Copied entire stems folder to {dest}![/green]")
                else:
                    console.print(f"[cyan]▶ Playing {Path(stem_act).name}...[/cyan]")
                    self.output_mgr.play_audio(Path(stem_act))
        else:
            console.print(f"\n[bold red]❌ Stem Separation Error: {res.get('error')}[/bold red]")
            Prompt.ask("Press Enter to continue")

    # ─── 7. BGM AUTO-DUCK MIXER ──────────────────────────────────────────────
    def handle_bgm_mixer(self) -> None:
        self.print_header("Background Music (BGM) Auto-Duck Audio Mixer")
        
        # Pick Voice Audio
        voice_str = inquirer.text(
            message="Enter path to voiceover audio file (or pick from outputs/):",
            validate=lambda x: Path(x.strip("'\" ")).exists() or "Voice file not found."
        ).execute()
        voice_file = Path(voice_str.strip("'\" "))

        # Pick BGM
        bgm_str = inquirer.text(
            message="Enter path to background music (.mp3/.wav):",
            validate=lambda x: Path(x.strip("'\" ")).exists() or "BGM file not found."
        ).execute()
        bgm_file = Path(bgm_str.strip("'\" "))

        bgm_vol = inquirer.number(
            message="Enter background music volume (0.05 to 0.40, recommended 0.15):",
            default=0.15,
            min_allowed=0.01,
            max_allowed=1.0,
            float_allowed=True
        ).execute()

        out_file = self.output_mgr.outputs_dir / f"{voice_file.stem}_with_bgm.mp3"

        console.print("\n[bold yellow]⚡ Mixing voiceover with sidechain auto-ducking via FFmpeg...[/bold yellow]")
        res = self.bgm_mixer.mix_voice_and_bgm(voice_file, bgm_file, out_file, bgm_volume=float(bgm_vol))

        if res.get("success"):
            console.print(f"\n[bold green]✅ Mixed with Auto-Ducking Successfully![/bold green]")
            console.print(f"📁 Master Mixed File: {out_file} ({res.get('size_kb')} KB)")
            self.post_audio_actions(out_file)
        else:
            console.print(f"\n[bold red]❌ Mixer Error:[/bold red] {res.get('error')}")
            Prompt.ask("\nPress Enter to return")

    # ─── 8. AUDIO SPEED & MULTI-FORMAT CONVERTER ─────────────────────────────
    def handle_audio_tools(self) -> None:
        self.print_header("Audio Tools: Speed (Tempo) & Multi-Format Converter")
        
        audio_str = inquirer.text(
            message="Enter path to audio file:",
            validate=lambda x: Path(x.strip("'\" ")).exists() or "File not found."
        ).execute()
        audio_file = Path(audio_str.strip("'\" "))

        tool_act = inquirer.select(
            message="Choose audio transformation:",
            choices=[
                Choice(value="speed", name="🏎️  1. Adjust Speed / Tempo (Pitch-Preserved atempo)"),
                Choice(value="convert", name="🔄 2. Convert Audio Format (WAV, FLAC, M4A, MP3 320k)"),
                Choice(value="normalize", name="📢 3. Normalize Loudness (EBU R128 Broadcast Standard)"),
                Separator(),
                Choice(value="back", name="🔙 Back to Main Menu")
            ]
        ).execute()

        if tool_act == "back":
            return

        if tool_act == "speed":
            sp_factor = inquirer.select(
                message="Select playback speed factor:",
                choices=[
                    Choice(value=0.85, name="0.85x (Slightly Slower)"),
                    Choice(value=1.10, name="1.10x (Gentle Boost)"),
                    Choice(value=1.15, name="1.15x (Crisp & Energetic - Recommended for Reels/Shorts)"),
                    Choice(value=1.25, name="1.25x (Fast Pace)"),
                    Choice(value=1.50, name="1.50x (Ultra Fast)")
                ],
                default=1.15
            ).execute()
            out_file = self.output_mgr.outputs_dir / f"{audio_file.stem}_{sp_factor}x.mp3"
            res = self.audio_proc.adjust_speed(audio_file, out_file, speed_factor=float(sp_factor))

        elif tool_act == "convert":
            fmt = inquirer.select(
                message="Select target export format:",
                choices=[
                    Choice(value="wav", name="WAV (Lossless Studio Master 44.1kHz)"),
                    Choice(value="flac", name="FLAC (Lossless Compressed)"),
                    Choice(value="mp3", name="MP3 (320kbps High-Quality)"),
                    Choice(value="m4a", name="M4A / AAC (Apple Compatible)")
                ],
                default="wav"
            ).execute()
            out_file = self.output_mgr.outputs_dir / f"{audio_file.stem}.{fmt}"
            res = self.audio_proc.convert_format(audio_file, out_file, target_format=fmt)

        elif tool_act == "normalize":
            out_file = self.output_mgr.outputs_dir / f"{audio_file.stem}_normalized.mp3"
            res = self.audio_proc.normalize_loudness(audio_file, out_file)

        if res.get("success"):
            console.print(f"\n[bold green]✅ Audio Processed Successfully![/bold green]")
            console.print(f"📁 Output: {out_file} ({res.get('size_kb')} KB)")
            self.post_audio_actions(out_file)
        else:
            console.print(f"\n[bold red]❌ Error:[/bold red] {res.get('error')}")
            Prompt.ask("\nPress Enter to return")

    # ─── 9. BATCH QUEUE PROCESSOR ────────────────────────────────────────────
    def handle_batch_queue(self) -> None:
        self.print_header("Batch Folder Synthesizer (Queue Mode)")
        
        folder_str = inquirer.text(
            message="Enter path to folder containing script files (.txt/.md):",
            default=str(self.scripts_dir)
        ).execute()
        folder_path = Path(folder_str.strip("'\" "))

        files = self.batch_queue.scan_folder(folder_path)
        if not files:
            console.print(f"[yellow]No .txt or .md files found in {folder_path}[/yellow]")
            Prompt.ask("Press Enter to return")
            return

        console.print(f"\n[bold cyan]Found {len(files)} scripts to process:[/bold cyan]")
        for f in files:
            console.print(f"• {f.name} ({f.stat().st_size} bytes)")

        voice_res = self.select_voice_flow()
        if not voice_res or voice_res == "__BACK__":
            return

        if not Confirm.ask(f"\nStart sequential batch queue for all {len(files)} files?", default=True):
            return

        console.print("\n[bold yellow]🚀 Processing Batch Queue...[/bold yellow]\n")
        
        def progress_cb(curr: int, total: int, filename: str, meta: Dict[str, Any]):
            status = meta.get("status")
            if status == "starting":
                console.print(f"[{curr}/{total}] ⏳ Processing: [bold white]{filename}[/bold white]...")
            elif status == "done":
                console.print(f"   ✅ Finished ({meta.get('duration', 0):.1f}s)")
            elif status == "failed":
                console.print(f"   ❌ Failed: {meta.get('error')}")

        res = self.batch_queue.process_queue(
            script_files=files,
            output_dir=self.output_mgr.outputs_dir,
            voice_id=voice_res["id"],
            progress_callback=progress_cb
        )

        console.print(f"\n[bold green]🎉 Batch Queue Completed![/bold green]")
        console.print(f"Successful: {res['successful_files']}/{res['total_files']} | Destination: {res['batch_dir']}")
        Prompt.ask("Press Enter to continue")

    # ─── 10. VOICE EXPLORER ──────────────────────────────────────────────────
    def handle_voice_browser(self) -> None:
        while True:
            self.print_header("Voice Explorer & Library")
            
            filter_action = inquirer.select(
                message="Choose voice view mode:",
                choices=[
                    Choice(value="popular", name="⭐ 1. Curated Popular Voices (Fast Access)"),
                    Choice(value="female", name="👩 2. Filter Female Voices"),
                    Choice(value="male", name="👨 3. Filter Male Voices"),
                    Choice(value="search", name="🔍 4. Search Voices by Name / Keyword"),
                    Choice(value="all", name="🌐 5. Browse All ElevenLabs Voices"),
                    Separator(),
                    Choice(value="back", name="🔙 Back to Main Menu")
                ]
            ).execute()

            if filter_action == "back":
                break

            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                progress.add_task("Fetching voice metadata...", total=None)
                if filter_action == "popular":
                    voices = POPULAR_VOICES
                elif filter_action == "female":
                    voices = self.voice_browser.filter_voices(gender="female")
                elif filter_action == "male":
                    voices = self.voice_browser.filter_voices(gender="male")
                elif filter_action == "search":
                    q = inquirer.text(message="Enter search keyword (e.g. 'warm', 'british', 'jessica'):").execute()
                    voices = self.voice_browser.filter_voices(search_query=q)
                else:
                    voices = self.voice_browser.fetch_all_voices()

            if not voices:
                console.print("[yellow]No voices matched your filter.[/yellow]")
                Prompt.ask("Press Enter to continue")
                continue

            table = Table(title=f"ElevenLabs Voices ({len(voices)} found)", border_style="cyan", box=None)
            table.add_column("#", style="dim")
            table.add_column("Name", style="bold white")
            table.add_column("Gender", style="magenta")
            table.add_column("Accent", style="cyan")
            table.add_column("Description / Tags", style="dim white")

            for idx, v in enumerate(voices[:25], 1):
                table.add_row(str(idx), v["name"], v.get("gender", "?"), v.get("accent", "?"), v.get("desc", ""))

            console.print(table)

            while True:
                v_choice = inquirer.select(
                    message="Select a voice to listen to audio demo:",
                    choices=[Choice(value=v, name=f"🎧 {v['name']} ({v.get('gender')}, {v.get('accent')})") for v in voices[:30]] + [
                        Separator(),
                        Choice(value="__DONE__", name="✅ Done (Return to Voice Categories)"),
                        Choice(value="__BACK__", name="🔙 Back to Main Menu")
                    ]
                ).execute()

                if v_choice == "__DONE__":
                    break
                elif v_choice == "__BACK__":
                    return
                else:
                    console.print(f"[bold yellow]▶ Playing instant sample for {v_choice['name']}... (macOS afplay)[/bold yellow]")
                    self.voice_browser.play_preview(v_choice)
                    time.sleep(1)

    # ─── 11. ACCOUNTS & KEY POOL ─────────────────────────────────────────────
    def handle_accounts(self) -> None:
        while True:
            self.print_header("API Key & Account Pool Manager")
            
            action = inquirer.select(
                message="Account Manager Options:",
                choices=[
                    Choice(value="health_check", name="🩺 1. Run Live Health Check on All Keys"),
                    Choice(value="list", name="📋 2. View Current Account Pool Table"),
                    Choice(value="add", name="➕ 3. Add New ElevenLabs API Key"),
                    Choice(value="delete", name="🗑️  4. Delete an API Key"),
                    Choice(value="sync", name="🔄 5. Auto-Sync / Re-Import Keys from Secrets Vault"),
                    Separator(),
                    Choice(value="back", name="🔙 Back to Main Menu")
                ]
            ).execute()

            if action == "back":
                break

            elif action == "health_check":
                console.print("\n[bold yellow]🩺 Checking live subscription quota for all keys...[/bold yellow]")
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                    progress.add_task("Querying ElevenLabs API...", total=None)
                    self.account_mgr.check_all_health()
                self.render_accounts_table()
                Prompt.ask("\nPress Enter to continue")

            elif action == "list":
                self.render_accounts_table()
                Prompt.ask("\nPress Enter to continue")

            elif action == "add":
                new_key = inquirer.text(
                    message="Enter ElevenLabs API Key (sk_...):",
                    validate=lambda x: x.startswith("sk_") or "Key must start with sk_"
                ).execute()
                new_name = inquirer.text(message="Enter nickname for this account (optional):").execute()
                
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                    progress.add_task("Verifying key with ElevenLabs...", total=None)
                    res = self.account_mgr.add_key(new_key, new_name)

                if res.get("success"):
                    console.print(f"\n[bold green]✅ Added key successfully![/bold green]")
                else:
                    console.print(f"\n[bold red]❌ {res.get('message')}[/bold red]")
                Prompt.ask("Press Enter to continue")

            elif action == "delete":
                accs = self.account_mgr.data["accounts"]
                if not accs:
                    console.print("[yellow]No accounts to delete.[/yellow]")
                    Prompt.ask("Press Enter")
                    continue
                
                del_choice = inquirer.select(
                    message="Select account to delete:",
                    choices=[Choice(value=a["id"], name=f"#{a['id']} - {a['name']} ({a['api_key'][:8]}...)") for a in accs] + [Separator(), Choice(value=None, name="🔙 Cancel / Back")]
                ).execute()

                if del_choice:
                    if Confirm.ask("Are you sure you want to delete this key?", default=False):
                        self.account_mgr.remove_key(del_choice)
                        console.print("[green]Key deleted.[/green]")
                        Prompt.ask("Press Enter")

            elif action == "sync":
                count = self.account_mgr.auto_import_from_secrets()
                console.print(f"\n[bold green]✅ Imported {count} new keys from secrets vault![/bold green]")
                Prompt.ask("Press Enter")

    def render_accounts_table(self) -> None:
        table = Table(title="ElevenLabs Key Pool Health & Character Balances", border_style="cyan")
        table.add_column("ID", justify="center", style="bold")
        table.add_column("Nickname", style="white")
        table.add_column("Masked Key", style="dim")
        table.add_column("Tier", style="magenta")
        table.add_column("Remaining Chars", justify="right", style="bold yellow")
        table.add_column("Status", justify="center")

        for a in self.account_mgr.data["accounts"]:
            st = a.get("status", "unverified")
            if st == "active":
                status_str = "[bold green]ACTIVE 🟢[/bold green]"
                rem = f"{a.get('character_remaining', 0):,}"
            elif st == "depleted":
                status_str = "[bold red]EXHAUSTED 🔴[/bold red]"
                rem = f"{a.get('character_remaining', 0):,}"
            elif st in ("locked", "invalid"):
                status_str = "[bold magenta]LOCKED (401) 🔒[/bold magenta]"
                rem = "[dim]0 (blocked)[/dim]"
            elif st == "rate_limited":
                status_str = "[bold yellow]COOLDOWN (429) ⏳[/bold yellow]"
                rem = f"{a.get('character_remaining', 0):,}"
            else:
                status_str = "[yellow]UNCHECKED ⏳[/yellow]"
                rem = f"{a.get('character_remaining', 0):,}"

            masked = f"{a['api_key'][:8]}...{a['api_key'][-4:]}"
            table.add_row(str(a["id"]), a.get("name", ""), masked, a.get("tier", "unknown"), rem, status_str)

        console.print("\n", table)

    # ─── 12. PROJECT HISTORY ─────────────────────────────────────────────────
    def handle_history(self) -> None:
        self.print_header("Project History & Catalog")
        
        entries = self.history_mgr.list_entries(limit=30)
        if not entries:
            console.print("[yellow]No historical generation projects recorded yet.[/yellow]")
            Prompt.ask("Press Enter to return")
            return

        table = Table(title="Past Generation Projects", border_style="cyan")
        table.add_column("#", style="dim")
        table.add_column("Title / Project", style="bold white")
        table.add_column("Type", style="magenta")
        table.add_column("Voice", style="cyan")
        table.add_column("Duration", justify="right", style="yellow")
        table.add_column("Date", style="dim")

        for idx, e in enumerate(entries, 1):
            table.add_row(str(idx), e["title"], e["type"], e.get("voice", "-"), f"{e.get('duration_sec', 0)}s", e.get("date_str", ""))

        console.print(table)

        choices = [Choice(value=e, name=f"{e['title']} ({e['type']}) - {e['date_str']}") for e in entries] + [Separator(), Choice(value=None, name="🔙 Back to Main Menu")]
        selected = inquirer.select(message="Select project to inspect or play:", choices=choices).execute()

        if selected:
            p_file = Path(selected["file_path"])
            if p_file.exists():
                self.post_audio_actions(p_file)
            else:
                console.print("[red]Audio file no longer exists at original path.[/red]")
                Prompt.ask("Press Enter to continue")

    # ─── 13. OUTPUT GALLERY ──────────────────────────────────────────────────
    def handle_outputs(self) -> None:
        while True:
            self.print_header("Output Gallery & Audio Manager")
            
            items = self.output_mgr.list_outputs(limit=25)
            if not items:
                console.print("[yellow]No audio files generated yet.[/yellow]")
                Prompt.ask("Press Enter to return")
                return

            choices = []
            for it in items:
                choices.append(Choice(value=it["path"], name=f"{it['name']} ({it['size_mb']} MB) - {it['date_str']}"))
            choices.append(Separator())
            choices.append(Choice(value="open_dir", name="📂 Open Output Folder in Finder"))
            choices.append(Choice(value="back", name="🔙 Back to Main Menu"))

            selected = inquirer.select(
                message="Select an audio file:",
                choices=choices
            ).execute()

            if selected == "back":
                break
            elif selected == "open_dir":
                self.output_mgr.reveal_in_finder(self.output_mgr.outputs_dir)
                Prompt.ask("Press Enter to continue")
            else:
                self.post_audio_actions(Path(selected))

    def post_audio_actions(self, audio_path: Path) -> None:
        """Interactive actions available right after selecting/generating audio."""
        while True:
            act = inquirer.select(
                message=f"Actions for [{audio_path.name}]:",
                choices=[
                    Choice(value="play", name="▶️  1. Play Audio (macOS afplay)"),
                    Choice(value="stop", name="⏹️  2. Stop Audio Playback"),
                    Choice(value="desktop", name="🖥️  3. Copy to Desktop"),
                    Choice(value="finder", name="📂 4. Reveal in Finder"),
                    Choice(value="copy_path", name="📋 5. Print Full Absolute Path"),
                    Choice(value="bgm", name="🎶 6. Mix with Background Music (Auto-Duck)"),
                    Choice(value="speed", name="🏎️  7. Change Speed / Tempo"),
                    Separator(),
                    Choice(value="done", name="✅ 8. Done / Proceed"),
                    Choice(value="back", name="🔙 9. Back to Previous Screen")
                ]
            ).execute()

            if act == "play":
                console.print(f"[bold cyan]▶ Playing {audio_path.name}...[/bold cyan]")
                self.output_mgr.play_audio(audio_path)
            elif act == "stop":
                self.output_mgr.stop_audio()
                console.print("[yellow]⏹️ Audio playback stopped.[/yellow]")
            elif act == "desktop":
                dest = self.output_mgr.copy_to_desktop(audio_path)
                console.print(f"[bold green]✅ Copied to {dest}![/bold green]")
            elif act == "finder":
                self.output_mgr.reveal_in_finder(audio_path)
            elif act == "copy_path":
                console.print(f"\n[bold yellow]{audio_path.resolve()}[/bold yellow]\n")
            elif act == "bgm":
                bgm_str = inquirer.text(message="Enter path to BGM audio file:").execute()
                bgm_path = Path(bgm_str.strip("'\" "))
                if bgm_path.exists():
                    out_f = self.output_mgr.outputs_dir / f"{audio_path.stem}_bgm.mp3"
                    res = self.bgm_mixer.mix_voice_and_bgm(audio_path, bgm_path, out_f)
                    if res.get("success"):
                        console.print(f"[green]Mixed: {out_f}[/green]")
            elif act == "speed":
                sp = inquirer.select(message="Speed factor:", choices=[0.85, 1.15, 1.25, 1.5]).execute()
                out_f = self.output_mgr.outputs_dir / f"{audio_path.stem}_{sp}x.mp3"
                res = self.audio_proc.adjust_speed(audio_path, out_f, speed_factor=float(sp))
                if res.get("success"):
                    console.print(f"[green]Speed adjusted: {out_f}[/green]")
            elif act in ("done", "back"):
                self.output_mgr.stop_audio()
                break

    # ─── 14. TAG HELPER ──────────────────────────────────────────────────────
    def handle_tag_helper(self) -> None:
        self.print_header("Audio Expression Tag Helper & Cheat Sheet")
        
        table = Table(title="ElevenLabs v3 Conversational Audio Tags", border_style="cyan")
        table.add_column("Tag Syntax", style="bold yellow")
        table.add_column("Description & Effect", style="white")
        table.add_column("Example Usage", style="dim cyan")

        for tag, desc in TAG_OPTIONS:
            ex = f"{tag} Welcome to the future of AI!"
            table.add_row(tag, desc, ex)

        console.print(table)
        console.print(Panel(
            "[bold white]💡 Pro Tip:[/bold white] You can stack multiple tags in a single sentence!\n"
            "Example: [bold yellow][whispers] Sunno... [excited] [amazed] 750% profit on complete autopilot! [laughs][/bold yellow]",
            border_style="yellow"
        ))
        Prompt.ask("\nPress Enter to return to main menu")

    # ─── SHARED FLOW HELPERS ─────────────────────────────────────────────────
    def select_voice_flow(self) -> Optional[Any]:
        while True:
            choices = [
                Choice(value=v, name=f"{v['name']} ({v.get('gender')}) - {v.get('desc')}")
                for v in POPULAR_VOICES
            ] + [
                Separator(),
                Choice(value="browse_more", name="🔍 Browse Full ElevenLabs Voice Library (20+ Voices)..."),
                Choice(value="__BACK__", name="🔙 Back to Previous Step")
            ]
            
            choice = inquirer.select(message="Select a voice:", choices=choices).execute()
            if choice == "__BACK__":
                return "__BACK__"
            
            if choice == "browse_more":
                all_v = self.voice_browser.fetch_all_voices()
                choice = inquirer.select(
                    message="Select from full library:",
                    choices=[Choice(value=v, name=f"{v['name']} ({v.get('gender')}, {v.get('accent')})") for v in all_v[:40]] + [Separator(), Choice(value=None, name="🔙 Back to Popular Voices")]
                ).execute()
                if not choice:
                    continue

            while True:
                is_playing = self.output_mgr.player.is_playing()
                console.print(f"\n[bold cyan]Selected Voice:[/bold cyan] [bold white]{choice['name']}[/bold white] ({choice.get('gender', '?')}, {choice.get('accent', '?')})")
                if choice.get("desc"):
                    console.print(f"[dim]{choice['desc']}[/dim]\n")
                
                demo_choices = [
                    Choice(value="done", name=f"✅ 1. Done & Proceed with [{choice['name']}]"),
                    Choice(value="listen", name=f"🎧 2. Listen to 5-Sec Voice Demo Sample (Instant Play)"),
                    Choice(value="stop", name="⏹️  3. Stop Audio Playback"),
                    Choice(value="back", name="🔙 4. Back (Choose a Different Voice)")
                ]

                v_action = inquirer.select(
                    message=f"Proceed with [{choice['name']}] or listen to demo first?",
                    choices=demo_choices,
                    default="done"
                ).execute()

                if v_action == "listen":
                    console.print(f"[bold yellow]▶ Playing audio sample for {choice['name']}... (macOS afplay)[/bold yellow]")
                    played = self.voice_browser.play_preview(choice)
                    if not played:
                        console.print("[red]Could not play sample audio.[/red]")
                elif v_action == "stop":
                    self.output_mgr.stop_audio()
                    console.print("[yellow]⏹️ Audio playback stopped.[/yellow]")
                elif v_action == "done":
                    self.output_mgr.stop_audio()
                    return choice
                elif v_action == "back":
                    self.output_mgr.stop_audio()
                    break

    def select_model_flow(self, allow_back: bool = True) -> str:
        choices = [
            Choice(value=m["id"], name=f"{m['name']} — {m['desc']}")
            for m in SUPPORTED_MODELS
        ]
        if allow_back:
            choices.extend([Separator(), Choice(value="__BACK__", name="🔙 Back to Previous Step")])

        return inquirer.select(
            message="Select ElevenLabs AI Model:",
            choices=choices,
            default="eleven_v3_conversational"
        ).execute()

    def select_preset_flow(self, allow_back: bool = True) -> Any:
        choices = [
            Choice(value=p, name=f"{p['name']} — {p['desc']}")
            for p in VOICE_PRESETS.values()
        ]
        if allow_back:
            choices.extend([Separator(), Choice(value="__BACK__", name="🔙 Back to Previous Step")])

        return inquirer.select(
            message="Select Voice Performance Preset:",
            choices=choices,
            default=VOICE_PRESETS["expressive"]
        ).execute()


if __name__ == "__main__":
    app = GenAudioApp()
    try:
        app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]GENAUDIO terminated by user. Goodbye![/yellow]\n")
        sys.exit(0)
