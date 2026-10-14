"""Telegram may accept a video even if its upload response is lost."""
from types import SimpleNamespace
from unittest.mock import patch
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import send_telegram


def test_upload_does_not_automatically_repeat_an_ambiguous_post():
    with patch.object(send_telegram.subprocess, "run", return_value=SimpleNamespace(stdout='{"ok":true,"result":{"message_id":74}}', stderr="")) as run:
        assert send_telegram.call("test-token", "sendVideo", [("video","@clip.mp4")])["message_id"] == 74
    args = run.call_args.args[0]
    assert "--http1.1" in args and "--retry" not in args
    assert args[args.index("--connect-timeout") + 1] == "20"
    assert args[args.index("--max-time") + 1] == "180"


def test_failed_transport_does_not_expose_bot_token_in_error():
    with patch.object(send_telegram.subprocess, "run", return_value=SimpleNamespace(stdout="", stderr="failed URL botsecret-token/sendVideo")):
        with pytest.raises(SystemExit) as error:
            send_telegram.call("secret-token", "sendVideo", [])
    assert "secret-token" not in str(error.value)
    assert "[redacted]" in str(error.value)
