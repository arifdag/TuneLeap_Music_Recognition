from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
import numpy as np

from core.reco.builder import PlaylistBuilder
from db.sql.database import get_db
from core.repository.song_repository import SongRepository
from db.sql.models import Song

router = APIRouter(prefix="/recommend", tags=["playlists"])

# In production, you would load or compute feature_map from your storage (e.g., a table of precomputed features).
# Here, we use a simple in-memory placeholder; replace with real data loading logic.
_feature_map: Dict[int, np.ndarray] = {}

def get_builder() -> PlaylistBuilder:
    """
    Dependency that returns a PlaylistBuilder.
    Real implementation should load feature_map from persistent storage.
    """
    return PlaylistBuilder(_feature_map)

@router.get("/{song_id}", response_model=List[int])
def recommend_song(
    song_id: int,
    top_n: int = 5,
    builder: PlaylistBuilder = Depends(get_builder),
):
    """
    Given a song_id, return top_n recommended song IDs.
    """
    recommendations = builder.build(song_id, top_n=top_n)
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found or missing features.")
    return recommendations
