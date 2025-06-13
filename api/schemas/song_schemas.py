from pydantic import BaseModel, ConfigDict
from typing import Optional

# Forward references for potentially circular dependencies with Artist/Album schemas
# if you decide to nest them later. For now, we'll keep it simple.
# from .artist_schemas import ArtistResponse  # Example if you create artist_schemas.py
# from .album_schemas import AlbumResponse   # Example if you create album_schemas.py

class SongBase(BaseModel):
    title: str
    duration: Optional[int] = None
    artist_id: int
    album_id: Optional[int] = None

class SongCreate(SongBase): # If you ever need to create songs via API
    pass

class SongUpdate(SongBase): # If you ever need to update songs via API
    pass

class SongResponse(SongBase):
    id: int
    artist_name: Optional[str] = None
    album_image: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)