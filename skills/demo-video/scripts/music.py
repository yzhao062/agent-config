"""Synthesize an original background track for a demo video: no samples and no third-party audio, so no licence.

    python music.py OUT.wav --duration 63.5 --groove 15.1 57.6 [--arp 4.8] [--bpm 100] [--transpose 0] [--level -17]

A soft major-key track in four chords, two bars each (I maj9, vi 9, IV maj7, V add9; D major unless transposed).
Sections: a pad from the start; a plucked arpeggio from --arp; a noise swell into the groove; bass, a kick on beats 1
and 3 and off-beat hats from the bar line nearest the groove start to the bar line nearest its end; then the
last chord holds and everything fades over --fade seconds. Take the groove times from the video's timeline (the
first and last scenes that should carry it). The level is the RMS of the groove in dBFS; peaks stay below -1.5 dBFS.
The agent cannot hear the result: check the printed peak and level, and let the user judge by ear.
"""
import argparse

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
# (pad notes, bass note, arpeggio notes) as MIDI numbers in D major
CHORDS = [
    ([50, 54, 57, 61, 64], 38, [62, 69, 64, 66, 73]),   # Dmaj9
    ([47, 50, 54, 57, 61], 35, [59, 66, 61, 62, 69]),   # Bm9
    ([43, 47, 50, 54, 57], 31, [55, 62, 57, 59, 66]),   # Gmaj7
    ([45, 49, 52, 59, 64], 33, [57, 64, 59, 61, 68]),   # A(add9)
]
ARP = [0, 1, 2, 3, 1, 4, 2, 3]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lowpass(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)


def highpass(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)


