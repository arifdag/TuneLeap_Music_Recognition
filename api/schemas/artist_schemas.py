from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

# Forward declare AlbumResponse and SongResponse if they are defined in other files
# and will be imported here for type hinting.
# For Pydantic V2, you might use: from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from .album_schemas import AlbumResponse
#     from .song_schemas import SongResponse

class ArtistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class ArtistCreate(ArtistBase):
    pass

class ArtistUpdate(ArtistBase):
    pass

class ArtistResponse(BaseModel): # Assuming other base/create models are defined
    id: int
    name: str
    # albums: List['AlbumResponse'] = Field(default_factory=list) # If nesting
    # songs: List['SongResponse'] = Field(default_factory=list)  # If nesting
    model_config = ConfigDict(from_attributes=True)


# from .album_schemas import AlbumResponse
# from .song_schemas import SongResponse
# ArtistResponse.update_forward_refs()