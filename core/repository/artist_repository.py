from typing import List, Optional, Dict, Any, Type
from sqlalchemy.orm import Session

from db.sql.models import Artist


class ArtistRepository:
    """
    Repository for Artist model: provides CRUD and bulk-insert operations.
    """

    def __init__(self, session: Session):
        """
        :param session: SQLAlchemy Session instance
        """
        self.session = session

    def create(
        self,
        name: str,
    ) -> Artist:
        """
        Create a new Artist record.
        """
        artist = Artist(name=name)
        self.session.add(artist)
        self.session.commit()
        self.session.refresh(artist)
        return artist

    def get_by_id(self, artist_id: int) -> Optional[Artist]:
        """
        Retrieve an Artist by its primary key.
        """
        return self.session.query(Artist).filter(Artist.id == artist_id).one_or_none()

    def list(
        self, skip: int = 0, limit: int = 100
    ) -> list[Type[Artist]]:
        """
        List artists with pagination.
        """
        return (
            self.session.query(Artist)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, artist: Artist, **kwargs: Any) -> Artist:
        """
        Update fields of an existing Artist.
        """
        for attr, value in kwargs.items():
            setattr(artist, attr, value)
        self.session.commit()
        self.session.refresh(artist)
        return artist

    def delete(self, artist: Artist) -> None:
        """
        Delete an Artist record.
        """
        self.session.delete(artist)
        self.session.commit()

    def bulk_insert(
        self, artists_data: List[Dict[str, Any]]
    ) -> List[Artist]:
        """
        Bulk-insert multiple artists. Each dict should have key 'name'.
        """
        objects = [Artist(**data) for data in artists_data]
        # Use add_all so that each object is attached to the session
        self.session.add_all(objects)
        self.session.commit()
        return objects 