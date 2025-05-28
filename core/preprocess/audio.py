import numpy as np
import librosa

def normalize(signal: np.ndarray) -> np.ndarray:
    """
    Normalize audio signal so that its RMS becomes 1.0.

    :param signal: 1D numpy array of audio samples
    :return: normalized signal
    """
    rms = np.sqrt(np.mean(np.square(signal)))
    if rms > 0:
        return signal / rms
    return signal

def resample(signal: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """
    Change the sample rate of an audio signal.

    :param signal: 1D numpy array of audio samples
    :param orig_sr: original sampling rate
    :param target_sr: desired sampling rate
    :return: resampled signal
    """
    return librosa.resample(signal, orig_sr=orig_sr, target_sr=target_sr)
