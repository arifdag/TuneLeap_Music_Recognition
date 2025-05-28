from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

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
