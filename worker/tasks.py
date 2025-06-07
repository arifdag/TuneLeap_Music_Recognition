from celery import Celery
import ssl
import os

# Fingerprint task imports
from core.fingerprint.extractor import extract_fingerprint
from core.repository.fingerprint_repository import FingerprintRepository
from core.reco.features import extract_features
from core.repository.song_feature_repository import SongFeatureRepository
import numpy as np

# Noise-reduction imports
import librosa
import soundfile as sf
from core.noise.reducer import reduce_noise_array

# --- Database Imports for recognize_audio_task ---
# This task needs its own database connection.
from db.sql.database import get_db
from core.repository.song_repository import SongRepository

# --- Celery App Configuration ---
# Get Redis URL from environment variable
REDIS_URL = os.getenv("CELERY_BROKER_URL")

celery_config = {
    "broker_url": REDIS_URL,
    "result_backend": REDIS_URL,
    "broker_connection_retry_on_startup": True,
    "task_ignore_result": True,
    "broker_transport_options": {
        'brpop_timeout': 30,
    }
}

# Force SSL/TLS for Upstash
# Force SSL/TLS for Upstash with the correct settings
if REDIS_URL and "upstash.io" in REDIS_URL:
    # Use the correct constant from the ssl module
    celery_config["broker_use_ssl"] = {
        'ssl_cert_reqs': ssl.CERT_REQUIRED
    }
    # Ensure the URL uses the rediss protocol
    if celery_config["broker_url"].startswith("redis://"):
        celery_config["broker_url"] = celery_config["broker_url"].replace("redis://", "rediss://", 1)

celery_app = Celery("worker")
celery_app.conf.update(**celery_config)


# --- Task Definitions ---

@celery_app.task(name="recognize_audio_task", ignore_result=False)
def recognize_audio_task(path: str):
    """
    This is the main asynchronous task for audio recognition.
    """
    from core.fingerprint.matcher import FingerprintMatcher

    try:
        fp_hash = extract_fingerprint(path)
        matcher = FingerprintMatcher()
        match_counts = matcher.match(fp_hash)
    except Exception:
        match_counts = {}
    finally:
        if os.path.exists(path):
            os.remove(path)

    if not match_counts:
        return {"status": "NO_MATCH"}

    total = sum(match_counts.values())
    results = []

    # We create a new DB session for this background task
    db = next(get_db())
    try:
        song_repo = SongRepository(db)
        for song_id, count in match_counts.items():
            prob = count / total
            item = {"song_id": song_id, "probability": prob}
            song = song_repo.get_by_id(song_id)
            if song:
                item["title"] = song.title
                item["artist_id"] = song.artist_id
                item["album_id"] = song.album_id
            results.append(item)
    finally:
        db.close()

    return {"status": "SUCCESS", "results": results}


@celery_app.task(name="store_fingerprint")
def store_fingerprint(file_path: str, song_id: int) -> str:
    """
    Extract fingerprint and save to MongoDB.
    """
    fp_hash = extract_fingerprint(file_path)
    repo = FingerprintRepository()
    fp = repo.create(song_id=song_id, hash=fp_hash)
    return str(fp.id)


@celery_app.task(name="reduce_noise")
def reduce_noise(file_path: str) -> str:
    """
    Celery task: load an audio file, reduce its noise, write new file, and return its path.
    """
    y, sr = librosa.load(file_path, sr=None, mono=True)
    y_denoised = reduce_noise_array(y, sr)
    out_path = file_path.replace(".wav", "_denoised.wav")
    sf.write(out_path, y_denoised, sr)
    return out_path


@celery_app.task(name="extract_and_store_features")
def extract_and_store_features_task(file_path: str, song_id: int):
    """
    Extracts audio features for a song and stores them in MongoDB.
    """
    try:
        feature_vector = extract_features(file_path)
        if isinstance(feature_vector, np.ndarray):
            repo = SongFeatureRepository()
            repo.create_or_update(song_id=song_id, feature_vector=feature_vector)
            return f"Features stored for song_id {song_id}"
        else:
            return f"Failed to extract features for song_id {song_id}: Not a numpy array"
    except Exception as e:
        return f"Error processing song_id {song_id}: {str(e)}"