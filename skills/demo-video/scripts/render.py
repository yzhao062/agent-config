"""Render a demo-video site frame by frame in headless Chromium and encode it as H.264.

    python render.py SITE --stills 2,9.5,21 OUTDIR       PNG stills at those seconds
    python render.py SITE --video OUT.mp4 [--fps 30]     every frame, piped to ffmpeg (libx264, CRF 18, yuv420p)
    python render.py SITE --timeline timeline.json       scene names, starts and durations, for music and narration

The page contract: it sets window.READY once fonts and images are in, window.DURATION in seconds, window.SCENES as
[{name, start, dur}], and window.renderFrame(t), which draws the frame for time t from t alone. The site is served
over a local HTTP server so an iframe figure is same-origin with the page that animates it.
Needs playwright (with its Chromium) and imageio-ffmpeg, which bundles an ffmpeg built with libx264.
"""
import argparse
import functools
import http.server
import json
import subprocess
import threading
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--stills")
    ap.add_argument("--video")
    ap.add_argument("--timeline")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1920x1080")
    args = ap.parse_args()
    w, h = (int(v) for v in args.size.split("x"))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(Path(args.site))))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{httpd.server_port}/index.html")
        page.wait_for_function("window.READY === true || window.FAILED", timeout=60000)
        if errors or page.evaluate("window.FAILED || null"):
            raise SystemExit(f"page failed: {errors or page.evaluate('window.FAILED')}")
        duration = page.evaluate("window.DURATION")
        scenes = page.evaluate("(window.SCENES || []).map(s => ({name: s.name, start: +s.start.toFixed(3), dur: +s.dur.toFixed(3)}))")
        print(f"duration {duration:.2f} s")
        for s in scenes:
            print(f"  {s['start']:6.2f}  {s['dur']:5.2f}  {s['name']}")
        if args.timeline:
            Path(args.timeline).write_text(json.dumps({"duration": duration, "scenes": scenes}, indent=1), encoding="utf-8")
        if args.stills:
            out = Path(args.out or "stills")
            out.mkdir(parents=True, exist_ok=True)
            for s in args.stills.split(","):
                page.evaluate("t => renderFrame(t)", float(s))
                page.screenshot(path=str(out / f"t{float(s):06.2f}.png"))
            print("stills in", out)
        if args.video:
            n = int(round(duration * args.fps))
            cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(args.fps),
                   "-c:v", "png", "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                   "-profile:v", "high", "-movflags", "+faststart", args.video]
            enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            for k in range(n):
                page.evaluate("t => renderFrame(t)", k / args.fps)
                enc.stdin.write(page.screenshot(type="png"))
                if k % 300 == 0:
                    print(f"frame {k}/{n}", flush=True)
            enc.stdin.close()
            if enc.wait():
                raise SystemExit("ffmpeg failed")
            print("wrote", args.video)
        if errors:
            raise SystemExit(f"page errors: {errors}")
        browser.close()
    httpd.shutdown()


if __name__ == "__main__":
    main()
