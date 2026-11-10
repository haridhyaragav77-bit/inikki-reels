# Voice Tool — how to use it (for agents)

A free text-to-speech tool using Microsoft's neural voices (through the `edge-tts` library), with an optional mode that dubs speech onto a video.

- **Tool file:** `voice_tool.py` (same folder as this guide)
- **Needs:** Python 3.9+ and a normal internet connection. On first run it installs `edge-tts` and `imageio-ffmpeg` by itself. No API key, no cost.
- **Run it** with `python voice_tool.py <command> ...` from a terminal. Every command prints a JSON result on its **last line** (`"ok": true/false`). Parse that.
- **Where it works:** on a normal computer. Sandboxed/cloud AI workspaces often block Microsoft's speech service. If you see network errors there, run it on the user's machine.

## Commands

### 1. List voices
```
python voice_tool.py voices --lang ta
```
`--lang` filters by language code (`ta`, `en-IN`, `hi`, …).

### 2. Speak one line
```
python voice_tool.py say --text "வணக்கம்!" --out hello.mp3 --voice ta-IN-ValluvarNeural --rate +35% --pitch -2Hz
```
Returns `{"ok": true, "file": "...", "seconds": 1.4}`.

### 3. Many lines at once
```
python voice_tool.py batch --plan plan.json --outdir clips
```
Makes `clips/line_00.mp3`, `line_01.mp3`, … plus `clips/full.mp3` (all lines joined, 0.3 s gaps). Returns each clip's length in seconds.

### 4. Dub a video
```
python voice_tool.py dub --plan plan.json --video input.mp4
```
- Places each line at its `start` time.
- If a line is longer than its slot (`end − start`), it is sped up, at most 1.35×. The result reports `overruns: true` for any line that still doesn't fit. Shorten that text, or widen its slot.
- Lowers the video's own audio (music, effects) while the voice speaks.
- Writes `input_VOICED.mp4` (or `--out`), keeping the video untouched.
- Clips are cached in `input_voice_clips/`. Re-running reuses them. Use `--fresh`, or delete one clip, to remake it.

## plan.json
```json
{
  "voice": "ta-IN-ValluvarNeural",
  "rate": "+35%",
  "pitch": "-2Hz",
  "duck": 0.3,
  "lines": [
    {"text": "முதலீடே இல்லாம, மாசம் பத்தொன்பது ஆயிரம் வேணுமா?", "start": 0.1, "end": 3.5, "rate": "+30%"},
    {"text": "Crypto இல்ல. MLM இல்ல.", "start": 5.3, "end": 7.4}
  ]
}
```
- Top-level `voice`/`rate`/`pitch` are defaults. Each line can override them.
- `start`/`end` (seconds) are only needed for `dub`.
- `duck` = how loud the video's own audio stays under the voice (0.3 = 30%).

## Settings that work well (tested)
- **Tamil voices:** `ta-IN-ValluvarNeural` (male) and `ta-IN-PallaviNeural` (female).
- **Speed:** `+30%` to `+38%` sounds like natural, energetic speech. `+10%` sounds too slow.
- **Pitch:** `-4Hz` to `+0Hz`.
- **Writing:** write in the language's own script, in short sentences with full stops. Common English words (Google, phone, free) can stay in English. Split long compound numbers into separate words.
- **Timing:** speech length is unknown until generated. For exact timing, run `batch` first, read the `seconds` it returns, then set `start`/`end` (or time your video) from those numbers.
