import os
import pytest
import numpy as np
import mongoengine
import mongomock
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
import io

from db.sql.models import Base, Artist, Album, Song
from db.nosql.collections import Fingerprint
from api.v1.recognition import router
from db.sql.database import get_db
from core.fingerprint.extractor import extract_fingerprint
from scipy.io.wavfile import write as wav_write
from api.main import app
from core.fingerprint.matcher import FingerprintMatcher


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
    mongoengine.disconnect()  # Disconnect if already connected
    mongoengine.connect(
        "testdb",
        host="mongodb://localhost",
        mongo_client_class=mongomock.MongoClient,
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


@pytest.fixture
def mock_audio_file():
    # Create a mock audio file for testing
    return {"file": ("test_audio.wav", io.BytesIO(b"mock audio content"), "audio/wav")}

@pytest.fixture
def mock_db_session():
    # Mock the database session
    mock_session = MagicMock()
    return mock_session

def test_recognize_audio_not_found(client, mock_audio_file):
    # Mock the fingerprint extraction and matching to return no matches
    with patch("api.v1.recognition.extract_fingerprint") as mock_extract:
        with patch("api.v1.recognition.FingerprintMatcher") as mock_matcher_class:
            # Configure mocks
            mock_extract.return_value = "mock_fingerprint"
            
            mock_matcher = MagicMock()
            mock_matcher.match.return_value = {}  # No matches found
            mock_matcher_class.return_value = mock_matcher
            
            # Save temp file mock
            with patch("api.v1.recognition.save_temp") as mock_save:
                mock_save.return_value = "temp_path"
                
                # Mock os path exists and remove
                with patch("os.path.exists") as mock_exists:
                    with patch("os.remove") as mock_remove:
                        mock_exists.return_value = True
                        
                        # Make the request
                        response = client.post("/recognize/", files=mock_audio_file)
                        
                        # Assert response
                        assert response.status_code == 404
                        assert response.json() == {"detail": "No match found"}

def test_recognize_audio_with_match(client, mock_audio_file):
    # Mock the fingerprint extraction and matching to return matches
    with patch("api.v1.recognition.extract_fingerprint") as mock_extract:
        with patch("api.v1.recognition.FingerprintMatcher") as mock_matcher_class:
            with patch("api.v1.recognition.SongRepository") as mock_repo_class:
                # Configure mocks
                mock_extract.return_value = "mock_fingerprint"
                
                mock_matcher = MagicMock()
                mock_matcher.match.return_value = {1: 10, 2: 5}  # Two matches with counts
                mock_matcher_class.return_value = mock_matcher
                
                mock_repo = MagicMock()
                mock_song1 = MagicMock()
                mock_song1.title = "Test Song 1"
                mock_song1.artist_id = 100
                mock_song1.album_id = 200
                
                mock_song2 = MagicMock()
                mock_song2.title = "Test Song 2"
                mock_song2.artist_id = 101
                mock_song2.album_id = 201
                
                mock_repo.get_by_id.side_effect = lambda id: {1: mock_song1, 2: mock_song2}.get(id)
                mock_repo_class.return_value = mock_repo
                
                # Save temp file mock
                with patch("api.v1.recognition.save_temp") as mock_save:
                    mock_save.return_value = "temp_path"
                    
                    # Mock os path exists and remove
                    with patch("os.path.exists") as mock_exists:
                        with patch("os.remove") as mock_remove:
                            mock_exists.return_value = True
                            
                            # Make the request
                            response = client.post("/recognize/", files=mock_audio_file)
                            
                            # Assert response
                            assert response.status_code == 200
                            response_data = response.json()
                            assert "results" in response_data
                            
                            # Check that we have two results with correct probabilities
                            results = response_data["results"]
                            assert len(results) == 2
                            
                            # Total matches = 15 (10+5)
                            # First song should have 10/15 = 0.6667 probability
                            # Second song should have 5/15 = 0.3333 probability
                            first_result = next(r for r in results if r["song_id"] == 1)
                            second_result = next(r for r in results if r["song_id"] == 2)
                            
                            assert first_result["probability"] == 10/15
                            assert first_result["title"] == "Test Song 1"
                            assert first_result["artist_id"] == 100
                            assert first_result["album_id"] == 200
                            
                            assert second_result["probability"] == 5/15
                            assert second_result["title"] == "Test Song 2"
                            assert second_result["artist_id"] == 101
                            assert second_result["album_id"] == 201
