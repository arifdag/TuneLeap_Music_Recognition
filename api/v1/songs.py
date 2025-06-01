from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.repository.song_repository import SongRepository
from db.sql.database import get_db

router = APIRouter(prefix="/songs", tags=["songs"])

@router.get("/{song_id}")
def get_song(
    song_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a song by its ID.
    """
    repo = SongRepository(db)
    song = repo.get_by_id(song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return {
        "id": song.id,
        "title": song.title,
        "artist_id": song.artist_id,
        "album_id": song.album_id,
        "duration": song.duration
    }
