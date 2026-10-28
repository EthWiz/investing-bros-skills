"""Replace the background behind Amitai in a lesson take (used by make_lesson_base.py build).

The config's optional `background` block:
    {"method": "vision", "image": "assets/lesson-background-navy-studio.jpg"}
    {"method": "chroma", "image": "...", "key": {"color": "0x00B140", "similarity": 0.12, "blend": 0.06}}

vision  Apple Vision's person segmentation (person_matte.swift, macOS only), for a plain sheet behind him.
        One matte per take, cached in the matte folder by the take's sha256, so a rebuild with new trims
        doesn't segment again (about 40 s per 25 s of 1080p on an M4). Fast hands crossing the face and a
        high chair back are its known misses (recording-setup reference).
chroma  ffmpeg chromakey + despill, for the green screen. The key values are a starting point, not yet
        tuned on a real green-screen take: check the first one by eye (hair, hands, green on the shirt).
The image is 1920x1080, from investing-bros-brand (assets/lesson-background-navy-studio.jpg), copied into
the lesson's assets/ like any other lesson image, so the Drive package carries it.
"""
import hashlib
import shutil
import subprocess
from pathlib import Path

METHODS = ("vision", "chroma")
KEY = {"color": "0x00B140", "similarity": 0.12, "blend": 0.06}
EDGE = "erosion,gblur=sigma=1.6"          # pull the vision matte in by a pixel and soften it
SWIFT = Path(__file__).resolve().parent / "person_matte.swift"
CACHE = Path.home() / ".cache" / "investing-bros"


def check(bg: dict) -> dict:
    """The background block with its defaults filled in; exits on a block that can't work."""
    if bg.get("method") not in METHODS:
        raise SystemExit(f"error: background.method must be one of {', '.join(METHODS)}, not {bg.get('method')!r}")
    if not bg.get("image"):
        raise SystemExit("error: background.image is missing (a 1920x1080 image in the lesson's assets/)")
    out = dict(bg)
    if bg["method"] == "chroma":
        out["key"] = {**KEY, **bg.get("key", {})}
    return out


# where a framed take's own edge lands inside the frame, its alpha fades over this many pixels instead of a hard cut
FEATHER = 48


def take_chain(i: int, a: float, b: float, cut: str, bg: dict, bg_input: int, matte_input=None, frame=None) -> list:
    """Filter parts that put take i (`cut`: its video trimmed to a..b and scaled) on the background, ending in
    [v{i}]. The image is its own looped input per take, so concat never has to buffer a shared background.
    `frame` {scale, x, y} (lesson_framing.py) scales the cut-out take and places its top-left corner at x, y."""
    parts = [f"[{bg_input}:v]scale=1920:1080,setsar=1,format=rgba[bg{i}]"]
    if bg["method"] == "chroma":
        k = bg["key"]
        parts.append(f"{cut},chromakey=color={k['color']}:similarity={k['similarity']}:blend={k['blend']},"
                     f"format=rgba,despill=type=green[fg{i}]")
    else:
        if matte_input is None:
            raise SystemExit(f"error: take {i}: a vision background needs its matte")
        parts.append(f"{cut},format=rgba[c{i}]")
        parts.append(f"[{matte_input}:v]trim={a}:{b},setpts=PTS-STARTPTS,scale=1920:1080,fps=30,format=gray,{EDGE}[m{i}]")
        parts.append(f"[c{i}][m{i}]alphamerge[fg{i}]")
    if not frame:
        parts.append(f"[bg{i}][fg{i}]overlay=shortest=1,format=yuv420p[v{i}]")
        return parts
    s = frame["scale"]
    ramp = f"255*min(1,min(X/{FEATHER},(W-1-X)/{FEATHER}))"
    parts += [f"[fg{i}]split[fa{i}][fb{i}]",
              f"[fa{i}]alphaextract[al{i}]",
              f"color=c=white:s=1920x1080:r=30,format=gray,geq=lum='{ramp}'[r{i}]",
              f"[al{i}][r{i}]blend=all_mode=multiply:shortest=1[ae{i}]",
              f"[fb{i}][ae{i}]alphamerge,scale=w=trunc(iw*{s}/2)*2:h=trunc(ih*{s}/2)*2:flags=lanczos[fs{i}]",
              f"[bg{i}][fs{i}]overlay=x={frame['x']}:y={frame['y']}:shortest=1,format=yuv420p[v{i}]"]
    return parts


def swift_tool(src: Path, name: str, cache: Path = CACHE, which=shutil.which, run=subprocess.run) -> Path:
    """A Swift tool beside this script, compiled once per version of its source."""
    tag = hashlib.sha256(src.read_bytes()).hexdigest()[:12]
    tool = cache / f"{name}-{tag}"
    if tool.is_file():
        return tool
    if not which("swiftc"):
        raise SystemExit(f"error: {name} needs swiftc (macOS: xcode-select --install)")
    cache.mkdir(parents=True, exist_ok=True)
    run(["swiftc", "-O", "-suppress-warnings", str(src), "-o", str(tool)], check=True)
    return tool


def matte_tool(cache: Path = CACHE, which=shutil.which, run=subprocess.run) -> Path:
    """person_matte compiled once per version of its source."""
    return swift_tool(SWIFT, "person_matte", cache, which, run)


def matte_name(sha: str) -> str:
    return f"{sha[:16]}.matte.mkv"


def probe(take: Path):
    """(width, height, frame rate) of the take's video, the rate as ffprobe gives it (30/1)."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(take)],
                         capture_output=True, text=True, check=True).stdout.strip().split(",")
    return int(out[0]), int(out[1]), out[2]


def matte(take: Path, sha: str, folder: Path, tool: Path) -> Path:
    """The take's matte as a lossless gray video at the take's size and rate, made once and reused."""
    out = folder / matte_name(sha)
    if out.is_file():
        return out
    folder.mkdir(parents=True, exist_ok=True)
    part = out.with_name(out.name.replace(".matte.mkv", ".part.mkv"))
    w, h, rate = probe(take)
    seg = subprocess.Popen([str(tool), str(take)], stdout=subprocess.PIPE)
    enc = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
                          "-r", rate, "-i", "-", "-c:v", "ffv1", "-pix_fmt", "gray", str(part)], stdin=seg.stdout)
    seg.stdout.close()
    if seg.wait() != 0 or enc.returncode != 0:
        part.unlink(missing_ok=True)
        raise SystemExit(f"error: no matte for {take}")
    part.rename(out)
    return out
