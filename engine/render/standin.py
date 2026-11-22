"""Stand-in timing for a test render without the voice service (python -m engine.render <plan> --local).

Writes engine/.work/<id>/timeline.json with each voiced word placed at an even pace (about the real voice at 1.2x)
and a silent audio.wav of the same length, so the frames, cues and layout of any approved look can be checked
anywhere, with no keys. Never used for a reel that posts."""
import json
import os
import subprocess
import sys

WORD_S = 0.34          # seconds a Tamil word takes at the page's voice speed (measured on posted reels, roughly)


def timeline(plan):
    t, tl = 0.0, []
    for i, s in enumerate(plan["screens"]):
        lead = s.get("lead", 0.45 if i == 0 else 0.12)
        words = str(s.get("voice") or "").split()
        e = {"i": i, "kind": s.get("kind"), "start": round(t, 3), "words": []}
        if words:
            e["voice_at"] = round(t + lead, 3)
            for k, w in enumerate(words):
                e["words"].append({"w": w, "t": round(t + lead + k * WORD_S, 3), "d": round(WORD_S * .9, 3)})
            e["voice_end"] = round(t + lead + len(words) * WORD_S, 3)
            dur = max(s.get("min", 0.0), lead + len(words) * WORD_S + s.get("tail", 0.3))
        else:
            dur = float(s.get("dur", 3.0))
        e["end"] = round(t + dur, 3)
        tl.append(e)
        t += dur
    beats = [round(k * 0.5, 3) for k in range(int(t / 0.5) + 1)]          # a steady 120 bpm stand-in beat
    return {"id": plan.get("id") or plan.get("reel_id"), "duration": round(t, 3), "fps": plan.get("fps", 30), "screens": tl,
            "beats": beats, "music": [], "sfx": [], "voice_provider": "stand-in", "voice_note": "stand-in timing, no voice"}


def main(plan_path, work):
    plan = json.load(open(plan_path, encoding="utf-8"))
    os.makedirs(work, exist_ok=True)
    tl = timeline(plan)
    json.dump(tl, open(os.path.join(work, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(tl["duration"]),
                    "-c:a", "pcm_s16le", os.path.join(work, "audio.wav")], check=True)
    print(json.dumps({"ok": True, "duration": tl["duration"], "screens": len(tl["screens"]), "stand_in": True}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
