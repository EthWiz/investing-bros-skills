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
