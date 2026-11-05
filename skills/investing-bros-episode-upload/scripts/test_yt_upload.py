"""yt_upload.py with a fake YouTube client: Private only, show channel only, one insert per asset version,
and --resume finishes on the same video after a failure."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import yt_upload as yu  # noqa: E402


class Call:
    def __init__(self, fn):
        self.fn = fn

    def execute(self):
        return self.fn()


class FakeInsert:
    def __init__(self, vid):
        self.vid, self.done = vid, False

    def next_chunk(self):
        return None, {"id": self.vid}


class FakeYT:
    def __init__(self, channel=yu.SHOW_CHANNEL_ID, fail_thumbnail=0):
        self.channel, self.fail_thumbnail = channel, fail_thumbnail
        self.inserts, self.bodies, self.thumbs, self.playlists = 0, [], [], []

    def channels(self):
        outer = self

        class C:
            def list(self, **kw):
                return Call(lambda: {"items": [{"id": outer.channel, "snippet": {"title": "x"}}]})
        return C()

    def videos(self):
        outer = self

        class V:
            def insert(self, part, body, media_body):
                outer.inserts += 1
                outer.bodies.append(body)
                return FakeInsert(f"VID{outer.inserts:08d}")
        return V()

    def thumbnails(self):
        outer = self

        class T:
            def set(self, videoId, media_body):
                def run():
                    if outer.fail_thumbnail:
                        outer.fail_thumbnail -= 1
                        raise ValueError("thumbnail rejected")  # not retryable: the run fails after the insert
                    outer.thumbs.append(videoId)
                    return {}
                return Call(run)
        return T()

    def playlistItems(self):
        outer = self

        class P:
            def insert(self, part, body):
                return Call(lambda: outer.playlists.append(body["snippet"]["resourceId"]["videoId"]) or {})
        return P()


@pytest.fixture(autouse=True)
def no_google(monkeypatch):
    monkeypatch.setattr(yu, "media", lambda path, resumable=False: path)


def files(tmp_path, content=b"video-v1"):
    v = tmp_path / "ep.mp4"
    v.write_bytes(content)
    t = tmp_path / "thumb.jpg"
    t.write_bytes(b"jpg")
    return v, t, tmp_path / "extras/uploads/main.json"


def args(v, t, rec, *extra):
    return [str(v), "--title", "פרק 11 - x", "--asset", "main", "--record", str(rec), "--thumbnail", str(t), *extra]


def test_privacy_is_private_only():
    with pytest.raises(SystemExit):
        yu.parser().parse_args(["x.mp4", "--privacy", "public"])
    with pytest.raises(SystemExit):
        yu.parser().parse_args(["x.mp4", "--privacy", "unlisted"])


def test_upload_needs_asset_and_record(tmp_path):
    v, t, rec = files(tmp_path)
    with pytest.raises(SystemExit):
        yu.main([str(v), "--title", "x"], yt=FakeYT())


def test_refuses_another_channel(tmp_path):
    v, t, rec = files(tmp_path)
    yt = FakeYT(channel="UCj9n6mOn7uWpN8G51nPggfA")
    assert yu.main(args(v, t, rec), yt=yt) == 1
    assert yt.inserts == 0 and not rec.exists()


def test_record_written_and_private(tmp_path):
    v, t, rec = files(tmp_path)
    yt = FakeYT()
    assert yu.main(args(v, t, rec), yt=yt) == 0
    r = json.loads(rec.read_text())
    assert r["video_id"] == "VID00000001" and r["channel"] == yu.SHOW_CHANNEL_ID
    assert r["steps_done"] == ["insert", "thumbnail"] and r["version"] == yu.sha256_file(v)
    assert yt.bodies[0]["status"]["privacyStatus"] == "private"


def test_failure_after_insert_then_retry_never_inserts_twice(tmp_path):
    v, t, rec = files(tmp_path)
    yt = FakeYT(fail_thumbnail=1)
    assert yu.main(args(v, t, rec, "--playlist", "PL1"), yt=yt) == 1      # inserted, then the thumbnail failed
    r = json.loads(rec.read_text())
    assert yt.inserts == 1 and r["steps_done"] == ["insert"]
    assert yu.main(args(v, t, rec, "--playlist", "PL1"), yt=yt) == 1      # the same command again: refused
    assert yt.inserts == 1
    assert yu.main(["--resume", str(rec)], yt=yt) == 0                    # finishes on the same video
    r = json.loads(rec.read_text())
    assert yt.inserts == 1 and yt.thumbs == ["VID00000001"] and yt.playlists == ["VID00000001"]
    assert r["steps_done"] == ["insert", "thumbnail", "playlist"]


def test_replace_records_the_old_id(tmp_path):
    v, t, rec = files(tmp_path)
    yt = FakeYT()
    yu.main(args(v, t, rec), yt=yt)
    assert yu.main(args(v, t, rec, "--replace"), yt=yt) == 0
    r = json.loads(rec.read_text())
    assert yt.inserts == 2 and r["video_id"] == "VID00000002"
    assert [s["video_id"] for s in r["superseded"]] == ["VID00000001"]


def test_new_version_is_a_reupload_with_superseded(tmp_path):
    v, t, rec = files(tmp_path)
    yt = FakeYT()
    yu.main(args(v, t, rec), yt=yt)
    v.write_bytes(b"video-v2")                                             # a fixed master
    assert yu.main(args(v, t, rec), yt=yt) == 0
    r = json.loads(rec.read_text())
    assert r["video_id"] == "VID00000002" and r["superseded"][0]["video_id"] == "VID00000001"


def test_source_is_the_version_of_a_compressed_copy(tmp_path):
    v, t, rec = files(tmp_path, b"compressed")
    master = tmp_path / "master.mp4"
    master.write_bytes(b"master-v1")
    yt = FakeYT()
    assert yu.main(args(v, t, rec, "--source", str(master)), yt=yt) == 0
    r = json.loads(rec.read_text())
    assert r["version"] == r["source_sha256"] == yu.sha256_file(master) and r["file_sha256"] == yu.sha256_file(v)
    v.write_bytes(b"compressed again")                                     # a new copy of the same master
    assert yu.main(args(v, t, rec, "--source", str(master)), yt=yt) == 1   # same version: refused
    assert yt.inserts == 1


def test_resume_without_a_record_refuses(tmp_path):
    yt = FakeYT()
    assert yu.main(["--resume", str(tmp_path / "none.json")], yt=yt) == 1
    assert yt.inserts == 0


def test_record_of_another_asset_refuses(tmp_path):
    v, t, rec = files(tmp_path)
    yt = FakeYT()
    yu.main(args(v, t, rec), yt=yt)
    other = [str(v), "--title", "x", "--asset", "seg01", "--record", str(rec)]
    assert yu.main(other, yt=yt) == 1 and yt.inserts == 1
