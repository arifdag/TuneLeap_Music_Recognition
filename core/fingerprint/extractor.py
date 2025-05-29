import numpy as np
import librosa
import hashlib

def extract_fingerprint(file_path: str, sr: int = 22050) -> str:
    """
    Loads an audio file and extracts a fingerprint by computing MFCC means
    and hashing them.

    :param file_path: Path to the audio file
    :param sr: Sampling rate to use when loading
    :return: Hexadecimal SHA-256 hash string representing the fingerprint
    """
    # load as mono
    y, _ = librosa.load(file_path, sr=sr, mono=True)
    # compute MFCCs
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    # mean across time frames
    mfcc_mean = np.mean(mfcc, axis=1)
    # quantize to reduce small variations
    quantized = np.round(mfcc_mean, 2)
    # hash the bytes
    return hashlib.sha256(quantized.tobytes()).hexdigest()
