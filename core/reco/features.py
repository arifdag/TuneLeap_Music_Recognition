import numpy as np
import librosa


def extract_features(file_path: str, sr: int = 22050) -> np.ndarray:
    """
    Extract a feature vector from an audio file.
    Currently uses:
      - Tempo (beat tracking)
      - MFCC mean vector (20 coefficients)
    :param file_path: path to local audio file
    :param sr: sampling rate
    :return: 1D numpy array (1 + 20 = 21 dimensions)
    """
    try:
        # Load audio as mono
        y, _ = librosa.load(file_path, sr=sr, mono=True)

        # Tempo (beats per minute)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

        # MFCCs: shape = (n_mfcc, n_frames)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)

        # Compute mean across time frames: shape (20,)
        mfcc_mean = np.mean(mfcc, axis=1)


        # Ensure tempo is a flattened 1D array before stacking.
        # This handles cases where tempo might be a scalar, a 1D array, or a 2D array.
        tempo_array = np.array(tempo).flatten()

        # Horizontally stack the 1D tempo array and the 1D MFCC array.
        feature_vector = np.hstack((tempo_array, mfcc_mean))

        return feature_vector

    except Exception as e:
        print(f"ERROR during feature extraction for {file_path}: {e}")
        # Return an empty array or re-raise to indicate failure
        return np.array([])
