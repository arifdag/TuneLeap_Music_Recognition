from typing import List, Optional, Dict, Any, Type
from sqlalchemy.orm import Session

from db.sql.models import Song


class SongRepository:
    """
    Repository for Song model: provides CRUD and bulk-insert operations.
    """

    def __init__(self, session: Session):
        """
        :param session: SQLAlchemy Session instance
        """
        self.session = session

    def create(
        self,
        title: str,
        artist_id: int,
        album_id: Optional[int] = None,
        duration: Optional[int] = None,
    ) -> Song:
        """
        Create a new Song record.
        """
        song = Song(
            title=title,
            artist_id=artist_id,
            album_id=album_id,
            duration=duration,
        )
        self.session.add(song)
        self.session.commit()
        self.session.refresh(song)
        return song

    def get_by_id(self, song_id: int) -> Optional[Song]:
        """
        Retrieve a Song by its primary key.
        """
        return self.session.query(Song).filter(Song.id == song_id).one_or_none()

    def list(
        self, skip: int = 0, limit: int = 100
    ) -> list[Type[Song]]:
        """
        List songs with pagination.
        """
        return (
            self.session.query(Song)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, song: Song, **kwargs: Any) -> Song:
        """
        Update fields of an existing Song.
        """
        for attr, value in kwargs.items():
            setattr(song, attr, value)
        self.session.commit()
        self.session.refresh(song)
        return song

    def delete(self, song: Song) -> None:
        """
        Delete a Song record.
        """
        self.session.delete(song)
        self.session.commit()

    def bulk_insert(
        self, songs_data: List[Dict[str, Any]]
    ) -> List[Song]:
        """
        Bulk-insert multiple songs. Each dict should have keys:
        'title', 'artist_id', optional 'album_id', 'duration'.
        """
        objects = [Song(**data) for data in songs_data]
        # Use add_all so that each object is attached to the session
        self.session.add_all(objects)
        self.session.commit()
        return objects
