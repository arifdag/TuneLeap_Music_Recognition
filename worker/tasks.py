﻿from celery import Celery
import os
from typing import List, Tuple, Dict

# Fingerprint task imports
from core.fingerprint.extractor import extract_fingerprint
from core.repository.fingerprint_repository import FingerprintRepository
from core.fingerprint.matcher import FingerprintMatcher
from core.fingerprint.threshold import HybridMatchStrategy
from core.reco.features import extract_features
from core.repository.song_feature_repository import SongFeatureRepository
import numpy as np

# Noise-reduction imports
import librosa
import soundfile as sf
from core.noise.reducer import reduce_noise_array

# --- Database Imports for recognize_audio_task ---
# This task needs its own database connection.
from db.sql.database import get_db
from core.repository.song_repository import SongRepository
from core.repository.album_repository import AlbumRepository
from core.repository.artist_repository import ArtistRepository

# --- Celery App Configuration ---
# Get Redis URL from environment variable
REDIS_URL = os.getenv("CELERY_BROKER_URL")

if REDIS_URL and "upstash.io" in REDIS_URL:
    # Only use SSL for Upstash cloud Redis
    celery_app = Celery(
        "worker",
        broker_url=REDIS_URL.replace("redis://", "rediss://"),
        result_backend=REDIS_URL.replace("redis://", "rediss://"),
    )
else:
    # For local development, use regular Redis (no SSL)
    celery_app = Celery(
        "worker",
        broker=REDIS_URL or "redis://localhost:6379/0",
        result_backend=REDIS_URL or "redis://localhost:6379/0"
    )

# --- Set common configurations for both environments ---
celery_app.conf.broker_connection_retry_on_startup = True
celery_app.conf.task_ignore_result = True

# Reduce Redis commands to save Upstash quota
celery_app.conf.broker_transport_options = {
    'brpop_timeout': 30,
    'visibility_timeout': 43200,  # 12 hours
    'retry_policy': {
        'timeout': 5.0
    }
}

# Reduce heartbeat and monitoring frequency
celery_app.conf.worker_send_task_events = False
celery_app.conf.task_send_sent_event = False
celery_app.conf.worker_hijack_root_logger = False
celery_app.conf.worker_log_color = False

# Increase polling intervals to reduce Redis commands
celery_app.conf.broker_heartbeat = 120  # Default is 10, increase to 120 seconds
celery_app.conf.worker_prefetch_multiplier = 1  # Process one task at a time
celery_app.conf.task_acks_late = True
celery_app.conf.worker_disable_rate_limits = True

# Only send results for tasks that explicitly need them
celery_app.conf.task_ignore_result = False  # Changed to False for specific tasks
celery_app.conf.result_expires = 3600  # Results expire after 1 hour

# --- Task Definitions ---

@celery_app.task(name="recognize_audio_task", ignore_result=False)
def recognize_audio_task(path: str):
    """
    Extract fingerprints from an audio file and return matching songs.
    Uses SpectralMatch spectral peak fingerprinting for robust recognition.
    """
    import traceback
    from core.fingerprint.extractor import extract_fingerprint
    from core.repository.fingerprint_repository import FingerprintRepository
    from mongoengine import connect
    from dotenv import load_dotenv

    # Ensure MongoDB connection in worker process
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "tuneleap_db")
    connect(db=db_name, host=mongo_uri, alias="default")

    try:
        print(f"Worker: Processing file {path}")

        # Check if file exists
        if not os.path.exists(path):
            print(f"Worker: File not found: {path}")
            return {"status": "NO_MATCH", "error": "File not found"}

        # Extract SpectralMatch fingerprints
        print("Worker: Extracting SpectralMatch fingerprints...")
        query_fingerprints = extract_fingerprint(path)
        print(f"Worker: Extracted {len(query_fingerprints)} fingerprints from query")

        if not query_fingerprints:
            print("Worker: No fingerprints extracted from query audio")
            return {"status": "NO_MATCH"}

        # Get stored fingerprints
        print("Worker: Loading stored fingerprints...")
        repo = FingerprintRepository()
        
        # Extract just the hashes from query fingerprints for efficient lookup
        query_hashes = [fp[0] for fp in query_fingerprints]
        stored_fingerprints = repo.get_fingerprints_by_hashes(query_hashes)
        
        if not stored_fingerprints:
            print("Worker: No matching fingerprints found in database")
            return {"status": "NO_MATCH"}

        # Match fingerprints using time-offset algorithm
        print("Worker: Matching fingerprints...")
        song_scores = match_spectral_fingerprints(query_fingerprints, stored_fingerprints)
        
        if not song_scores:
            print("Worker: No matches found")
            return {"status": "NO_MATCH"}

        # Sort by score and get top matches
        sorted_matches = sorted(song_scores.items(), key=lambda x: x[1], reverse=True)
        print(f"Worker: Top matches: {sorted_matches[:5]}")

        # Convert to probabilities
        total_score = sum(score for _, score in sorted_matches[:10])  # Top 10 for probability calculation
        
        results = []
        db = next(get_db())
        try:
            song_repo = SongRepository(db)
            album_repo = AlbumRepository(db)
            artist_repo = ArtistRepository(db)
            
            for song_id, score in sorted_matches[:5]:  # Return top 5 matches
                probability = score / total_score if total_score > 0 else 0
                item = {
                    "song_id": song_id,
                    "probability": probability,
                    "match_score": score
                }
                
                # Get song details
                song = song_repo.get_by_id(song_id)
                if song:
                    item["title"] = song.title
                    item["artist_id"] = song.artist_id
                    
                    # Get artist name
                    artist = artist_repo.get_by_id(song.artist_id)
                    if artist:
                        item["artist_name"] = artist.name
                    
                    # Get album details if available
                    if song.album_id:
                        album = album_repo.get_by_id(song.album_id)
                        if album:
                            item["album_id"] = song.album_id
                            item["album_name"] = album.title
                            if album.album_image:
                                item["album_image"] = album.album_image
                
                results.append(item)
            
            print(f"Worker: Recognition complete with {len(results)} results")
            
        except Exception as e:
            print(f"Worker: Error getting song details: {e}")
            return {"status": "ERROR", "error": str(e)}
        finally:
            db.close()

        return {"status": "SUCCESS", "results": results}

    except Exception as e:
        print(f"Worker: Error during recognition: {e}")
        traceback.print_exc()
        return {"status": "ERROR", "error": str(e)}
    finally:
        # Clean up file after processing
        if os.path.exists(path):
            print(f"Worker: Cleaning up file {path}")
            os.remove(path)


