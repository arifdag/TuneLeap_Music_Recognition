from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from .song_schemas import SongResponse # Assuming SongResponse is Pydantic V2 compatible

class RecognitionHistoryBase(BaseModel):
    song_id: int
    client_info: Optional[str] = None
    source: Optional[str] = None

class RecognitionHistoryCreate(RecognitionHistoryBase):
    pass

class RecognitionHistoryResponse(RecognitionHistoryBase):
    id: int
    user_id: int
    recognized_at: datetime
    song: SongResponse # Embed full song details

    model_config = ConfigDict(from_attributes=True) # Pydantic V2