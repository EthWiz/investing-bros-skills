"""send_telegram.py `text`: the one approval message is checked before any API call."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import send_telegram as st  # noqa: E402


@pytest.mark.parametrize("text", ["", "   \n\t\n", "sent by Grokbot", "assets: https://youtu.be/x",
                                  "a\nsent by Grokbot ✅", "x" * 4100 + "\nsent by Grokbot"])
def test_bad_messages_are_refused(text):
    assert st.text_problem(text)


def test_good_message():
    assert st.text_problem("לאישור נדב:\nhttps://youtu.be/AbCdEfGhIjK\n\nsent by Grokbot\n") is None


@pytest.mark.parametrize("text", ["", "  \n ", "no signature here"])
def test_refused_text_makes_no_api_call(tmp_path, monkeypatch, text):
    msg = tmp_path / "approval.txt"
    msg.write_text(text, encoding="utf-8")
    calls = []
    monkeypatch.setattr(st, "call", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(st.subprocess, "run", lambda *a, **k: calls.append(a))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-not-a-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    with pytest.raises(SystemExit) as e:
        st.main(["text", str(msg), "--env", str(tmp_path / "none.env")])
    assert e.value.code and calls == []


def test_good_text_is_one_sendmessage(tmp_path, monkeypatch):
    msg = tmp_path / "approval.txt"
    msg.write_text("כל הנכסים:\nhttps://youtu.be/AbCdEfGhIjK\nsent by Grokbot\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(st, "call", lambda tok, method, fields: calls.append((method, dict(fields))) or {"message_id": 7})
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-not-a-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.chdir(tmp_path)
    st.main(["text", str(msg), "--env", str(tmp_path / "none.env")])
    assert [m for m, _ in calls] == ["sendMessage"]
    assert calls[0][1]["text"].endswith("sent by Grokbot")
