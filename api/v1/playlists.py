from typing import List, Dict
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from core.reco.builder import PlaylistBuilder
from db.sql.database import get_db
from core.repository.song_feature_repository import SongFeatureRepository
from mongoengine import connect, disconnect
import os

# --- MongoDB Connection Management ---
MONGO_URI_PLAYLISTS = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME_PLAYLISTS = os.getenv("DB_NAME", "tuneleap_db")

_feature_map_cache: Dict[int, np.ndarray] = {} # Keep as a cache
_feature_map_loaded = False

def get_feature_map_from_db() -> Dict[int, np.ndarray]:
    global _feature_map_cache, _feature_map_loaded
    if not _feature_map_loaded:
        try:
            # Ensure MongoEngine is connected for this part of the app if not globally
            # This connection logic might need to be more robust or centralized
            connect(db=DB_NAME_PLAYLISTS, host=MONGO_URI_PLAYLISTS, alias='default_playlists_api') # Use an alias if 'default' is used elsewhere
            repo = SongFeatureRepository()
            _feature_map_cache = repo.get_all_features()
            _feature_map_loaded = True
        except Exception as e:
            # Log error: print(f"Failed to load feature map: {e}")
            # Depending on strategy, could raise an error or return empty map
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Feature map not available")
        # finally:
            # disconnect(alias='default_playlists_api') # Disconnect if connection is per-request/load
    return _feature_map_cache

# Routers
router = APIRouter(prefix="/recommend", tags=["recommendation"])
playlist_router = APIRouter(prefix="/playlist", tags=["playlists"])

# Dependency
def get_builder() -> PlaylistBuilder:
    """Return a PlaylistBuilder wired to the feature_map from DB."""
    feature_map = get_feature_map_from_db()
    if not feature_map: # Handle case where map might be empty after attempted load
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Recommendation engine not ready, no features.")
    return PlaylistBuilder(feature_map)

# /recommend/{song_id}
@router.get("/{song_id}", response_model=List[int])
def recommend_song(
    song_id: int,
    top_n: int = Query(5, ge=1, le=20),
    builder: PlaylistBuilder = Depends(get_builder),
) -> List[int]:
    feature_map = get_feature_map_from_db() # Ensure map is loaded
    if song_id not in feature_map:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song features not found for recommendation seed")

    rec_ids = builder.build(song_id, top_n=top_n)
    if not rec_ids: # build might return empty if no similar songs found
        # Distinguish "song not found in map" from "no recommendations found"
         pass # Or raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recommendations found")

    return rec_ids

# /playlist/auto
@playlist_router.post("/auto", response_model=List[int])
def auto_playlist(
    seed_song_id: int,
    top_n: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db), # SQL DB session
    builder: PlaylistBuilder = Depends(get_builder), # Use the builder with DB-loaded features
) -> List[int]:
    feature_map = get_feature_map_from_db() # Ensure map is loaded
    if seed_song_id not in feature_map:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seed song features not found for auto playlist")

    rec_ids = builder.build(seed_song_id, top_n=top_n)
    if not rec_ids:
         pass # Or raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not build playlist, no recommendations found")
    return rec_ids

# Optional: Endpoint to trigger a reload of the feature map (e.g., for admin use)
@router.post("/admin/reload-features", include_in_schema=False) # Hide from public docs
def admin_reload_features():
    global _feature_map_loaded
    _feature_map_loaded = False # Force reload on next request
    try:
        get_feature_map_from_db() # Attempt to reload immediately
        return {"message": "Feature map reload triggered and attempted."}
    except HTTPException as e:
        return {"message": f"Feature map reload failed: {e.detail}"}