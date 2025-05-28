import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.sql.models import Base, Artist, Album, Song
import mongoengine
from db.nosql.collections import Fingerprint
import mongomock

@pytest.fixture(scope="module")
def sqlite_session():
    # Create in-memory SQLite database and tables
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    # Teardown: close session and drop all tables
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="module", autouse=True)
def mongo_connection():
    # Use mongomock for an in-memory MongoDB instance
    mongoengine.connect(
        db="testdb",
        host="mongodb://localhost",
        mongo_client_class=mongomock.MongoClient #
    )
    yield
    Fingerprint.drop_collection()
    mongoengine.disconnect()

def test_sql_models_relationships(sqlite_session):
    # Create an artist
    artist = Artist(name="Test Artist")
    sqlite_session.add(artist)
    sqlite_session.commit()

    # Create an album linked to that artist
    album = Album(title="Test Album", artist_id=artist.id)
    sqlite_session.add(album)
    sqlite_session.commit()

    # Create a song linked to both artist and album
    song = Song(title="Test Song", duration=300, artist_id=artist.id, album_id=album.id)
    sqlite_session.add(song)
    sqlite_session.commit()

    # Refresh instances to load relationships
    sqlite_session.refresh(artist)
    sqlite_session.refresh(album)

    # Verify that relationships work as expected
    assert len(artist.songs) == 1
    assert artist.songs[0].title == "Test Song"
    assert len(album.songs) == 1
    assert album.songs[0].title == "Test Song"
    assert len(artist.albums) == 1
    assert artist.albums[0].title == "Test Album"

def test_nosql_fingerprint_model_and_indexes():
    # Save a fingerprint document
    fp = Fingerprint(song_id=42, hash="hashvalue123")
    fp.save()

    # Retrieve and verify fields
    fetched = Fingerprint.objects.first()
    assert fetched.song_id == 42
    assert fetched.hash == "hashvalue123"

    # Verify that indexes exist on 'hash' and 'song_id'
    index_info = Fingerprint._get_collection().index_information()
    index_fields = [
        tuple(field for field, _ in info["key"])
        for info in index_info.values()
    ]
    assert any("hash" in fields for fields in index_fields)
    assert any("song_id" in fields for fields in index_fields)
