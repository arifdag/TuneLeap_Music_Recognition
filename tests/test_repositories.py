import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import mongomock
import mongoengine
import numpy as np

from db.nosql.collections import Fingerprint, SongFeature
from core.repository.song_repository import SongRepository
from core.repository.fingerprint_repository import FingerprintRepository
from core.repository.user_repository import UserRepository
from core.repository.song_feature_repository import SongFeatureRepository
from core.repository.history_repository import RecognitionHistoryRepository
from core.repository.playlist_repository import PlaylistRepository

from db.sql.models import Base, Artist, Album, Song, User
from api.schemas.user_schemas import UserCreate
from api.schemas.history_schemas import RecognitionHistoryCreate
from api.schemas.playlist_schemas import PlaylistCreate, PlaylistUpdate
from db.sql.models import RecognitionHistory, Playlist, PlaylistItem


@pytest.fixture(scope="module")
def sqlite_session():
    # In-memory SQLite DB; create/drop tables per module
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="module", autouse=True)
def mongo_connection():
    # In-memory MongoDB via mongomock
    mongoengine.disconnect()
    mongoengine.connect(
        db="testdb",
        host="mongodb://localhost",
        mongo_client_class=mongomock.MongoClient
    )
    yield
    Fingerprint.drop_collection()
    SongFeature.drop_collection()
    mongoengine.disconnect()


def test_song_repository_crud_and_bulk(sqlite_session):
    repo = SongRepository(sqlite_session)

    # Prepare Artist and Album for foreign-key relations
    artist = Artist(name="Artist A")
    sqlite_session.add(artist)
    sqlite_session.commit()
    album = Album(title="Album A", artist_id=artist.id)
    sqlite_session.add(album)
    sqlite_session.commit()

    # Test create()
    song = repo.create(title="Song A", artist_id=artist.id, album_id=album.id, duration=180)
    assert isinstance(song, Song)
    assert song.id is not None
    assert song.title == "Song A"

    # Test get_by_id()
    fetched = repo.get_by_id(song.id)
    assert fetched.id == song.id
    assert fetched.title == "Song A"

    # Test update()
    updated = repo.update(song, title="Song A Updated", duration=200)
    assert updated.title == "Song A Updated"
    assert updated.duration == 200

    # Test list()
    all_songs = repo.list()
    assert any(s.id == song.id for s in all_songs)

    # Test bulk_insert()
    songs_data = [
        {"title": "Bulk 1", "artist_id": artist.id, "duration": 100},
        {"title": "Bulk 2", "artist_id": artist.id, "album_id": album.id, "duration": 120},
    ]
    bulk_songs = repo.bulk_insert(songs_data)
    assert len(bulk_songs) == 2
    ids = [s.id for s in bulk_songs]
    listed = repo.list(limit=10)
    assert all(i in [s.id for s in listed] for i in ids)

    # Test delete()
    repo.delete(song)
    assert repo.get_by_id(song.id) is None


def test_fingerprint_repository_crud_and_bulk():
    repo = FingerprintRepository()

    # Test create()
    fp = repo.create(song_id=1, hash="hash_1")
    assert isinstance(fp, Fingerprint)
    fp_id = str(fp.id)

    # Test get_by_id()
    fetched = repo.get_by_id(fp_id)
    assert fetched is not None
    assert fetched.song_id == 1
    assert fetched.hash == "hash_1"

    # Test list()
    fps = repo.list()
    assert any(str(item.id) == fp_id for item in fps)

    # Test bulk_insert()
    fps_data = [
        {"song_id": 2, "hash": "hash_2"},
        {"song_id": 3, "hash": "hash_3"},
    ]
    bulk_fps = repo.bulk_insert(fps_data)
    assert len(bulk_fps) == 2
    all_ids = {str(item.id) for item in bulk_fps}
    listed = {str(item.id) for item in repo.list(limit=10)}
    assert all(i in listed for i in all_ids)

    # Test delete()
    deleted = repo.delete(fp_id)
    assert deleted is True
    assert repo.get_by_id(fp_id) is None


