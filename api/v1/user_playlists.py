from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.sql.database import get_db
from db.sql.models import User # For current_user dependency
from api.v1.auth import get_current_active_user # Auth dependency
from api.schemas.playlist_schemas import PlaylistCreate, PlaylistResponse, PlaylistUpdate, PlaylistItemCreate, PlaylistItemResponse # Schemas
from core.repository.playlist_repository import PlaylistRepository
from core.repository.song_repository import SongRepository # To verify song exists

router = APIRouter(prefix="/me/playlists", tags=["User Playlists"])

@router.post("/", response_model=PlaylistResponse, status_code=status.HTTP_201_CREATED)
def create_my_playlist(
    playlist_in: PlaylistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    playlist_repo = PlaylistRepository(db)
    playlist = playlist_repo.create_playlist(playlist_data=playlist_in, user_id=current_user.id)
    return playlist

@router.get("/", response_model=List[PlaylistResponse])
def get_my_playlists(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    playlist_repo = PlaylistRepository(db)
    playlists = playlist_repo.get_playlists_by_user_id(user_id=current_user.id, skip=skip, limit=limit)
    return playlists

@router.get("/{playlist_id}", response_model=PlaylistResponse)
def get_my_playlist_by_id(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    playlist_repo = PlaylistRepository(db)
    playlist = playlist_repo.get_playlist_by_id(playlist_id=playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    return playlist

@router.put("/{playlist_id}", response_model=PlaylistResponse)
def update_my_playlist(
    playlist_id: int,
    playlist_in: PlaylistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    playlist_repo = PlaylistRepository(db)
    updated_playlist = playlist_repo.update_playlist(playlist_id=playlist_id, playlist_data=playlist_in, user_id=current_user.id)
    if not updated_playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found or not owned by user")
    return updated_playlist

@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    playlist_repo = PlaylistRepository(db)
    if not playlist_repo.delete_playlist(playlist_id=playlist_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found or not owned by user")
    return None # Or return a success message if preferred over 204

# --- Playlist Items ---
@router.post("/{playlist_id}/songs", response_model=PlaylistItemResponse, status_code=status.HTTP_201_CREATED)
def add_song_to_my_playlist(
    playlist_id: int,
    item_in: PlaylistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    playlist_repo = PlaylistRepository(db)
    # Optional: Verify song exists using SongRepository
    song_repo = SongRepository(db)
    if not song_repo.get_by_id(item_in.song_id):
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Song with id {item_in.song_id} not found")

    playlist_item = playlist_repo.add_song_to_playlist(playlist_id=playlist_id, song_id=item_in.song_id, user_id=current_user.id)
    if not playlist_item:
        # This could be due to playlist not found, or song already in playlist (if repo handles it that way)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not add song to playlist. Playlist not found, or song already exists.")
    return playlist_item

@router.delete("/{playlist_id}/songs/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_song_from_my_playlist(
    playlist_id: int,
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    playlist_repo = PlaylistRepository(db)
    if not playlist_repo.remove_song_from_playlist(playlist_id=playlist_id, song_id=song_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found in playlist or playlist not owned by user")
    return None