from sqlalchemy.orm import Session
from typing import List, Optional
from db.sql.models import Playlist, PlaylistItem, Song, User
from api.schemas.playlist_schemas import PlaylistCreate, PlaylistUpdate

class PlaylistRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_playlist(self, playlist_data: PlaylistCreate, user_id: int) -> Playlist:
        db_playlist = Playlist(**playlist_data.dict(), user_id=user_id)
        self.session.add(db_playlist)
        self.session.commit()
        self.session.refresh(db_playlist)
        return db_playlist

    def get_playlist_by_id(self, playlist_id: int) -> Optional[Playlist]:
        return self.session.query(Playlist).filter(Playlist.id == playlist_id).first()

    def get_playlists_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Playlist]:
        return (
            self.session.query(Playlist)
            .filter(Playlist.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_playlist(self, playlist_id: int, playlist_data: PlaylistUpdate, user_id: int) -> Optional[Playlist]:
        db_playlist = self.session.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == user_id).first()
        if db_playlist:
            db_playlist.name = playlist_data.name
            self.session.commit()
            self.session.refresh(db_playlist)
        return db_playlist

    def delete_playlist(self, playlist_id: int, user_id: int) -> bool:
        db_playlist = self.session.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == user_id).first()
        if db_playlist:
            self.session.delete(db_playlist)
            self.session.commit()
            return True
        return False

    def add_song_to_playlist(self, playlist_id: int, song_id: int, user_id: int) -> Optional[PlaylistItem]:
        # Check if playlist exists and belongs to user
        db_playlist = self.session.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == user_id).first()
        if not db_playlist:
            return None
        # Check if song exists
        db_song = self.session.query(Song).filter(Song.id == song_id).first()
        if not db_song:
            return None # Or raise specific exception

        # Check if song already in playlist
        existing_item = self.session.query(PlaylistItem).filter_by(playlist_id=playlist_id, song_id=song_id).first()
        if existing_item:
            return existing_item # Or raise exception: "Song already in playlist"

        db_item = PlaylistItem(playlist_id=playlist_id, song_id=song_id)
        self.session.add(db_item)
        self.session.commit()
        self.session.refresh(db_item)
        return db_item

    def remove_song_from_playlist(self, playlist_id: int, song_id: int, user_id: int) -> bool:
        # Check if playlist exists and belongs to user for authorization
        db_playlist = self.session.query(Playlist).filter(Playlist.id == playlist_id, Playlist.user_id == user_id).first()
        if not db_playlist:
            return False

        db_item = self.session.query(PlaylistItem).filter(PlaylistItem.playlist_id == playlist_id, PlaylistItem.song_id == song_id).first()
        if db_item:
            self.session.delete(db_item)
            self.session.commit()
            return True
        return False