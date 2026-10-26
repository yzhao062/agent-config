"""Synthesize narration with edge-tts and place each line at its time in the video.

    python narrate.py SCRIPT.json OUT.wav --timeline timeline.json [--voice en-US-GuyNeural] [--rate +5%]

SCRIPT.json is a list of lines, each {"scene": NAME, "offset": SECONDS, "text": "..."} (relative to that scene's
start in the timeline render.py writes) or {"at": SECONDS, "text": "..."}. The script prints each line's start, length
and the gap to the next line, and stops when a line runs into the next one or past the end, so the text can be cut
before anything is mixed. The default voice and rate are the maintainer's choice.

edge-tts is an unofficial client of the online read-aloud service in Microsoft Edge: it needs the network, sends the
text to Microsoft, and has no service guarantee. Azure AI Speech offers the same voice names under a paid licence.
"""
import argparse
import asyncio
import json
import os
import subprocess
import tempfile

import edge_tts
import imageio_ffmpeg
import numpy as np
from scipy.io import wavfile

SR = 44100


async def synth(text, voice, rate, path):
    await edge_tts.Communicate(text, voice, rate=rate).save(path)


def decode(path):
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1",
                          "-ar", str(SR), "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.int16).astype(float) / 32768
    nz = np.flatnonzero(np.abs(x) > 1e-3)                 # trim the service's leading and trailing silence
    return x[nz[0]: nz[-1] + 1] if len(nz) else x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("out")
    ap.add_argument("--timeline", required=True)
    ap.add_argument("--voice", default="en-US-GuyNeural")
    ap.add_argument("--rate", default="+5%")
    ap.add_argument("--min-gap", type=float, default=0.25)
    a = ap.parse_args()
    with open(a.timeline, encoding="utf-8") as f:
        tl = json.load(f)
    starts = {s["name"]: s["start"] for s in tl["scenes"]}
    with open(a.script, encoding="utf-8") as f:
        lines = json.load(f)
    for ln in lines:
        ln["t"] = ln["at"] if "at" in ln else starts[ln["scene"]] + ln.get("offset", 0.0)
    lines.sort(key=lambda ln: ln["t"])
    track = np.zeros(int(tl["duration"] * SR))
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, ln in enumerate(lines):
            mp3 = os.path.join(tmp, f"{i}.mp3")
            asyncio.run(synth(ln["text"], a.voice, a.rate, mp3))
            x = decode(mp3)
            ln["len"] = len(x) / SR
            s = int(ln["t"] * SR)
            track[s: s + len(x)] += x[: max(0, len(track) - s)]
    for i, ln in enumerate(lines):
        end = ln["t"] + ln["len"]
        nxt = lines[i + 1]["t"] if i + 1 < len(lines) else tl["duration"]
        words = len(ln["text"].split())
        print(f"{ln['t']:6.2f}  {ln['len']:5.2f} s  {words / ln['len']:.1f} words/s  gap {nxt - end:+.2f}  {ln['text'][:60]}")
        if nxt - end < a.min_gap:
            problems.append(f"line at {ln['t']:.2f} s ends {end - nxt + a.min_gap:.2f} s too late; cut words or move the next line")
    if problems:
        raise SystemExit("\n".join(problems))
    peak = np.max(np.abs(track))
    track *= 10 ** (-3 / 20) / peak if peak else 1
    wavfile.write(a.out, SR, (np.stack([track, track], axis=1) * 32767).astype(np.int16))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