def match_spectral_fingerprints(query_fingerprints: List[Tuple[str, int]], 
                              stored_fingerprints: Dict[str, List[Tuple[int, int]]]) -> Dict[int, int]:
    """
    Match query fingerprints against stored fingerprints using time-offset algorithm.
    Returns dict of song_id -> match_score.
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


def _process_fingerprint_matches(match_counts: dict, path: str):
    """Process exact fingerprint matches using traditional counting."""
    print("Worker: Processing exact fingerprint matches...")
    total = sum(match_counts.values())
    results = []

    db = next(get_db())
    try:
        song_repo = SongRepository(db)
        album_repo = AlbumRepository(db)
        for song_id, count in match_counts.items():
            prob = count / total
            item = {"song_id": song_id, "probability": prob}
            song = song_repo.get_by_id(song_id)
            if song:
                item["title"] = song.title
                item["artist_id"] = song.artist_id
                item["album_id"] = song.album_id
                
                # Get album image if available
                if song.album_id:
                    album = album_repo.get_by_id(song.album_id)
                    if album and album.album_image:
                        item["album_image"] = album.album_image
                        
            results.append(item)
        print(f"Worker: Exact match results: {results}")
    except Exception as e:
        print(f"Worker: Error processing exact matches: {e}")
        return {"status": "ERROR", "error": str(e)}
    finally:
        db.close()

    return {"status": "SUCCESS", "results": results}


def _process_similarity_matches(path: str):
    """Process feature-based similarity matches with enhanced tolerance for degraded audio."""
    try:
        from core.reco.features import extract_features
        from core.repository.song_feature_repository import SongFeatureRepository
        import numpy as np

        print("Worker: Extracting features from query audio...")
        query_features = extract_features(path)

        if len(query_features) == 0:
            print("Worker: Could not extract features from query")
            return {"status": "NO_MATCH"}

        # Get all stored song features
        feature_repo = SongFeatureRepository()
        all_features = feature_repo.get_all_features()

        if not all_features:
            print("Worker: No stored song features found")
            return {"status": "NO_MATCH"}

        print(f"Worker: Comparing against {len(all_features)} stored songs")

        # Calculate similarities directly
        similarities = []
        for song_id, stored_features in all_features.items():
            similarity = _compute_weighted_cosine_similarity(query_features, stored_features)
            similarities.append((song_id, similarity))

        # Lower threshold for phone-to-PC recognition (was 0.5)
        threshold = 0.3  # More tolerant of degraded audio
        filtered_similarities = [(sid, sim) for sid, sim in similarities if sim >= threshold]

        if not filtered_similarities:
            print(f"Worker: No similarities above threshold {threshold}")
            return {"status": "NO_MATCH"}

        # Sort by similarity descending and take top 10 for better results
        filtered_similarities.sort(key=lambda x: x[1], reverse=True)
        top_similarities = filtered_similarities[:10]  # Increased from 5 to 10

        print(f"Worker: Top similarities: {[(sid, f'{sim:.3f}') for sid, sim in top_similarities]}")

        # Apply softmax to similarity scores for better probability distribution
        sim_scores = np.array([sim for _, sim in top_similarities])

        # Temperature to control the sharpness of the probability distribution
        temperature = 0.05  # Lower temperature makes the distribution sharper

        # Apply temperature and compute softmax
        sim_scores_temp = sim_scores / temperature
        probabilities = np.exp(sim_scores_temp) / np.sum(np.exp(sim_scores_temp))

        results = []

        db = next(get_db())
        try:
            song_repo = SongRepository(db)
            album_repo = AlbumRepository(db)
            
            for i, (song_id, similarity) in enumerate(top_similarities):
                prob = probabilities[i]
                item = {"song_id": song_id, "probability": prob, "similarity": similarity}
                song = song_repo.get_by_id(song_id)
                if song:
                    item["title"] = song.title
                    item["artist_id"] = song.artist_id
                    item["album_id"] = song.album_id
                    
                    # Get album image if available
                    if song.album_id:
                        album = album_repo.get_by_id(song.album_id)
                        if album and album.album_image:
                            item["album_image"] = album.album_image
                            
                results.append(item)

            # Sort results by final probability
            results.sort(key=lambda x: x['probability'], reverse=True)

            # Keep only top 1 result after softmax
            results = results[:3]

            # Format results for logging
            result_summary = [(r['song_id'], f"prob={r['probability']:.3f}", f"sim={r['similarity']:.3f}") for r in results]
            print(f"Worker: Similarity-based results with softmax: {result_summary}")

        except Exception as e:
            print(f"Worker: Error processing similarity matches: {e}")
            return {"status": "ERROR", "error": str(e)}
        finally:
            db.close()

        return {"status": "SUCCESS", "results": results}

    except Exception as e:
        print(f"Worker: Error in similarity matching: {e}")
        return {"status": "ERROR", "error": str(e)}


def _compute_weighted_cosine_similarity(features1: np.ndarray, features2: np.ndarray) -> float:
    """
    Compute weighted cosine similarity optimized for phone-to-PC recognition.
    Adjusted weights to prioritize features that are more robust to noise and degradation.
    """
    if len(features1) == 0 or len(features2) == 0:
        return 0.0

    # Ensure same length
    min_len = min(len(features1), len(features2))
    f1 = features1[:min_len]
    f2 = features2[:min_len]

    # Create feature weights optimized for degraded audio (55 features expected)
    if min_len >= 55:
        weights = np.concatenate([
            np.full(12, 3.0),  # Chroma - highest weight (very robust to noise)
            np.full(13, 1.5),  # MFCC mean - medium weight (somewhat affected by noise)
            np.full(13, 0.8),  # MFCC std - lower weight (highly affected by noise)
            np.full(6, 1.0),   # Spectral features - medium weight
            np.full(7, 2.0),   # Spectral contrast - high weight (robust to noise)
            np.full(2, 0.3),   # Rhythm - very low weight (unreliable with noise)
            np.full(2, 0.2)    # ZCR - lowest weight (very noise-sensitive)
        ])
    else:
        # Fallback for different feature lengths
        weights = np.ones(min_len)

    weights = weights[:min_len]

    # Apply weights and normalize
    f1_weighted = f1 * weights
    f2_weighted = f2 * weights

    norm1 = np.linalg.norm(f1_weighted)
    norm2 = np.linalg.norm(f2_weighted)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(f1_weighted, f2_weighted) / (norm1 * norm2))


@celery_app.task(name="store_fingerprint")
def store_fingerprint(file_path: str, song_id: int) -> str:
    """
    Extract and store SpectralMatch fingerprints for a song.
    Now uses SpectralMatch algorithm for better partial song recognition.
    """
    from mongoengine import connect
    from dotenv import load_dotenv

    # Ensure MongoDB connection in worker process
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "tuneleap_db")
    connect(db=db_name, host=mongo_uri, alias="default")

    try:
        # Extract SpectralMatch fingerprints
        fingerprints = extract_fingerprint(file_path)
        
        if not fingerprints:
            return f"No fingerprints extracted for song_id {song_id}"
        
        # Store fingerprints
        repo = FingerprintRepository()
        count = repo.store_spectral_fingerprints(song_id, fingerprints)
        
        return f"Stored {count} SpectralMatch fingerprints for song_id {song_id}"
        
    except Exception as e:
        return f"Error processing song_id {song_id}: {str(e)}"


@celery_app.task(name="reduce_noise")
def reduce_noise(file_path: str) -> str:
    """
    Celery task: load an audio file, reduce its noise, write new file, and return its path.
    """
    y, sr = librosa.load(file_path, sr=None, mono=True)
    y_denoised = reduce_noise_array(y, sr)
    out_path = file_path.replace(".wav", "_denoised.wav")
    sf.write(out_path, y_denoised, sr)
    return out_path


@celery_app.task(name="extract_and_store_features")
def extract_and_store_features_task(file_path: str, song_id: int):
    """
    Extracts audio features for a song and stores them in MongoDB.
    """
    from mongoengine import connect
    from dotenv import load_dotenv

    # Ensure MongoDB connection in worker process
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "tuneleap_db")
    connect(db=db_name, host=mongo_uri, alias="default")

    try:
        feature_vector = extract_features(file_path)
        if isinstance(feature_vector, np.ndarray):
            repo = SongFeatureRepository()
            repo.create_or_update(song_id=song_id, feature_vector=feature_vector)
            return f"Features stored for song_id {song_id}"
        else:
            return f"Failed to extract features for song_id {song_id}: Not a numpy array"
    except Exception as e:
        return f"Error processing song_id {song_id}: {str(e)}"