def test_user_repository_crud(sqlite_session):
    repo = UserRepository(sqlite_session)

    user_data = UserCreate(email="test@example.com", username="testuser", password="password123")
    
    # Test create_user
    user = repo.create_user(user_data)
    assert isinstance(user, User)
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.hashed_password != "password123"

    # Test get_user_by_id
    fetched_by_id = repo.get_user_by_id(user.id)
    assert fetched_by_id is not None
    assert fetched_by_id.id == user.id

    # Test get_user_by_email
    fetched_by_email = repo.get_user_by_email("test@example.com")
    assert fetched_by_email is not None
    assert fetched_by_email.email == "test@example.com"

    # Test get_user_by_username
    fetched_by_username = repo.get_user_by_username("testuser")
    assert fetched_by_username is not None
    assert fetched_by_username.username == "testuser"

    # Test non-existent cases
    assert repo.get_user_by_id(999) is None
    assert repo.get_user_by_email("nonexistent@example.com") is None
    assert repo.get_user_by_username("nonexistentuser") is None


def test_song_feature_repository_crud(mongo_connection):
    repo = SongFeatureRepository()

    song_id_1 = 1
    feature_vector_1 = np.array([0.1, 0.2, 0.3])
    
    # Test create_or_update (create)
    sf1 = repo.create_or_update(song_id_1, feature_vector_1)
    assert isinstance(sf1, SongFeature)
    assert sf1.song_id == song_id_1
    assert np.array_equal(np.array(sf1.feature_vector), feature_vector_1)
    original_updated_at = sf1.updated_at

    # Test get_by_song_id
    fetched_sf1 = repo.get_by_song_id(song_id_1)
    assert fetched_sf1 is not None
    assert fetched_sf1.song_id == song_id_1
    assert np.array_equal(np.array(fetched_sf1.feature_vector), feature_vector_1)

    # Test create_or_update (update)
    feature_vector_updated = np.array([0.4, 0.5, 0.6])
    sf1_updated = repo.create_or_update(song_id_1, feature_vector_updated)
    assert sf1_updated.song_id == song_id_1
    assert np.array_equal(np.array(sf1_updated.feature_vector), feature_vector_updated)
    if hasattr(sf1_updated, 'updated_at') and hasattr(original_updated_at, 'microsecond'):
         assert sf1_updated.updated_at > original_updated_at


    # Test get_all_features
    song_id_2 = 2
    feature_vector_2 = np.array([0.7, 0.8, 0.9])
    repo.create_or_update(song_id_2, feature_vector_2)
    
    all_features = repo.get_all_features()
    assert isinstance(all_features, dict)
    assert len(all_features) == 2
    assert song_id_1 in all_features
    assert song_id_2 in all_features
    assert np.array_equal(all_features[song_id_1], feature_vector_updated)
    assert np.array_equal(all_features[song_id_2], feature_vector_2)

    # Test get_by_song_id (non-existent)
    assert repo.get_by_song_id(999) is None


def test_recognition_history_repository_crud(sqlite_session):
    repo = RecognitionHistoryRepository(sqlite_session)

    # Setup: Create a User and a Song
    user = User(username="hist_user", email="hist@example.com", hashed_password="xxx")
    artist = Artist(name="Hist Artist")
    album = Album(title="Hist Album", artist=artist)
    song = Song(title="Hist Song", artist=artist, album=album, duration=180)
    sqlite_session.add_all([user, artist, album, song])
    sqlite_session.commit()

    history_data = RecognitionHistoryCreate(song_id=song.id, source="test_source")

    # Test create_recognition_event
    event = repo.create_recognition_event(history_data, user_id=user.id)
    assert isinstance(event, RecognitionHistory)
    assert event.id is not None
    assert event.song_id == song.id
    assert event.user_id == user.id
    assert event.source == "test_source"

    # Test create_recognition_event with non-existent song
    invalid_history_data = RecognitionHistoryCreate(song_id=999, source="invalid")
    assert repo.create_recognition_event(invalid_history_data, user_id=user.id) is None

    # Test get_recognition_event_by_id
    fetched_event = repo.get_recognition_event_by_id(event.id, user_id=user.id)
    assert fetched_event is not None
    assert fetched_event.id == event.id
    assert repo.get_recognition_event_by_id(event.id, user_id=user.id + 1) is None

    # Test get_recognition_history_for_user
    event2_data = RecognitionHistoryCreate(song_id=song.id, source="test_source2")
    repo.create_recognition_event(event2_data, user_id=user.id)
    
    user_history = repo.get_recognition_history_for_user(user_id=user.id, limit=5)
    assert len(user_history) == 2
    assert user_history[0].source == "test_source2"

    # Test delete_recognition_event
    assert repo.delete_recognition_event(event.id, user_id=user.id) is True
    assert repo.get_recognition_event_by_id(event.id, user_id=user.id) is None
    assert repo.delete_recognition_event(event.id, user_id=user.id) is False
    assert repo.delete_recognition_event(999, user_id=user.id) is False


