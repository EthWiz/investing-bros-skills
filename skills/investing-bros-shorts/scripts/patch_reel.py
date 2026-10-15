"""patch_reel.py WORKDIR SRC CONTENT_END SRC_END OUT - point a temp copy of reel/ at one clip.
reel/ is already generic (fix.json word fixes, optional mgs.json cues, title.png overlay); this only sets paths/times."""
import sys, re, os
wd, src, ce, se, out = sys.argv[1:6]
def sub(fn, pairs):
    p = os.path.join(wd, fn); s = open(p).read()
    for a, b in pairs:
        assert re.search(a, s), f"{fn}: pattern not found: {a}"
        s = re.sub(a, lambda m: b, s, count=1)
    open(p, "w").write(s)
sub("plan.py", [(r'SRC = "[^"]*"', f'SRC = "{src}"'), (r"CONTENT_END = [\d.]+", f"CONTENT_END = {ce}"),
                (r"SRC_END = [\d.]+", f"SRC_END = {se}")])
sub("render.py", [(r'OUT = "[^"]*"', f'OUT = "{out}"')])
print("patched", wd)
