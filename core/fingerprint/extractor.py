import numpy as np
import librosa
import hashlib
from scipy.ndimage import maximum_filter
from typing import List, Tuple, Set
import struct


class FingerPrinter:
    """
    Implements Shazam-like audio fingerprinting using spectral peaks.
    This creates multiple hashes per song that can match partial audio.
    """

    # Fingerprinting parameters
    SAMPLE_RATE = 22050
    FFT_WINDOW_SIZE = 4096  # ~0.2 seconds
    OVERLAP_RATIO = 0.5

    # Peak detection parameters
    PEAK_NEIGHBORHOOD_SIZE = 20  # Size of local maxima filter
    MIN_PEAK_AMPLITUDE = 0.01  # Minimum amplitude for a peak

    # Fingerprint parameters
    MAX_HASH_TIME_DELTA = 200  # Maximum time difference between peaks (in frames)
    MIN_HASH_TIME_DELTA = 0  # Minimum time difference
    FINGERPRINT_REDUCTION = 20  # Reduce number of fingerprints by this factor

    # Target zone for pairing peaks
    TARGET_ZONE_START = 5  # Start pairing after 5 frames
    TARGET_ZONE_WIDTH = 100  # Look up to 100 frames ahead
    MAX_PAIRS_PER_PEAK = 3  # Maximum number of pairs per peak

    def __init__(self):
        self.hop_length = int(self.FFT_WINDOW_SIZE * (1 - self.OVERLAP_RATIO))

    def extract_fingerprints(self, file_path: str) -> List[Tuple[str, int]]:
        """
        Extract Shazam-like fingerprints from an audio file.
        Returns list of (hash, time_offset) tuples.
        """
        # Load audio
        y, sr = librosa.load(file_path, sr=self.SAMPLE_RATE, mono=True)

        # Compute spectrogram
        spectrogram = self._compute_spectrogram(y)

        # Find spectral peaks
        peaks = self._find_peaks(spectrogram)

        # Generate fingerprints from peak pairs
        fingerprints = self._generate_fingerprints(peaks)

        return fingerprints

    def _compute_spectrogram(self, audio: np.ndarray) -> np.ndarray:
        """Compute the magnitude spectrogram of the audio."""
        # Use STFT to get spectrogram
        D = librosa.stft(
            audio,
            n_fft=self.FFT_WINDOW_SIZE,
            hop_length=self.hop_length,
            window='hann'
        )

        # Convert to magnitude and apply log scaling
        magnitude = np.abs(D)

        # Apply log scaling to better capture quieter frequencies
        log_magnitude = np.log1p(magnitude)

        return log_magnitude

    def _find_peaks(self, spectrogram: np.ndarray) -> List[Tuple[int, int]]:
        """
        Find local maxima (peaks) in the spectrogram.
        Returns list of (frequency_bin, time_frame) tuples.
        """
        # Apply local maximum filter
        neighborhood_size = (self.PEAK_NEIGHBORHOOD_SIZE, self.PEAK_NEIGHBORHOOD_SIZE)
        local_max = maximum_filter(spectrogram, neighborhood_size, mode='constant')

        # Find peaks: points that are local maxima and above threshold
        is_peak = (spectrogram == local_max) & (spectrogram > self.MIN_PEAK_AMPLITUDE)

        # Get peak coordinates
        freq_indices, time_indices = np.where(is_peak)

        # Create list of peaks with their amplitudes
        peaks_with_amplitude = []
        for f, t in zip(freq_indices, time_indices):
            amplitude = spectrogram[f, t]
            peaks_with_amplitude.append((f, t, amplitude))

        # Sort by amplitude and keep strongest peaks
        peaks_with_amplitude.sort(key=lambda x: x[2], reverse=True)
        max_peaks = len(peaks_with_amplitude) // self.FINGERPRINT_REDUCTION
        peaks_with_amplitude = peaks_with_amplitude[:max_peaks]

        # Return just the coordinates
        peaks = [(f, t) for f, t, _ in peaks_with_amplitude]

        return peaks

    def _generate_fingerprints(self, peaks: List[Tuple[int, int]]) -> List[Tuple[str, int]]:
        """
        Generate fingerprints by pairing peaks within target zones.
        Each fingerprint is a hash of two peaks and the time delta between them.
        """
        # Sort peaks by time
        peaks.sort(key=lambda x: x[1])

        fingerprints = []

        for i, (f1, t1) in enumerate(peaks):
            # Look for peaks in the target zone
            pairs_found = 0

            for j in range(i + 1, len(peaks)):
                f2, t2 = peaks[j]

                # Calculate time difference
                time_delta = t2 - t1

                # Check if peak is in target zone
                if time_delta < self.TARGET_ZONE_START:
                    continue
                if time_delta > self.TARGET_ZONE_START + self.TARGET_ZONE_WIDTH:
                    break

                # Create hash from the two frequencies and time delta
                # Hash format: freq1:freq2:time_delta
                hash_input = f"{f1}:{f2}:{time_delta}"
                hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:16]

                # Store with time offset of first peak
                fingerprints.append((hash_value, t1))

                pairs_found += 1
                if pairs_found >= self.MAX_PAIRS_PER_PEAK:
                    break

        return fingerprints

    def match_fingerprints(self, query_fingerprints: List[Tuple[str, int]],
                           stored_fingerprints: dict) -> dict:
        """
        Match query fingerprints against stored fingerprints.
        Returns dict of song_id -> match_score.

        stored_fingerprints format: {hash: [(song_id, time_offset), ...]}
        """
        # Time difference histogram for each song
        time_diff_counts = {}

        for query_hash, query_time in query_fingerprints:
            if query_hash in stored_fingerprints:
                # This hash matches some stored fingerprints
                for song_id, stored_time in stored_fingerprints[query_hash]:
                    # Calculate time difference
                    time_diff = stored_time - query_time

                    # Create key for this song and time difference
                    key = (song_id, time_diff)

                    # Increment count
                    if key not in time_diff_counts:
                        time_diff_counts[key] = 0
                    time_diff_counts[key] += 1

        # Find the best match for each song
        song_scores = {}
        for (song_id, time_diff), count in time_diff_counts.items():
            if song_id not in song_scores or count > song_scores[song_id]:
                song_scores[song_id] = count

        return song_scores

def extract_fingerprint(file_path: str) -> List[Tuple[str, int]]:
    """
    Extract Shazam-like fingerprints from an audio file.
    Wrapper function that creates a FingerPrinter instance and extracts fingerprints.
    Returns list of (hash, time_offset) tuples.
    """
    fingerprinter = FingerPrinter()
    return fingerprinter.extract_fingerprints(file_path)