def test_playlist_repository_crud_and_items(sqlite_session):
    repo = PlaylistRepository(sqlite_session)

    # Setup: Create User and Songs
    user1 = User(username="playlist_user1", email="puser1@example.com", hashed_password="xxx")
    user2 = User(username="playlist_user2", email="puser2@example.com", hashed_password="yyy")
    artist = Artist(name="Playlist Artist")
    song1 = Song(title="Playlist Song 1", artist=artist, duration=180)
    song2 = Song(title="Playlist Song 2", artist=artist, duration=200)
    sqlite_session.add_all([user1, user2, artist, song1, song2])
    sqlite_session.commit()

    playlist_data = PlaylistCreate(name="User1's Cool Playlist")

    # Test create_playlist
    playlist = repo.create_playlist(playlist_data, user_id=user1.id)
    assert isinstance(playlist, Playlist)
    assert playlist.id is not None
    assert playlist.name == "User1's Cool Playlist"
    assert playlist.user_id == user1.id

    # Test get_playlist_by_id
    fetched_playlist = repo.get_playlist_by_id(playlist.id)
    assert fetched_playlist is not None
    assert fetched_playlist.name == playlist.name

    # Test get_playlists_by_user_id
    user1_playlists = repo.get_playlists_by_user_id(user_id=user1.id)
    assert len(user1_playlists) == 1
    assert user1_playlists[0].id == playlist.id
    assert len(repo.get_playlists_by_user_id(user_id=user2.id)) == 0

    # Test update_playlist
    update_data = PlaylistUpdate(name="User1's Awesome Playlist")
    updated_playlist = repo.update_playlist(playlist.id, update_data, user_id=user1.id)
    assert updated_playlist is not None
    assert updated_playlist.name == "User1's Awesome Playlist"
    assert repo.update_playlist(playlist.id, update_data, user_id=user2.id) is None

    # Test add_song_to_playlist
    item1 = repo.add_song_to_playlist(playlist.id, song1.id, user_id=user1.id)
    assert isinstance(item1, PlaylistItem)
    assert item1.song_id == song1.id
    assert item1.playlist_id == playlist.id
    
    # Add same song again (should return existing item or handle gracefully)
    item1_again = repo.add_song_to_playlist(playlist.id, song1.id, user_id=user1.id)
    assert item1_again is not None
    assert item1_again.id == item1.id

    # Test adding to non-existent playlist, with non-existent song, or unowned playlist
    assert repo.add_song_to_playlist(999, song1.id, user_id=user1.id) is None
    assert repo.add_song_to_playlist(playlist.id, 999, user_id=user1.id) is None
    assert repo.add_song_to_playlist(playlist.id, song1.id, user_id=user2.id) is None

    # Test remove_song_from_playlist
    assert repo.remove_song_from_playlist(playlist.id, song1.id, user_id=user1.id) is True
    sqlite_session.refresh(playlist)
    assert song1 not in [item.song for item in playlist.items]
    assert repo.remove_song_from_playlist(playlist.id, song1.id, user_id=user1.id) is False
    assert repo.remove_song_from_playlist(playlist.id, song1.id, user_id=user2.id) is False

    # Test delete_playlist
    assert repo.delete_playlist(playlist.id, user_id=user1.id) is True
    assert repo.get_playlist_by_id(playlist.id) is None
    assert repo.delete_playlist(playlist.id, user_id=user1.id) is False
    assert repo.delete_playlist(999, user_id=user1.id) is False
