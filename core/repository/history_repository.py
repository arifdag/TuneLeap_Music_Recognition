from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from db.sql.models import RecognitionHistory, Song, Artist, Album
from api.schemas.history_schemas import RecognitionHistoryCreate

class RecognitionHistoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_recognition_event(
        self, history_data: RecognitionHistoryCreate, user_id: int
    ) -> Optional[RecognitionHistory]:
        # Optional: Check if the song_id exists
        song = self.session.query(Song).filter(Song.id == history_data.song_id).first()
        if not song:
            # Or raise an HTTPException directly that can be caught by FastAPI
            return None

        db_history_event = RecognitionHistory(
            **history_data.dict(),
            user_id=user_id
        )
        self.session.add(db_history_event)
        self.session.commit()
        self.session.refresh(db_history_event)
        return db_history_event

    def get_recognition_history_for_user(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> List[RecognitionHistory]:
        return (
            self.session.query(RecognitionHistory)
            .filter(RecognitionHistory.user_id == user_id)
            .options(
                joinedload(RecognitionHistory.song)
                .joinedload(Song.artist),
                joinedload(RecognitionHistory.song)
                .joinedload(Song.album)
            )
            .order_by(RecognitionHistory.recognized_at.desc(), RecognitionHistory.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_recognition_event_by_id(self, event_id: int, user_id: int) -> Optional[RecognitionHistory]:
        return (
            self.session.query(RecognitionHistory)
            .filter(RecognitionHistory.id == event_id, RecognitionHistory.user_id == user_id)
            .options(
                joinedload(RecognitionHistory.song)
                .joinedload(Song.artist),
                joinedload(RecognitionHistory.song)
                .joinedload(Song.album)
            )
            .first()
        )

    def delete_recognition_event(self, event_id: int, user_id: int) -> bool:
        db_event = self.get_recognition_event_by_id(event_id=event_id, user_id=user_id)
        if db_event:
            self.session.delete(db_event)
            self.session.commit()
            return True
        return False