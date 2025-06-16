from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.sql.database import get_db
from db.sql.models import User
from api.v1.auth import get_current_active_user
from api.schemas.history_schemas import RecognitionHistoryCreate, RecognitionHistoryResponse
from core.repository.history_repository import RecognitionHistoryRepository
from core.repository.song_repository import SongRepository

router = APIRouter(prefix="/me/history", tags=["User Recognition History"])

@router.post("/", response_model=RecognitionHistoryResponse, status_code=status.HTTP_201_CREATED)
def record_recognition_event(
    history_in: RecognitionHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Ensure song exists before recording history
    song_repo = SongRepository(db)
    song = song_repo.get_by_id(history_in.song_id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Song with id {history_in.song_id} not found."
        )

    history_repo = RecognitionHistoryRepository(db)
    history_event = history_repo.create_recognition_event(
        history_data=history_in, user_id=current_user.id
    )
    # create_recognition_event might return None if song validation inside it fails
    if not history_event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not record history event.")
    

    db.refresh(history_event, ["song"])
    

    if history_event.song:
        # Refresh song to load its relationships
        db.refresh(history_event.song)
        
        # Set artist_name and album_image fields
        if history_event.song.artist:
            history_event.song.artist_name = history_event.song.artist.name
        if history_event.song.album:
            history_event.song.album_image = history_event.song.album.album_image
    
    return history_event

@router.get("/", response_model=List[RecognitionHistoryResponse])
def get_my_recognition_history(
    skip: int = 0,
    limit: int = 20, # Default to 20, can be adjusted
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    history_repo = RecognitionHistoryRepository(db)
    history_list = history_repo.get_recognition_history_for_user(
        user_id=current_user.id, skip=skip, limit=limit
    )
    
    # Enhance the response with artist_name and album_image
    for history_item in history_list:
        if history_item.song and history_item.song.artist:
            history_item.song.artist_name = history_item.song.artist.name
        if history_item.song and history_item.song.album:
            history_item.song.album_image = history_item.song.album.album_image
            
    return history_list

@router.get("/{event_id}", response_model=RecognitionHistoryResponse)
def get_recognition_history_by_id(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    history_repo = RecognitionHistoryRepository(db)
    history_event = history_repo.get_recognition_event_by_id(
        event_id=event_id, user_id=current_user.id
    )
    
    if not history_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History event not found")
        
    # Enhance the response with artist_name and album_image
    if history_event.song and history_event.song.artist:
        history_event.song.artist_name = history_event.song.artist.name
    if history_event.song and history_event.song.album:
        history_event.song.album_image = history_event.song.album.album_image
        
    return history_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_recognition_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    history_repo = RecognitionHistoryRepository(db)
    if not history_repo.delete_recognition_event(event_id=event_id, user_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History event not found or not owned by user")
    return None