"""The voice with a pretend ElevenLabs: one take per line, kept lines cost nothing, the backup takes over when the main
voice cannot speak. Run: python -m tests.test_voice   (no keys, no credits spent)"""
import base64
import os
import shutil
import subprocess
import sys
import tempfile

from engine import voice


class Reply:
    ok, status_code = True, 200
    headers = {"character-cost": "12"}

    def __init__(self, body):
        self._b = body

    def json(self):
        return self._b


def main():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("ok   " if cond else "FAIL ") + name)

    tmp = tempfile.mkdtemp()
    tone = os.path.join(tmp, "tone.mp3")
    subprocess.run([voice._ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=200:duration=1.2", tone], check=True)
    audio = base64.b64encode(open(tone, "rb").read()).decode()
    calls = []

    def post(url, params=None, headers=None, json=None, timeout=None):
        calls.append(json)
        text = json["text"]
        n = len(text)
        return Reply({"audio_base64": audio, "alignment": {"characters": list(text), "character_start_times_seconds": [i * 1.2 / n for i in range(n)],
                                                           "character_end_times_seconds": [(i + 1) * 1.2 / n for i in range(n)]}})
    os.environ["ELEVENLABS_API_KEY"] = "test"
    voice.requests.post = post
    left = {"n": 30000}
    voice.subscription = lambda: {"used": 40000 - left["n"], "limit": 40000, "left": left["n"], "tier": "starter", "resets": "2026-12-04"}
    used = []
    voice.note_use = lambda drive, provider, reel_id, credits=0, reused=0, why=None, sub=None: used.append((provider, credits, reused, why))
    plan = {"voice": "ta-IN-ValluvarNeural", "rate": "+18%", "one_take": False, "lines": [{"text": "இந்த shot-a கவனிச்சீங்களா?"}, {"text": "இது ஒரு match cut."}]}

    r, why = voice.main_voice(plan, os.path.join(tmp, "el"), None, "reel-1")
    check("ElevenLabs speaks first, one call per line", r and r["provider"] == "elevenlabs" and len(calls) == 2)
    check("a Microsoft voice name in a plan does not reach ElevenLabs", r["voice_id"] == voice.voice_id(None))
    check("the lines before and after are sent, so the reel sounds like one read", calls[0].get("next_text") and calls[1].get("previous_text"))
    w = r["clips"][0]["words"]
    check("word timings for subtitles", [x["w"] for x in w] == ["இந்த", "shot-a", "கவனிச்சீங்களா"] and w[1]["t"] > w[0]["t"])
    check("the credits used are counted", used[-1][:2] == ("elevenlabs", 24))
    r2, _ = voice.main_voice(plan, os.path.join(tmp, "el"), None, "reel-1")
    check("the same lines again cost nothing (no second draft)", len(calls) == 2 and r2["reused"] == 2 and r2["credits"] == 0)
    plan2 = {"one_take": False, "lines": [{"text": "இந்த shot-a கவனிச்சீங்களா?"}, {"text": "புது வரி."}]}
    voice.main_voice(plan2, os.path.join(tmp, "el"), None, "reel-1")
    check("after a word change only the changed line is recorded", len(calls) == 3)

    # one take (the default since 19 Nov): the whole reel in one call, cut into one clip per line with its own word times
    plan3 = {"lines": [{"text": "முதல் வரி இது."}, {"text": "ரெண்டாவது வரி இங்கே."}]}
    r5, _ = voice.main_voice(plan3, os.path.join(tmp, "el"), None, "reel-4")
    check("one take: one call for the whole reel", len(calls) == 4 and r5 and r5.get("one_take") and calls[-1]["text"] == "முதல் வரி இது. ரெண்டாவது வரி இங்கே.")
    check("one take: each line gets its own clip and words", len(r5["clips"]) == 2 and [x["w"] for x in r5["clips"][1]["words"]][0] == "ரெண்டாவது"
          and r5["clips"][1]["words"][0]["t"] < 0.3)
    r6, _ = voice.main_voice(plan3, os.path.join(tmp, "el"), None, "reel-4")
    check("one take: the same reel again costs nothing", len(calls) == 4 and r6["credits"] == 0)
    left["n"] = 900                                           # under the reserve: the backup must speak
    r3, why = voice.main_voice({"lines": [{"text": "இன்னொரு புது வரி."}]}, os.path.join(tmp, "el"), None, "reel-2")
    check("near the end of the credits the backup voice is chosen", r3 is None and "credits" in why and len(calls) == 4)
    check("the reason is written in plain words", "backup voice (Microsoft)" in voice.backup_note(None, "reel-2", why))
    r4, why = voice.main_voice({"provider": "microsoft", "lines": [{"text": "x"}]}, os.path.join(tmp, "el"), None, "reel-3")
    check("a reel or series can ask for the Microsoft voice", r4 is None and why is None)
    shutil.rmtree(tmp, ignore_errors=True)
    print("\nALL PASSED" if ok else "\nFAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
