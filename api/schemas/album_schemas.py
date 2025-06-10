from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# Forward declare SongResponse if needed
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .song_schemas import SongResponse
#     from .artist_schemas import ArtistResponse


class AlbumBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    release_date: Optional[datetime] = None
    artist_id: int
    album_image: Optional[str] = None

class AlbumCreate(AlbumBase):
    pass

class AlbumUpdate(AlbumBase):
    pass

class AlbumResponse(BaseModel):
    id: int
    title: str
    release_date: Optional[datetime] = None
    artist_id: int
    album_image: Optional[str] = None
    # songs: List['SongResponse'] = Field(default_factory=list) # If nesting
    model_config = ConfigDict(from_attributes=True)

# from .artist_schemas import ArtistResponse # Ensure imports are correctly placed
# from .song_schemas import SongResponse
# AlbumResponse.update_forward_refs()