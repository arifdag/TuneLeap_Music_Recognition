from pydantic import BaseModel, Field, ConfigDict # Ensure Field and ConfigDict are imported
from typing import List, Optional
from datetime import datetime

# Assuming these files exist in the same directory (api/schemas/)
from api.schemas.user_schemas import UserResponse
from api.schemas.song_schemas import SongResponse

class PlaylistItemBase(BaseModel):
    song_id: int

class PlaylistItemCreate(PlaylistItemBase):
    pass

class PlaylistItemResponse(BaseModel):
    id: int
    added_at: datetime
    song: SongResponse
    model_config = ConfigDict(from_attributes=True)

class PlaylistBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class PlaylistCreate(PlaylistBase):
    pass

class PlaylistUpdate(PlaylistBase):
    pass

class PlaylistResponse(BaseModel):
    id: int
    user_id: int
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[PlaylistItemResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)