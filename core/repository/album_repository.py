from typing import List, Optional, Dict, Any, Type
from sqlalchemy.orm import Session

from db.sql.models import Album


class AlbumRepository:
    """
    Repository for Album model: provides CRUD and bulk-insert operations.
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
        album_image: Optional[str] = None,
        release_date: Optional[Any] = None,
    ) -> Album:
        """
        Create a new Album record.
        """
        album = Album(
            title=title,
            artist_id=artist_id,
            album_image=album_image,
            release_date=release_date,
        )
        self.session.add(album)
        self.session.commit()
        self.session.refresh(album)
        return album

    def get_by_id(self, album_id: int) -> Optional[Album]:
        """
        Retrieve an Album by its primary key.
        """
        return self.session.query(Album).filter(Album.id == album_id).one_or_none()

    def list(
        self, skip: int = 0, limit: int = 100
    ) -> list[Type[Album]]:
        """
        List albums with pagination.
        """
        return (
            self.session.query(Album)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, album: Album, **kwargs: Any) -> Album:
        """
        Update fields of an existing Album.
        """
        for attr, value in kwargs.items():
            setattr(album, attr, value)
        self.session.commit()
        self.session.refresh(album)
        return album

    def delete(self, album: Album) -> None:
        """
        Delete an Album record.
        """
        self.session.delete(album)
        self.session.commit()

    def bulk_insert(
        self, albums_data: List[Dict[str, Any]]
    ) -> List[Album]:
        """
        Bulk-insert multiple albums. Each dict should have keys:
        'title', 'artist_id', optional 'album_image', 'release_date'.
        """
        objects = [Album(**data) for data in albums_data]
        # Use add_all so that each object is attached to the session
        self.session.add_all(objects)
        self.session.commit()
        return objects 