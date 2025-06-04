from celery import Celery
import os # Import os

# Fingerprint task imports
from core.fingerprint.extractor import extract_fingerprint
from core.repository.fingerprint_repository import FingerprintRepository
from core.reco.features import extract_features # Assuming this is the correct feature extraction function
from core.repository.song_feature_repository import SongFeatureRepository
import numpy as np

# Noise-reduction imports
import librosa
import soundfile as sf
from core.noise.reducer import reduce_noise_array

# Get Redis URL from environment variable, default to localhost if not set
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery("worker", broker=REDIS_URL) # Use the variable


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
    # load file
    y, sr = librosa.load(file_path, sr=None, mono=True)
    # denoise
    y_denoised = reduce_noise_array(y, sr)
    # write out
    out_path = file_path.replace(".wav", "_denoised.wav")
    sf.write(out_path, y_denoised, sr)
    return out_path

@celery_app.task(name="extract_and_store_features")
def extract_and_store_features_task(file_path: str, song_id: int):
    """
    Extracts audio features for a song and stores them in MongoDB.
    """
    try:
        # Note: extract_features might take sr as an argument
        # y, sr_audio = librosa.load(file_path, sr=None, mono=True) # Load to get sr if needed
        # feature_vector = extract_features(file_path, sr=sr_audio) # Pass sr if function needs it
        feature_vector = extract_features(file_path) # Or if it handles sr internally

        if isinstance(feature_vector, np.ndarray):
            repo = SongFeatureRepository()
            repo.create_or_update(song_id=song_id, feature_vector=feature_vector)
            return f"Features stored for song_id {song_id}"
        else:
            # Log an error or raise an exception
            return f"Failed to extract features for song_id {song_id}: Not a numpy array"
    except Exception as e:
        # Log error: print(f"Error extracting/storing features for {song_id}: {e}")
        # Optionally re-raise or handle
        return f"Error processing song_id {song_id}: {str(e)}"