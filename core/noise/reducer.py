import numpy as np
import noisereduce as nr

def reduce_noise_array(y: np.ndarray, sr: int) -> np.ndarray:
    """
    Reduce noise from a 1D audio signal using spectral gating.

    :param y: input audio time series
    :param sr: sampling rate
    :return: denoised audio time series
    """
    return nr.reduce_noise(y=y, sr=sr)
