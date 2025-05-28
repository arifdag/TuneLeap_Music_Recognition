import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import mongomock
import mongoengine
from db.nosql.collections import Fingerprint
from core.repository.song_repository import SongRepository
from core.repository.fingerprint_repository import FingerprintRepository
from db.sql.models import Base, Artist, Album, Song


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
    mongoengine.connect(
        db="testdb",
        host="mongodb://localhost",
        mongo_client_class=mongomock.MongoClient
    )
    yield
    Fingerprint.drop_collection()
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
