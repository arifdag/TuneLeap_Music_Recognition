from typing import List, Dict
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from core.reco.builder import PlaylistBuilder
from db.sql.database import get_db
from core.repository.song_feature_repository import SongFeatureRepository
from core.repository.history_repository import RecognitionHistoryRepository
from mongoengine import connect
import os
from collections import Counter

# --- MongoDB Connection Management ---
MONGO_URI_PLAYLISTS = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME_PLAYLISTS = os.getenv("DB_NAME", "tuneleap_db")

_feature_map_cache: Dict[int, np.ndarray] = {}
_feature_map_loaded = False


def get_feature_map_from_db() -> Dict[int, np.ndarray]:
    global _feature_map_cache, _feature_map_loaded
    if not _feature_map_loaded:
        try:
            connect(db=DB_NAME_PLAYLISTS, host=MONGO_URI_PLAYLISTS, alias='default_playlists_api')
            repo = SongFeatureRepository()
            _feature_map_cache = repo.get_all_features()
            _feature_map_loaded = True
        except Exception as e:
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
    if not feature_map:  # Handle case where map might be empty after attempted load
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Recommendation engine not ready, no features.")
    return PlaylistBuilder(feature_map)


# /recommend/{song_id}
@router.get("/{song_id}", response_model=List[int])
def recommend_song(
        song_id: int,
        top_n: int = Query(5, ge=1, le=20),
        builder: PlaylistBuilder = Depends(get_builder),
) -> List[int]:
    feature_map = get_feature_map_from_db()
    if song_id not in feature_map:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Song features not found for recommendation seed")

    rec_ids = builder.build(song_id, top_n=top_n)
    if not rec_ids:
        HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recommendations found")

    return rec_ids


# /playlist/auto
@playlist_router.post("/auto", response_model=List[int])
def auto_playlist(
        seed_song_id: int,
        top_n: int = Query(5, ge=1, le=20),
        db: Session = Depends(get_db),  # SQL DB session
        builder: PlaylistBuilder = Depends(get_builder),
) -> List[int]:
    feature_map = get_feature_map_from_db()
    if seed_song_id not in feature_map:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Seed song features not found for auto playlist")

    rec_ids = builder.build(seed_song_id, top_n=top_n)
    if not rec_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Could not build playlist, no recommendations found")
    return rec_ids


@router.get("/user/{user_id}", response_model=List[int])
def recommend_for_user(
        user_id: int,
        top_n: int = Query(10, ge=1, le=50),
        time_weight: bool = Query(True, description="Whether to weight recent listens more heavily"),
        db: Session = Depends(get_db),
        builder: PlaylistBuilder = Depends(get_builder)
) -> List[int]:
    """
    Recommend songs for a user based on their listening history.
    
    Algorithm:
    1. Get user's listening history
    2. Build a weighted list of songs they've listened to (more recent = higher weight if time_weight=True)
    3. For each song in history, get similar songs using feature-based recommendations
    4. Aggregate and rank these recommendations, excluding songs the user already heard
    5. Return top N recommendations
    """
    history_repo = RecognitionHistoryRepository(db)
    history = history_repo.get_recognition_history_for_user(user_id=user_id, limit=100)

    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No listening history found for user")

    song_weights = {}
    heard_songs = set()

    # Newer listens get higher weights if time_weight is True
    for idx, item in enumerate(history):
        heard_songs.add(item.song_id)
        weight = len(history) - idx if time_weight else 1
        song_weights[item.song_id] = song_weights.get(item.song_id, 0) + weight

    # Get recommendations for each song in user's history, weighted by listen count/recency
    all_recommendations = []
    feature_map = get_feature_map_from_db()

    for song_id, weight in song_weights.items():
        if song_id in feature_map:
            song_recs = builder.build(song_id, top_n=10)  # Get more than needed as we'll filter and rank

            # Weight each recommendation by the seed song's weight
            for rec_id in song_recs:
                if rec_id not in heard_songs:  # Don't recommend songs they've already heard
                    all_recommendations.append((rec_id, weight))

    if not all_recommendations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not generate recommendations")

    # Aggregate and rank recommendations
    rec_counter = Counter()
    for rec_id, weight in all_recommendations:
        rec_counter[rec_id] += weight

    # Get top N recommended song IDs
    top_recommendations = [song_id for song_id, _ in rec_counter.most_common(top_n)]

    return top_recommendations


# Endpoint to recommend similar songs to a given song
@router.get("/similar/{song_id}", response_model=List[int])
def recommend_similar_songs(
        song_id: int,
        top_n: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db),
        builder: PlaylistBuilder = Depends(get_builder)
) -> List[int]:
    """
    Recommend songs similar to a specific song based on audio features.
    """
    feature_map = get_feature_map_from_db()
    if song_id not in feature_map:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song features not found")

    similar_songs = builder.build(song_id, top_n=top_n)
    if not similar_songs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No similar songs found")

    return similar_songs


# Endpoint to trigger a reload of the feature map (e.g., for admin use)
@router.post("/admin/reload-features", include_in_schema=False)
def admin_reload_features():
    global _feature_map_loaded
    _feature_map_loaded = False  # Force reload on next request
    try:
        get_feature_map_from_db()  # Attempt to reload immediately
        return {"message": "Feature map reload triggered and attempted."}
    except HTTPException as e:
        return {"message": f"Feature map reload failed: {e.detail}"}