class Track:
    def __init__(self, a):
        self.dur, self.n = a.duration, int(SR * a.duration)
        self.beat = 60 / a.bpm
        self.bar = 4 * self.beat
        self.tr = a.transpose
        self.arp_start = a.arp
        self.g0 = round(a.groove[0] / self.bar) * self.bar    # the nearest bar line, so the swell can lead in
        self.g1 = max(self.g0 + 2 * self.bar, round(a.groove[1] / self.bar) * self.bar)
        self.fade = a.fade
        self.rng = np.random.default_rng(7)

    def chord(self, bar):
        pad, bass, arp = CHORDS[(bar // 2) % len(CHORDS)]
        return [m + self.tr for m in pad], bass + self.tr, [m + self.tr for m in arp]

    def place(self, buf, start, sig):
        i = int(start * SR)
        if i < 0:
            sig, i = sig[-i:], 0
        if i >= len(buf):
            return
        sig = sig[: len(buf) - i]
        buf[i:i + len(sig)] += sig

    def pad_voice(self, notes, length, seed):
        t = np.arange(length) / SR
        r = np.random.default_rng(seed)
        out = np.zeros(length)
        for m in notes:
            for det in (-0.0021, 0.0, 0.0023):
                f = hz(m) * (1 + det)
                for k in range(1, 7):
                    out += np.sin(2 * np.pi * f * k * t + r.uniform(0, 2 * np.pi)) / k ** 1.6
        return out / (len(notes) * 3)

    def pads(self):
        L, R = np.zeros(self.n), np.zeros(self.n)
        b = 0
        while b * self.bar < self.dur:
            start = b * self.bar
            final = start >= self.g1 - 1e-6           # the last chord holds to the end
            seg = self.dur - start + 0.4 if final else 2 * self.bar
            length = int((seg + 1.6) * SR)
            t = np.arange(length) / SR
            env = np.minimum(1, t / 1.2) * (1 if final else np.clip((seg + 1.6 - t) / 1.6, 0, 1))
            notes = self.chord(b)[0]
            self.place(L, start - 0.4, self.pad_voice(notes, length, 11 + b) * env)
            self.place(R, start - 0.4, self.pad_voice(notes, length, 97 + b) * env)
            if final:
                break
            b += 2
        t = np.arange(self.n) / SR
        breathe = 0.85 + 0.15 * np.sin(2 * np.pi * t / (2 * self.bar))
        return lowpass(L, 1700) * breathe, lowpass(R, 1700) * breathe

    def pluck(self, f, length=0.9, tau=0.26):
        t = np.arange(int(length * SR)) / SR
        env = (1 - np.exp(-t / 0.004)) * np.exp(-t / tau)
        return env * (np.sin(2 * np.pi * f * t) + 0.28 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t))

    def arps(self):
        L, R = np.zeros(self.n), np.zeros(self.n)
        k = 0
        while self.arp_start + k * self.beat / 2 < self.dur - 1.0:
            when = self.arp_start + k * self.beat / 2
            if when >= self.g1 and k % 2:             # the outro thins to quarter notes
                k += 1
                continue
            m = self.chord(int(when / self.bar))[2][ARP[k % 8]] + 12
            vel = (0.9 if k % 4 == 0 else 0.62 + 0.08 * ((k * 5) % 3)) * (0.8 if when >= self.g1 else 1)
            s = self.pluck(hz(m)) * vel
            pan = 0.5 + 0.22 * np.sin(k * 0.9)
            self.place(L, when, s * (1 - pan) * 2)
            self.place(R, when, s * pan * 2)
            k += 1
        d = int(0.75 * self.beat * SR)                # ping-pong delay at a dotted eighth
        wl, wr = np.zeros(self.n), np.zeros(self.n)
        for tap in range(1, 6):
            g = 0.42 ** tap
            a, b = (R, L) if tap % 2 else (L, R)
            wl[tap * d:] += g * a[: self.n - tap * d]
            wr[tap * d:] += g * b[: self.n - tap * d]
        return L + 0.55 * lowpass(wl, 3500), R + 0.55 * lowpass(wr, 3500)

    def bass(self):
        out = np.zeros(self.n)
        for b in range(int(round(self.g0 / self.bar)), int(round(self.g1 / self.bar))):
            f = hz(self.chord(b)[1] + 12)
            length = 2 * self.beat
            t = np.arange(int(length * SR)) / SR
            env = (1 - np.exp(-t / 0.012)) * np.exp(-t / 1.1) * np.clip((length - t) / 0.08, 0, 1)
            s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.1 * np.sin(6 * np.pi * f * t)
            for half in (0, 2):
                self.place(out, b * self.bar + half * self.beat, env * s)
        return lowpass(out, 900)

    def drums(self):
        kick, hl, hr, sw = (np.zeros(self.n) for _ in range(4))
        t = np.arange(int(0.5 * SR)) / SR
        k = np.sin(2 * np.pi * np.cumsum(46 + 80 * np.exp(-t / 0.035)) / SR) * np.exp(-t / 0.2)
        k[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
        th = np.arange(int(0.12 * SR)) / SR
        hat = highpass(self.rng.standard_normal(len(th)), 7000, 4) * np.exp(-th / 0.03)
        for b in range(int(round(self.g0 / self.bar)), int(round(self.g1 / self.bar))):
            for beat in (0, 2):
                self.place(kick, b * self.bar + beat * self.beat, k)
            for e in range(4):
                self.place(hl if e % 2 else hr, b * self.bar + (e + 0.5) * self.beat, hat * (1.0 if e % 2 else 0.7))
        ts = np.arange(int(self.bar * SR)) / SR      # a soft noise swell over the bar before the groove
        self.place(sw, self.g0 - self.bar, lowpass(self.rng.standard_normal(len(ts)), 2500) * (ts / ts[-1]) ** 2.5)
        return kick, hl, hr, sw

    def reverb(self, x, seed, length=2.6):
        t = np.arange(int(length * SR)) / SR
        ir = lowpass(np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t / 0.6), 6000)
        return fftconvolve(x, ir / np.sqrt(np.sum(ir ** 2)))[: len(x)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--duration", type=float, required=True)
    ap.add_argument("--groove", type=float, nargs=2, required=True, metavar=("START", "END"))
    ap.add_argument("--arp", type=float, default=None, help="arpeggio start in seconds (default: two bars in)")
    ap.add_argument("--bpm", type=float, default=100)
    ap.add_argument("--transpose", type=int, default=0, help="semitones from D major")
    ap.add_argument("--level", type=float, default=-17, help="groove RMS in dBFS")
    ap.add_argument("--fade", type=float, default=3.2)
    a = ap.parse_args()
    if a.arp is None:
        a.arp = 2 * 4 * 60 / a.bpm
    T = Track(a)
    pad_l, pad_r = T.pads()
    arp_l, arp_r = T.arps()
    bass = T.bass()
    kick, hats_l, hats_r, swell = T.drums()
    rv_l, rv_r = T.reverb(0.6 * pad_l + 0.7 * arp_l, 1), T.reverb(0.6 * pad_r + 0.7 * arp_r, 2)
    L = 0.5 * pad_l + 0.32 * arp_l + 0.36 * bass + 0.5 * kick + 0.05 * hats_l + 0.045 * swell + 0.32 * rv_l
    R = 0.5 * pad_r + 0.32 * arp_r + 0.36 * bass + 0.5 * kick + 0.05 * hats_r + 0.045 * swell + 0.32 * rv_r
    mix = np.stack([highpass(L, 28), highpass(R, 28)], axis=1)
    t = np.arange(T.n) / SR
    mix *= (np.minimum(1, t / 0.8) * np.clip((T.dur - t) / a.fade, 0, 1) ** 1.5)[:, None]
    mix = np.tanh(1.3 * mix / np.max(np.abs(mix))) / np.tanh(1.3)
    g = slice(int(T.g0 * SR), int(T.g1 * SR))
    mix *= min(10 ** (a.level / 20) / np.sqrt(np.mean(mix[g] ** 2)), 10 ** (-1.5 / 20) / np.max(np.abs(mix)))
    steps = np.max(np.abs(np.diff(mix, axis=0)))
    print(f"groove {T.g0:.2f}-{T.g1:.2f} s; peak {20 * np.log10(np.max(np.abs(mix))):.1f} dBFS; "
          f"groove rms {20 * np.log10(np.sqrt(np.mean(mix[g] ** 2))):.1f} dBFS; largest sample step {steps:.3f} (a click is > 0.3)")
    wavfile.write(a.out, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    main()
