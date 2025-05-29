import os
import pytest
import numpy as np
import mongoengine
import mongomock
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.sql.models import Base, Artist, Album, Song
from db.nosql.collections import Fingerprint
from api.v1.recognition import router
from db.sql.database import get_db
from core.fingerprint.extractor import extract_fingerprint
from scipy.io.wavfile import write as wav_write


@pytest.fixture(scope="module")
def sqlite_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="module", autouse=True)
def mongo_connection():
    mongoengine.connect(
        db="testdb",
        host=None,
        mongo_client_class=mongomock.MongoClient
    )
    yield
    Fingerprint.drop_collection()
    mongoengine.disconnect()


@pytest.fixture(scope="module")
def client(sqlite_db):
    app = FastAPI()
    app.include_router(router)

    # override get_db to use in-memory sqlite
    def override_get_db():
        try:
            yield sqlite_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _make_tone(tmp_path, sr=22050, freq=440, duration=1.0):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * freq * t)
    path = tmp_path / "tone.wav"
    wav_write(str(path), sr, (y * 32767).astype(np.int16))
    return str(path), sr


def test_recognize_no_match(client, tmp_path):
    # send a file with no stored fingerprint
    dummy = tmp_path / "empty.wav"
    dummy.write_bytes(b"RIFF....WAVEfmt ")
    with open(str(dummy), "rb") as f:
        resp = client.post("/recognize/", files={"file": ("empty.wav", f, "audio/wav")})
    assert resp.status_code == 404


def test_recognize_with_match(client, sqlite_db, tmp_path):
    # set up a song in SQL
    artist = Artist(name="Artist X")
    sqlite_db.add(artist);
    sqlite_db.commit()
    song = Song(title="Song X", artist_id=artist.id)
    sqlite_db.add(song);
    sqlite_db.commit()

    # generate a tone and its fingerprint
    file_path, sr = _make_tone(tmp_path)
    hash_val = extract_fingerprint(file_path, sr=sr)
    # insert into Mongo
    Fingerprint(song_id=song.id, hash=hash_val).save()

    # POST the same file
    with open(file_path, "rb") as f:
        resp = client.post("/recognize/", files={"file": ("tone.wav", f, "audio/wav")})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data and len(data["results"]) == 1
    result = data["results"][0]
    assert result["song_id"] == song.id
    assert result["probability"] == 1.0
