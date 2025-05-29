from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from core.io.recording import save_temp
from core.fingerprint.extractor import extract_fingerprint
from core.fingerprint.matcher import FingerprintMatcher
from core.repository.song_repository import SongRepository
from db.sql.database import get_db  # your DB session dependency

router = APIRouter(prefix="/recognize", tags=["recognition"])

@router.post("/")
async def recognize_audio(file: UploadFile, db: Session = Depends(get_db)):
    """
    Recognize an uploaded audio file and return matching song(s) with probabilities.
    """
    tmp_dir = "tmp"
    path = save_temp(file, dir=tmp_dir)

    try:
        try:
            fp_hash = extract_fingerprint(path)
            matcher = FingerprintMatcher()
            match_counts = matcher.match(fp_hash)
        except Exception:
            # on any extraction error, treat as “no match”
            match_counts = {}
    finally:
        if os.path.exists(path):
            os.remove(path)

    if not match_counts:
        raise HTTPException(status_code=404, detail="No match found")

    total = sum(match_counts.values())
    results = []
    for song_id, count in match_counts.items():
        prob = count / total
        item = {"song_id": song_id, "probability": prob}
        try:
            # if the SQL lookup works, add metadata; otherwise just swallow the error
            song = SongRepository(db).get_by_id(song_id)
            if song:
                item["title"] = song.title
                item["artist_id"] = song.artist_id
                item["album_id"] = song.album_id
        except Exception:
            pass
        results.append(item)

    return {"results": results}
