from typing import List, Dict

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.reco.builder import PlaylistBuilder
from db.sql.database import get_db

# ---------------------------------------------------------------------
# Shared, in-memory feature map that tests (and a future loader job)
# can populate.  All endpoints read from the same dict.
# ---------------------------------------------------------------------
_feature_map: Dict[int, np.ndarray] = {}

# Routers ----------------------------------------------------------------
router = APIRouter(prefix="/recommend", tags=["recommendation"])
playlist_router = APIRouter(prefix="/playlist", tags=["playlists"])


# Dependency -------------------------------------------------------------
def get_builder() -> PlaylistBuilder:
    """Return a PlaylistBuilder wired to the global _feature_map."""
    return PlaylistBuilder(_feature_map)


# /recommend/{song_id} ---------------------------------------------------
@router.get("/{song_id}", response_model=List[int])
def recommend_song(
    song_id: int,
    top_n: int = Query(5, ge=1, le=20),
    builder: PlaylistBuilder = Depends(get_builder),
) -> List[int]:
    if song_id not in _feature_map:
        raise HTTPException(status_code=404, detail="Song not found")

    rec_ids = builder.build(song_id, top_n=top_n)
    if not rec_ids:
        raise HTTPException(status_code=404, detail="No recommendations found")

    return rec_ids


# /playlist/auto ---------------------------------------------------------
@playlist_router.post("/auto", response_model=List[int])
def auto_playlist(
    seed_song_id: int,
    top_n: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),  # injected for future use
) -> List[int]:
    # For now we work entirely from the global in-memory map that the
    # tests patch.  In production you’d populate _feature_map from your
    # feature store or model-inference pipeline.
    if seed_song_id not in _feature_map:
        raise HTTPException(status_code=404, detail="Seed song not found")

    builder = PlaylistBuilder(_feature_map)
    rec_ids = builder.build(seed_song_id, top_n=top_n)
    if not rec_ids:
        raise HTTPException(status_code=404, detail="Could not build playlist")

    return rec_ids
