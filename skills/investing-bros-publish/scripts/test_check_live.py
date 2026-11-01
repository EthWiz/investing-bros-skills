"""check_live.py: RedCircle feed item lookup and YouTube public/unlisted/private states."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_live as cl  # noqa: E402

FEED = """<?xml version="1.0"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel>
<item><title>\u05e4\u05e8\u05e7 9 - \u05de\u05d9 \u05d9\u05e8\u05d5\u05d5\u05d9\u05d7?\u200f</title>
<itunes:episode>9</itunes:episode><itunes:season>1</itunes:season>
<itunes:episodeType>full</itunes:episodeType><itunes:duration>2750</itunes:duration></item>
<item><title>old</title><itunes:episode>8</itunes:episode></item>
</channel></rss>"""
CHANNEL = "<feed><yt:videoId>YL1hdpdcVt8</yt:videoId><yt:videoId>6Z4joIPUBrM</yt:videoId></feed>"


def fake(responses):
    def get(url):
        for key, val in responses.items():
            if key in url:
                return val
        return 404, ""
    return get


def test_redcircle_found_and_title_match():
    get = fake({"feeds.redcircle.com": (200, FEED)})
    out = cl.check_redcircle(9, "\u05e4\u05e8\u05e7 9 - \u05de\u05d9 \u05d9\u05e8\u05d5\u05d5\u05d9\u05d7?", get)
    assert out[0].startswith("ok") and "2750" in out[0] and len(out) == 1


def test_redcircle_missing_or_wrong_title():
    get = fake({"feeds.redcircle.com": (200, FEED)})
    assert cl.check_redcircle(10, None, get)[0].startswith("FAIL")
    assert cl.check_redcircle(9, "other", get)[-1].startswith("FAIL")
    assert cl.check_redcircle(9, None, fake({}))[0].startswith("FAIL")


def test_youtube_states():
    assert cl.youtube_state(200, True) == "public"
    assert cl.youtube_state(200, False) == "unlisted"
    assert cl.youtube_state(403, False) == "private"
    assert cl.youtube_state(404, False) == "missing"


def test_check_youtube():
    get = fake({"feeds/videos.xml": (200, CHANNEL),
                "YL1hdpdcVt8": (200, "{}"), "6Z4joIPUBrM": (200, "{}"), "N_EaOlbiPAc": (200, "{}"),
                "mzV4BAzqdD0": (403, "")})
    out = cl.check_youtube(["YL1hdpdcVt8", "6Z4joIPUBrM"], "public", get)
    assert all(l.startswith("ok") for l in out)
    out = cl.check_youtube(["N_EaOlbiPAc", "mzV4BAzqdD0", "short"], "public", get)
    assert sum(l.startswith("FAIL") for l in out) == 3
    assert cl.check_youtube(["mzV4BAzqdD0"], "private", get)[0].startswith("ok")
