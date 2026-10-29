import face_score as fs

BASE = {"ear": 0.27, "pitch": 4.0}


def face(**kw):
    f = {k: 0.0 for k in fs.BLEND_KEYS}
    f.update(yaw=0.0, pitch=5.0, earL=0.26, earR=0.26, irisXL=0.62, irisXR=0.38,
             mouthOpenRatio=0.22, mouthWidth=0.48, sharp=250.0,
             mouthSmileLeft=0.85, mouthSmileRight=0.85, mouthUpperUpLeft=0.2, mouthUpperUpRight=0.2,
             jawOpen=0.25, eyeBlinkLeft=0.25, eyeBlinkRight=0.25)
    f.update(kw)
    return f


GOOD = face()


def test_real_smile_beats_neutral():
    assert fs.score(GOOD, BASE) > fs.score(face(mouthSmileLeft=0, mouthSmileRight=0,
                                                mouthUpperUpLeft=0, mouthUpperUpRight=0), BASE)


def test_eyes_turned_away_lose():
    assert fs.score(face(irisXL=0.70, irisXR=0.48), BASE) < fs.score(GOOD, BASE) - 0.3


def test_wide_eyed_stare_loses():
    assert fs.score(face(earL=0.34, earR=0.34), BASE) < fs.score(GOOD, BASE) - 0.3


def test_blink_and_shut_eyes_lose():
    assert fs.score(face(eyeBlinkLeft=0.8, eyeBlinkRight=0.8), BASE) < fs.score(GOOD, BASE) - 0.5
    assert fs.score(face(earL=0.12, earR=0.12), BASE) < fs.score(GOOD, BASE) - 0.5


def test_smile_squint_is_not_a_blink():
    # a real smile narrows the eyes; that alone must not be punished as "shut"
    assert fs.parts(face(earL=0.2, earR=0.2), BASE)["eyes_shut"] == 0


def test_head_down_and_lowered_brows_lose():
    assert fs.score(face(pitch=11.0, browDownLeft=0.22, browDownRight=0.22), BASE) < fs.score(GOOD, BASE) - 0.5


def test_odd_mouths_lose():
    for bad in (dict(mouthStretchLeft=0.14, mouthStretchRight=0.12), dict(mouthPucker=0.2),
                dict(mouthSmileLeft=0.9, mouthSmileRight=0.6), dict(jawOpen=0.6)):
        assert fs.score(face(**bad), BASE) < fs.score(GOOD, BASE) - 0.15, bad


def test_slight_turn_is_free_big_turn_costs():
    assert fs.parts(face(yaw=4.0), BASE)["turned"] == 0
    assert fs.parts(face(yaw=25.0), BASE)["turned"] < -0.4


def test_pick_spacing():
    got = fs.pick([(1.0, 10), (0.9, 20), (0.8, 50), (0.7, 90)], 3, 30)
    assert [t for _, t in got] == [10, 50, 90]


def test_baseline_medians():
    b = fs.baseline([face(earL=0.2, earR=0.2, pitch=1), face(pitch=3), face(earL=0.3, earR=0.3, pitch=9)])
    assert b == {"ear": 0.26, "pitch": 3}
