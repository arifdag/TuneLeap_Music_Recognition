import numpy as np
import librosa


def extract_features(file_path: str, sr: int = 22050) -> np.ndarray:
    """
    Extract optimized feature vector for partial song recognition.
    
    Features designed for:
    - High match rate with partial songs/clips
    - Fast similarity computation
    - Robust to duration and quality variations
    
    Feature breakdown:
    - Chroma features (12): Harmonic/melodic content - excellent for partial songs
    - MFCC statistics (26): Timbre characteristics with mean+std for 13 coefficients  
    - Spectral features (6): Centroid, rolloff, bandwidth (mean+std each)
    - Spectral contrast (7): Spectral peaks/valleys across frequency bands
    - Rhythm features (2): Tempo + rhythm strength
    - Zero crossing rate (2): Mean + std for texture analysis
    
    Total: 55 features (good balance of discrimination vs speed)
    
    :param file_path: path to local audio file
    :param sr: sampling rate
    :return: 1D numpy array of 55 features
    """
    try:
        # Load audio as mono
        y, _ = librosa.load(file_path, sr=sr, mono=True)
        
        if len(y) == 0:
            return np.array([])
        
        # Initialize feature list
        features = []
        
        # 1. CHROMA FEATURES (12 features) - Excellent for partial song matching
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=12)
        chroma_mean = np.mean(chroma, axis=1)
        features.extend(chroma_mean.tolist())
        
        # 2. MFCC STATISTICS (26 features) - Robust timbre representation
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)
        features.extend(mfcc_mean.tolist())
        features.extend(mfcc_std.tolist())
        
        # 3. SPECTRAL FEATURES (6 features) - Texture and brightness
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        
        features.extend([
            float(np.mean(spectral_centroids)),
            float(np.std(spectral_centroids)),
            float(np.mean(spectral_rolloff)),
            float(np.std(spectral_rolloff)),
            float(np.mean(spectral_bandwidth)),
            float(np.std(spectral_bandwidth))
        ])
        
        # 4. SPECTRAL CONTRAST (7 features) - Captures spectral shape
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, n_bands=6)
        contrast_mean = np.mean(spectral_contrast, axis=1)
        features.extend(contrast_mean.tolist())
        
        # 5. RHYTHM FEATURES (2 features)
        if len(y) > sr * 2:  # At least 2 seconds
            try:
                tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
                # Calculate rhythm strength (beat consistency)
                if len(beats) > 1:
                    beat_times = librosa.frames_to_time(beats, sr=sr)
                    beat_intervals = np.diff(beat_times)
                    rhythm_strength = 1.0 / (np.std(beat_intervals) + 1e-8)  # Lower std = more consistent rhythm
                else:
                    rhythm_strength = 0.0
            except:
                tempo = 0.0
                rhythm_strength = 0.0
        else:
            tempo = 0.0
            rhythm_strength = 0.0
            
        features.extend([float(tempo), float(rhythm_strength)])
        
        # 6. ZERO CROSSING RATE (2 features) - Texture analysis
        zcr = librosa.feature.zero_crossing_rate(y)
        features.extend([
            float(np.mean(zcr)),
            float(np.std(zcr))
        ])
        
        # Convert to numpy array and ensure consistent length
        feature_vector = np.array(features, dtype=np.float32)
        
        # Verify expected length (should be 55)
        expected_length = 12 + 26 + 6 + 7 + 2 + 2  # 55 total
        if len(feature_vector) != expected_length:
            print(f"Warning: Expected {expected_length} features, got {len(feature_vector)}")
        
        # Handle any NaN or infinite values
        feature_vector = np.nan_to_num(feature_vector, nan=0.0, posinf=1e6, neginf=-1e6)
        
        return feature_vector

    except Exception as e:
        print(f"ERROR during feature extraction for {file_path}: {e}")
        # Return zeros with expected length rather than empty array
        return np.zeros(55, dtype=np.float32)


def extract_lightweight_features(file_path: str, sr: int = 22050) -> np.ndarray:
    """
    Extract a lightweight feature set for very fast matching (25 features).
    Use this when you need maximum speed over accuracy.
    
    Features:
    - Chroma mean (12): Core harmonic content
    - MFCC mean (13): Basic timbre
    
    :param file_path: path to local audio file
    :param sr: sampling rate
    :return: 1D numpy array of 25 features
    """
    try:
        y, _ = librosa.load(file_path, sr=sr, mono=True)
        
        if len(y) == 0:
            return np.zeros(25, dtype=np.float32)
        
        features = []
        
        # Chroma features (12)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=12)
        chroma_mean = np.mean(chroma, axis=1)
        features.extend(chroma_mean.tolist())
        
        # MFCC mean only (13)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        features.extend(mfcc_mean.tolist())
        
        feature_vector = np.array(features, dtype=np.float32)
        feature_vector = np.nan_to_num(feature_vector, nan=0.0, posinf=1e6, neginf=-1e6)
        
        return feature_vector
        
    except Exception as e:
        print(f"ERROR during lightweight feature extraction for {file_path}: {e}")
        return np.zeros(25, dtype=np.float32)
