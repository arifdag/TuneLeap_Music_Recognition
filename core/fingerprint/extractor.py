import numpy as np
import librosa
import hashlib
from typing import List

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

def extract_fingerprint_windows(file_path: str, sr: int = 22050, 
                               window_duration: float = 10.0, 
                               hop_duration: float = 5.0) -> List[str]:
    """
    Extract multiple fingerprints from overlapping windows of an audio file.
    This allows matching partial songs by creating fingerprints for different segments.
    
    :param file_path: Path to the audio file
    :param sr: Sampling rate to use when loading
    :param window_duration: Duration of each window in seconds
    :param hop_duration: Hop size between windows in seconds
    :return: List of hexadecimal SHA-256 hash strings representing fingerprints
    """
    # load as mono
    y, _ = librosa.load(file_path, sr=sr, mono=True)
    
    # Calculate window and hop sizes in samples
    window_samples = int(window_duration * sr)
    hop_samples = int(hop_duration * sr)
    
    fingerprints = []
    
    # Extract windows
    for start in range(0, len(y) - window_samples + 1, hop_samples):
        end = start + window_samples
        window_audio = y[start:end]
        
        # Skip if window is too short
        if len(window_audio) < window_samples * 0.8:  # At least 80% of expected length
            continue
            
        # compute MFCCs for this window
        mfcc = librosa.feature.mfcc(y=window_audio, sr=sr, n_mfcc=20)
        # mean across time frames
        mfcc_mean = np.mean(mfcc, axis=1)
        # quantize to reduce small variations
        quantized = np.round(mfcc_mean, 2)
        # hash the bytes
        fp_hash = hashlib.sha256(quantized.tobytes()).hexdigest()
        fingerprints.append(fp_hash)
    
    return fingerprints

def extract_robust_fingerprint(file_path: str, sr: int = 22050) -> str:
    """
    Extract a more robust fingerprint that works better with partial songs.
    Uses spectral centroid and other features that are less sensitive to duration.
    
    :param file_path: Path to the audio file
    :param sr: Sampling rate to use when loading
    :return: Hexadecimal SHA-256 hash string representing the fingerprint
    """
    # load as mono
    y, _ = librosa.load(file_path, sr=sr, mono=True)
    
    # Extract multiple features that are more robust
    features = []
    
    # MFCCs (but use percentiles instead of just mean)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_percentiles = np.percentile(mfcc, [25, 50, 75], axis=1).flatten()
    features.extend(mfcc_percentiles.tolist())
    
    # Spectral centroid
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    features.append(float(np.mean(spectral_centroid)))
    features.append(float(np.std(spectral_centroid)))
    
    # Spectral rolloff
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    features.append(float(np.mean(spectral_rolloff)))
    features.append(float(np.std(spectral_rolloff)))
    
    # Zero crossing rate
    zcr = librosa.feature.zero_crossing_rate(y)
    features.append(float(np.mean(zcr)))
    features.append(float(np.std(zcr)))
    
    # Tempo (if audio is long enough)
    if len(y) > sr * 3:  # At least 3 seconds
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        features.append(float(tempo))
    else:
        features.append(0.0)  # Default value for short clips
    
    # Convert to numpy array and quantize
    features_array = np.array(features, dtype=float)
    quantized = np.round(features_array, 2)
    
    # hash the bytes
    return hashlib.sha256(quantized.tobytes()).hexdigest()
