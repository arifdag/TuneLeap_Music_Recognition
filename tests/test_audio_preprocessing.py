import os
import numpy as np
import pytest
import librosa
from io import BytesIO
from fastapi import UploadFile

from core.io.recording import save_temp
from core.preprocess.audio import normalize, resample

@pytest.fixture
def dummy_wav_file(tmp_path):
    # create a minimal WAV-like byte stream
    data = b"RIFF....WAVEfmt "  # just header bytes
    upload = UploadFile(filename="test.wav", file=BytesIO(data))
    return upload, data, tmp_path

def test_save_temp_writes_file(dummy_wav_file):
    upload, raw_bytes, tmp_path = dummy_wav_file
    path = save_temp(upload, dir=str(tmp_path))
    assert os.path.isfile(path)
    with open(path, "rb") as f:
        content = f.read()
    assert content == raw_bytes
    os.remove(path)

def test_normalize_rms_to_one():
    # create a constant signal with RMS = 2.0
    x = np.ones(1000, dtype=float) * 2.0
    y = normalize(x)
    rms = np.sqrt(np.mean(np.square(y)))
    assert pytest.approx(rms, rel=1e-3) == 1.0

def test_resample_changes_rate():
    orig_sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(orig_sr * duration), endpoint=False)
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)
    target_sr = 22050

    y = resample(signal, orig_sr, target_sr)
    expected_len = int(len(signal) * target_sr / orig_sr)
    assert abs(len(y) - expected_len) <= 1
    assert np.isfinite(y).all()
