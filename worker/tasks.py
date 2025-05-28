from celery import Celery

# Fingerprint task imports
from core.fingerprint.extractor import extract_fingerprint
from core.repository.fingerprint_repository import FingerprintRepository

# Noise-reduction imports
import librosa
import soundfile as sf
from core.noise.reducer import reduce_noise_array

celery_app = Celery("worker", broker="redis://localhost:6379/0")


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
