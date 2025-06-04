from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)

    # Relationship: an artist can have many songs
    songs = relationship("Song", back_populates="artist")


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    release_date = Column(DateTime, nullable=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)

    # Relationship: an album belongs to one artist
    artist = relationship("Artist", back_populates="albums")
    # Relationship: an album can contain many songs
    songs = relationship("Song", back_populates="album")


# Define reverse relationship on Artist for albums
Artist.albums = relationship("Album", back_populates="artist")


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    duration = Column(Integer, nullable=True)  # duration in seconds
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=True)

    # Relationship: each song is created by one artist
    artist = relationship("Artist", back_populates="songs")
    # Relationship: each song may belong to one album
    album = relationship("Album", back_populates="songs")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True) # Optional username
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    # Add created_at, updated_at if desired

    playlists = relationship("Playlist", back_populates="owner")

class Playlist(Base):
    __tablename__ = "playlists"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User") # Add back_populates="playlists" to User.playlists if defined
    items = relationship("PlaylistItem", back_populates="playlist", cascade="all, delete-orphan")

class PlaylistItem(Base):
    __tablename__ = "playlist_items"
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False) # Link to your Song model
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    playlist = relationship("Playlist", back_populates="items")
    song = relationship("Song") # Assuming Song model exists and is appropriate

class RecognitionHistory(Base):
    __tablename__ = "recognition_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False, index=True)
    recognized_at = Column(DateTime(timezone=True), server_default=func.now())
    client_info = Column(String(255), nullable=True) # e.g., app version, device type
    source = Column(String(100), nullable=True) # Added source field

    user = relationship("User") 
    song = relationship("Song")
