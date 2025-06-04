import pytest
import numpy as np
import mongoengine
from scipy.io.wavfile import write
from db.nosql.collections import Fingerprint
from core.fingerprint.extractor import extract_fingerprint
from worker.tasks import store_fingerprint
import mongomock

@pytest.fixture(scope="module", autouse=True)
def mongo_connection():
    # in-memory MongoDB
    mongoengine.disconnect(alias="default")  # Disconnect if already connected
    mongoengine.connect(
        "testdb",
        host="mongodb://localhost",  # any mongodb URI is fine
        mongo_client_class=mongomock.MongoClient,
        alias="default",            # keep the usual alias
    )
    yield
    Fingerprint.drop_collection()
    mongoengine.disconnect()

def _make_tone(tmp_path, sr=22050, freq=440, duration=1.0):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * freq * t)
    path = tmp_path / "tone.wav"
    write(str(path), sr, (y * 32767).astype(np.int16))
    return str(path), sr

def test_extract_fingerprint_is_consistent(tmp_path):
    file_path, sr = _make_tone(tmp_path)
    fp1 = extract_fingerprint(file_path, sr=sr)
    fp2 = extract_fingerprint(file_path, sr=sr)
    assert isinstance(fp1, str)
    assert len(fp1) == 64
    assert fp1 == fp2

def test_store_fingerprint_creates_document(tmp_path):
    file_path, sr = _make_tone(tmp_path)
    assert Fingerprint.objects.count() == 0
    fp_id = store_fingerprint.run(file_path, song_id=7)
    doc = Fingerprint.objects.first()
    assert doc is not None
    assert doc.song_id == 7
    assert doc.hash == extract_fingerprint(file_path, sr=sr)
    assert str(doc.id) == fp_id
