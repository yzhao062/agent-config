"""Add music, narration or both to a rendered video: the music ducks under the voice, then AAC is muxed in.

    python mix.py VIDEO.mp4 OUT.mp4 [--music music.wav] [--voice voice.wav] [--duck 9] [--music-gain 0]

The audio is cut or padded to the video's length, and every frame is kept (ffmpeg's -shortest dropped the last
four). While the voice speaks, the music drops by --duck dB, with a 0.15 s attack and a 0.5 s release. The voice is set
to about -16 dBFS RMS while speaking, and the sum is kept below -1 dBFS peak. The picture is copied, not re-encoded.
"""
import argparse
import os
import subprocess
import tempfile

import imageio_ffmpeg
import numpy as np
from scipy.io import wavfile

SR = 44100


def load(path, n):
    sr, x = wavfile.read(path)
    if sr != SR:
        raise SystemExit(f"{path}: {sr} Hz, expected {SR}")
    x = x.astype(float) / 32768
    x = np.stack([x, x], axis=1) if x.ndim == 1 else x[:, :2]
    out = np.zeros((n, 2))
    out[: min(n, len(x))] = x[:n]
    return out


def smooth(gate, attack, release, step=44):
    """One-pole smoothing, fast in and slow out, computed at SR / step and held back up to SR."""
    g = gate[::step]
    out, y = np.empty_like(g), 0.0
    a, r = np.exp(-step / (attack * SR)), np.exp(-step / (release * SR))
    for i, v in enumerate(g):
        c = a if v > y else r
        y = c * y + (1 - c) * v
        out[i] = y
    return np.repeat(out, step)[: len(gate)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--music")
    ap.add_argument("--voice")
    ap.add_argument("--duck", type=float, default=9)
    ap.add_argument("--music-gain", type=float, default=0, help="dB applied to the music before ducking")
    a = ap.parse_args()
    if not (a.music or a.voice):
        raise SystemExit("give --music, --voice or both")
    _, secs = imageio_ffmpeg.count_frames_and_secs(a.video)
    n = int(round(secs * SR))
    mix = np.zeros((n, 2))
    voice = load(a.voice, n) if a.voice else None
    if voice is not None:
        mono = voice.mean(axis=1)
        w = int(0.05 * SR)
        env = np.sqrt(np.convolve(mono ** 2, np.ones(w) / w, "same"))
        speaking = env > 10 ** (-40 / 20)
        if speaking.any():
            voice *= 10 ** (-16 / 20) / np.sqrt(np.mean(mono[speaking] ** 2))
        mix += voice
    if a.music:
        music = load(a.music, n) * 10 ** (a.music_gain / 20)
        if voice is not None:
            gate = smooth(speaking.astype(float), 0.15, 0.5)
            music *= (10 ** (-a.duck * gate / 20))[:, None]
        mix += music
    peak = np.max(np.abs(mix))
    if peak > 10 ** (-1 / 20):
        mix *= 10 ** (-1 / 20) / peak
    print(f"peak {20 * np.log10(np.max(np.abs(mix))):.1f} dBFS over {secs:.2f} s")
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "mix.wav")
        wavfile.write(wav, SR, (mix * 32767).astype(np.int16))
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", a.video, "-i", wav, "-map", "0:v",
                        "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                        a.out], check=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
