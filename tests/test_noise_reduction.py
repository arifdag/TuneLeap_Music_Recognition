import os
import numpy as np
import pytest
import librosa
from scipy.io.wavfile import write as wav_write
from worker.tasks import reduce_noise

@pytest.fixture
def noisy_wav(tmp_path):
    # generate 1s of 440Hz sine wave + Gaussian noise
    sr = 22050
    t = np.linspace(0, 1, int(sr * 1.0), endpoint=False)
    clean = 0.5 * np.sin(2 * np.pi * 440 * t)
    noise = np.random.normal(0, 0.1, clean.shape)
    noisy = clean + noise
    path = tmp_path / "noisy.wav"
    wav_write(str(path), sr, (noisy * 32767).astype(np.int16))
    return str(path)

def test_reduce_noise_creates_file_and_preserves_length(noisy_wav):
    input_path = noisy_wav
    output_path = reduce_noise.run(input_path)

    # verify output
    assert isinstance(output_path, str)
    assert os.path.isfile(output_path)

    # load both files and compare
    y_in, sr_in = librosa.load(input_path, sr=None)
    y_out, sr_out = librosa.load(output_path, sr=None)

    assert sr_in == sr_out
    assert len(y_in) == len(y_out)
