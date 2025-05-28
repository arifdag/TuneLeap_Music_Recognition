from celery import Celery
from core.fingerprint.extractor import extract_fingerprint
from core.repository.fingerprint_repository import FingerprintRepository

celery_app = Celery("worker", broker="redis://localhost:6379/0")

@celery_app.task(name="store_fingerprint")
def store_fingerprint(file_path: str, song_id: int) -> str:
    """
    Celery task: extract fingerprint and save to MongoDB.

    :param file_path: path to audio file
    :param song_id: associated Song ID
    :return: MongoDB ObjectId of created Fingerprint as string
    """
    fp_hash = extract_fingerprint(file_path)
    repo = FingerprintRepository()
    fp = repo.create(song_id=song_id, hash=fp_hash)
    return str(fp.id)
