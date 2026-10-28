#!/usr/bin/env python3
"""A 720p copy of a rendered video small enough to send to a phone (Amitai reviews lessons on his).

Usage:
    python3 phone_copy.py lesson.mp4 -o lesson-1-phone-720p.mp4 [--mb 30]

Two-pass H.264 at the bitrate that fits the size (5% headroom), AAC 64 kb/s stereo, faststart. Give the copy a
plain ASCII name: a Hebrew file name was sent fine but some phone previews played it silent. Before sending,
the script checks the copy still has its sound. If he still hears nothing, it is the phone (the silent switch
mutes in-app video on an iPhone), not the file.
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

AUDIO_KBPS, MIN_VIDEO_KBPS = 64, 250


def video_kbps(seconds: float, mb: float) -> int:
    """Video bitrate that keeps the whole file under mb megabytes (MiB), with 5% for the container."""
    total = mb * 8 * 1024 * 0.95 / seconds
    kbps = int(total - AUDIO_KBPS)
    if kbps < MIN_VIDEO_KBPS:
        raise SystemExit(f"error: {seconds:.0f} s doesn't fit in {mb} MB at 720p; split it or raise --mb")
    return kbps


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def mean_volume(path: Path) -> float:
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-t", "60", "-i", str(path), "-vn", "-af", "volumedetect",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    for line in log.splitlines():
        if "mean_volume:" in line:
            return float(line.split("mean_volume:")[1].split()[0])
    return float("-inf")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--mb", type=float, default=30.0)
    a = ap.parse_args(argv)
    src, out = Path(a.video), Path(a.out)
    if not out.name.isascii():
        print(f"note: {out.name} isn't ASCII; some phone previews play such files silent", file=sys.stderr)
    kbps = video_kbps(duration(src), a.mb)
    with tempfile.TemporaryDirectory() as tmp:
        log = str(Path(tmp) / "pass")
        common = ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", "scale=-2:720", "-c:v", "libx264", "-preset", "slow",
                  "-b:v", f"{kbps}k", "-passlogfile", log]
        subprocess.run(common + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"], check=True)
        subprocess.run(common + ["-pass", "2", "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k", "-ac", "2", "-movflags", "+faststart",
                                 str(out)], check=True)
    size = out.stat().st_size / 2 ** 20
    vol = mean_volume(out)
    if vol < -50:
        raise SystemExit(f"error: {out} has no audible sound (mean {vol:.0f} dB)")
    print(f"{out}: {size:.1f} MB, video {kbps} kb/s, sound at {vol:.0f} dB mean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
