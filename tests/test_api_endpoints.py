import os
import pytest
import numpy as np

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


from db.sql.models import Base, Artist, Album, Song
from db.nosql.collections import Fingerprint
from api.main import app as main_app
from api.v1.songs import router as songs_router
from api.v1.recognition import router as recog_router
from api.v1.playlists import router as rec_router, playlist_router
from db.sql.database import get_db
from core.fingerprint.extractor import extract_fingerprint
from scipy.io.wavfile import write as wav_write
import mongoengine
import mongomock


# ---------- Fixtures for DB ----------------

@pytest.fixture(scope="module")
def sqlite_session():
    """
    Create an in-memory SQLite DB and override get_db.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="module", autouse=True)
def mongo_connection():
    """
    Connect to mongomock in-memory.
    """
    mongoengine.disconnect(alias="default")  # Disconnect if already connected
    mongoengine.connect(
        db="testdb",
        host=None,  # Ensures mongomock is used
        mongo_client_class=mongomock.MongoClient,
        alias="default"  # Explicitly use the default alias
    )
    yield
    mongoengine.disconnect(alias="default")

@pytest.fixture(scope="module", autouse=True)
def override_get_db(sqlite_session):
    """
    Monkey-patch FastAPI dependency.
    """
    def _get_db_override():
        try:
            yield sqlite_session
        finally:
            pass

    main_app.dependency_overrides[get_db] = _get_db_override
    yield
    main_app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def client():
    """
    Create a TestClient with all routers included.
    """
    return TestClient(main_app)

# ---------- Helper to create a temporary WAV ----------

def _make_tone(tmp_path, sr=22050, freq=440, duration=1.0):
    """
    Generate a 1-second sine wave and write as WAV.
    """
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * freq * t)
    path = tmp_path / "tone.wav"
    wav_write(str(path), sr, (y * 32767).astype(np.int16))
    return str(path), sr

# ---------- Tests ----------

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_get_song_not_found(client):
    resp = client.get("/songs/1")
    assert resp.status_code == 404

def test_get_song_success(client, sqlite_session):
    # Insert artist, album, song
    artist = Artist(name="Artist A")
    sqlite_session.add(artist)
    sqlite_session.commit()
    album = Album(title="Album A", artist_id=artist.id)
    sqlite_session.add(album)
    sqlite_session.commit()
    song = Song(title="Song A", duration=200, artist_id=artist.id, album_id=album.id)
    sqlite_session.add(song)
    sqlite_session.commit()

    resp = client.get(f"/songs/{song.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == song.id
    assert data["title"] == "Song A"
    assert data["artist_id"] == artist.id
    assert data["album_id"] == album.id
    assert data["duration"] == 200

def test_recognize_no_match(client, tmp_path):
    # No fingerprints exist
    dummy = tmp_path / "empty.wav"
    dummy.write_bytes(b"RIFF....WAVEfmt ")
    with open(str(dummy), "rb") as f:
        resp = client.post("/recognize/", files={"file": ("empty.wav", f, "audio/wav")})
    assert resp.status_code == 404

def test_recognize_with_match(client, sqlite_session, tmp_path):
    # Setup SQL song and one fingerprint
    artist = Artist(name="Artist X")
    sqlite_session.add(artist); sqlite_session.commit()
    song = Song(title="Song X", artist_id=artist.id)
    sqlite_session.add(song); sqlite_session.commit()

    # Create tone file and fingerprint
    file_path, sr = _make_tone(tmp_path)
    fp_hash = extract_fingerprint(file_path, sr=sr)
    Fingerprint(song_id=song.id, hash=fp_hash).save()

    # Send same file
    with open(file_path, "rb") as f:
        resp = client.post("/recognize/", files={"file": ("tone.wav", f, "audio/wav")})
    assert resp.status_code == 200
    result = resp.json()
    assert "results" in result and len(result["results"]) == 1
    entry = result["results"][0]
    assert entry["song_id"] == song.id
    assert entry["probability"] == 1.0

def test_auto_playlist_not_found(client, monkeypatch):
    # No songs inserted, so seed not found

    # Monkeypatch to simulate a successfully loaded feature map
    # that is non-empty (to satisfy get_builder) but does not contain seed_song_id=1
    monkeypatch.setattr("api.v1.playlists._feature_map_cache", {999: np.array([0.0])}) # Non-empty, but no song_id 1
    monkeypatch.setattr("api.v1.playlists._feature_map_loaded", True)

    resp = client.post("/playlist/auto", params={"seed_song_id": 1, "top_n": 3})
    assert resp.status_code == 404

def test_auto_playlist_success(client, sqlite_session, tmp_path, monkeypatch):
    # Insert two songs so one can be recommended
    artist = Artist(name="Artist Y")
    sqlite_session.add(artist); sqlite_session.commit()
    song1 = Song(title="Song Y1", artist_id=artist.id)
    song2 = Song(title="Song Y2", artist_id=artist.id)
    sqlite_session.add_all([song1, song2]); sqlite_session.commit()

    # Monkey-patch feature_map to be deterministic
    test_feature_map_cache = {
        song1.id: np.array([1.0, 0.0]),
        song2.id: np.array([0.9, 0.1])
    }
    monkeypatch.setattr("api.v1.playlists._feature_map_cache", test_feature_map_cache)
    monkeypatch.setattr("api.v1.playlists._feature_map_loaded", True)

    resp = client.post("/playlist/auto", params={"seed_song_id": song1.id, "top_n": 1})
    assert resp.status_code == 200
    result = resp.json()
    # Only one recommendation: song2
    assert result == [song2.id]

# Clean up after all tests
@pytest.fixture(scope="module", autouse=True)
def teardown(tmp_path_factory):
    yield
    Fingerprint.drop_collection()