"""check_links.py: link parsing, YouTube ids, oEmbed status and the message signature."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_links as cl  # noqa: E402


def test_find_links_dedupes_and_strips_punctuation():
    text = "צפו: https://youtu.be/AbCdEfGhIjK. ושוב https://youtu.be/AbCdEfGhIjK\n(https://open.spotify.com/episode/x1)"
    assert cl.find_links(text) == ["https://youtu.be/AbCdEfGhIjK", "https://open.spotify.com/episode/x1"]


def test_youtube_ids():
    assert cl.youtube_id("https://www.youtube.com/watch?v=AbCdEfGhIjK&t=30") == "AbCdEfGhIjK"
    assert cl.youtube_id("https://www.youtube.com/watch?feature=share&v=AbCdEfGhIjK") == "AbCdEfGhIjK"
    assert cl.youtube_id("https://youtu.be/AbCdEfGhIjK?si=x") == "AbCdEfGhIjK"
    assert cl.youtube_id("https://youtube.com/shorts/Ab-dEf_hIjK") == "Ab-dEf_hIjK"
    assert cl.youtube_id("https://studio.youtube.com/video/AbCdEfGhIjK/edit") == "AbCdEfGhIjK"
    assert cl.youtube_id("https://youtu.be/AbCdEfGhIj") is None  # 10 chars: truncated copy
    assert cl.youtube_id("https://youtu.be/AbCdEfGhIjKL") is None  # 12 chars


def test_oembed_status():
    assert cl.classify_oembed(200)[0]
    assert cl.classify_oembed(401)[0] and "private" in cl.classify_oembed(401)[1]
    assert not cl.classify_oembed(404)[0]
    assert not cl.classify_oembed(400)[0]


def test_signature():
    assert cl.signature_ok("לאישור נדב:\nhttps://youtu.be/AbCdEfGhIjK\n\nsent by Grokbot\n")
    assert not cl.signature_ok("https://youtu.be/AbCdEfGhIjK\nsent by Grokbot ✅")
    assert not cl.signature_ok("")


def test_offline_cli(tmp_path, capsys):
    good = tmp_path / "m.txt"
    good.write_text("פרק מלא: https://youtu.be/AbCdEfGhIjK\nsent by Grokbot\n", encoding="utf-8")
    assert cl.main([str(good), "--message", "--offline"]) == 0
    bad = tmp_path / "b.txt"
    bad.write_text("https://youtu.be/AbCdEf\n", encoding="utf-8")
    assert cl.main([str(bad), "--message", "--offline"]) == 1
    assert "sent by Grokbot" in capsys.readouterr().out


def test_exact_youtube_hosts_only():
    vid = "AbCdEfGhIjK"
    for u in (f"https://youtu.be/{vid}", f"https://www.youtube.com/watch?v={vid}",
              f"https://m.youtube.com/watch?v={vid}", f"https://youtube.com/shorts/{vid}",
              f"https://music.youtube.com/watch?v={vid}", f"https://www.youtube.com/embed/{vid}"):
        assert cl.youtube_id(u) == vid, u
    for u in (f"https://youtube.com.evil.io/watch?v={vid}", f"https://notyoutube.com/watch?v={vid}",
              f"https://youtu.be.co/{vid}", f"https://evil.io/youtu.be/{vid}",
              f"https://evil.io/?next=https://youtu.be/{vid}"):
        assert cl.youtube_id(u) is None, u
    assert cl.parse_check(f"https://youtube.com.evil.io/watch?v={vid}")[0] is False
    assert cl.parse_check("https://drive-google.com/file/d/x")[0] is False


def test_id_only_from_path_or_v_query():
    vid = "AbCdEfGhIjK"
    # an 11-char word elsewhere in the URL is not an id
    assert cl.youtube_id(f"https://www.youtube.com/watch?list=PL{vid}") is None
    assert cl.youtube_id(f"https://www.youtube.com/watch?v={vid}#t=AAAAAAAAAAA") == vid
    assert cl.youtube_id(f"https://youtu.be/{vid}/extra") is None
    assert cl.youtube_id(f"https://www.youtube.com/video/{vid}") is None  # only Studio uses /video/
    assert cl.parse_check(f"https://www.youtube.com/watch?list=PL{vid}")[0] is False


def test_channel_and_playlist_pages_are_not_videos():
    assert not cl.is_youtube_video("https://www.youtube.com/@investingbros")
    assert not cl.is_youtube_video("https://www.youtube.com/playlist?list=PLx")
    assert not cl.is_youtube_video("https://studio.youtube.com/channel/UCx/videos")
    assert cl.parse_check("https://www.youtube.com/@investingbros")[0] is None


class _Resp:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _fake_http(monkeypatch, answers):
    """answers: (method, url-prefix) -> status. Records every request."""
    import urllib.error
    calls = []

    def urlopen(req, timeout=20):
        calls.append((req.get_method(), req.full_url))
        for (m, pre), st in answers.items():
            if req.get_method() == m and req.full_url.startswith(pre):
                if st >= 400:
                    raise urllib.error.HTTPError(req.full_url, st, "x", {}, None)
                return _Resp(st)
        raise AssertionError(f"unexpected request {req.get_method()} {req.full_url}")

    monkeypatch.setattr(cl.urllib.request, "urlopen", urlopen)
    return calls


def test_youtube_goes_through_oembed_with_the_canonical_url(monkeypatch):
    calls = _fake_http(monkeypatch, {("GET", "https://www.youtube.com/oembed?"): 200})
    assert cl.check("https://youtu.be/AbCdEfGhIjK?si=share") == (True, "ok (public or unlisted)")
    assert calls == [("GET", "https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DAbCdEfGhIjK&format=json")]


def test_mistyped_id_is_bad_and_private_is_ok(monkeypatch):
    _fake_http(monkeypatch, {("GET", "https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DAbCdEfGhljK"): 404,
                             ("GET", "https://www.youtube.com/oembed?"): 401})
    ok, why = cl.check("https://youtu.be/AbCdEfGhljK")  # l instead of I
    assert not ok and "404" in why
    ok, why = cl.check("https://youtu.be/AbCdEfGhIjK")
    assert ok and "private" in why


def test_lookalike_host_makes_no_request(monkeypatch):
    calls = _fake_http(monkeypatch, {})
    ok, _ = cl.check("https://youtube.com.evil.io/watch?v=AbCdEfGhIjK")
    assert not ok and calls == []


def test_other_links_head_then_get(monkeypatch):
    calls = _fake_http(monkeypatch, {("HEAD", "https://open.spotify.com/"): 405,
                                     ("GET", "https://open.spotify.com/"): 200,
                                     ("HEAD", "https://drive.google.com/"): 404})
    assert cl.check("https://open.spotify.com/episode/x1") == (True, "HTTP 200")
    assert [m for m, _ in calls] == ["HEAD", "GET"]
    assert cl.check("https://drive.google.com/file/d/nope/view")[0] is False


def test_cli_with_mocked_http(tmp_path, monkeypatch, capsys):
    _fake_http(monkeypatch, {("GET", "https://www.youtube.com/oembed?"): 200})
    m = tmp_path / "m.txt"
    m.write_text("פרק מלא: https://youtu.be/AbCdEfGhIjK\nsent by Grokbot\n", encoding="utf-8")
    assert cl.main([str(m), "--message"]) == 0
    m.write_text("https://youtube.com.evil.io/watch?v=AbCdEfGhIjK\nsent by Grokbot\n", encoding="utf-8")
    assert cl.main([str(m), "--message"]) == 1
    assert "look-alike" in capsys.readouterr().out
