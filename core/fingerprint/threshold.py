from abc import ABC, abstractmethod
from typing import List
from db.nosql.collections import Fingerprint
import numpy as np

class ThresholdStrategy(ABC):
    """
    Abstract base class for fingerprint matching strategies.
    """

    @abstractmethod
    def get_matches(self, fp_hash: str, query_file_path: str = None) -> List[Fingerprint]:
        """
        Return list of Fingerprint docs matching the strategy.
        
        Args:
            fp_hash: The fingerprint hash of the query audio
            query_file_path: Optional path to the query audio file for feature extraction
        """
        pass

class ExactMatchStrategy(ThresholdStrategy):
    """
    Strategy that matches fingerprints with exact hash equality.
    """

    def get_matches(self, fp_hash: str, query_file_path: str = None) -> List[Fingerprint]:
        return list(Fingerprint.objects(hash=fp_hash))

class SimilarityMatchStrategy(ThresholdStrategy):
    """
    Strategy that matches fingerprints based on feature similarity using stored audio features.
    Useful for partial song matching where exact hash won't work.
    """
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
    
    def _extract_query_features(self, file_path: str) -> np.ndarray:
        """
        Extract audio features from the uploaded file for comparison.
        """
        from core.reco.features import extract_features
        try:
            features = extract_features(file_path)
            if isinstance(features, np.ndarray) and len(features) > 0:
                return features
            return np.array([])
        except Exception as e:
            print(f"Error extracting features: {e}")
            return np.array([])
    
    def _compute_weighted_cosine_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Compute weighted cosine similarity optimized for partial song recognition.
        
        Feature weights (55 features total):
        - Chroma (12): Weight 2.0 - Most important for partial songs (harmony/melody)
        - MFCC mean (13): Weight 1.5 - Important for timbre
        - MFCC std (13): Weight 1.0 - Additional timbre info
        - Spectral features (6): Weight 1.2 - Texture characteristics  
        - Spectral contrast (7): Weight 1.3 - Musical style discrimination
        - Rhythm (2): Weight 0.8 - Less reliable for short clips
        - ZCR (2): Weight 0.7 - Least important for melody recognition
        """
        if len(features1) == 0 or len(features2) == 0:
            return 0.0
        
        # Ensure same length
        min_len = min(len(features1), len(features2))
        f1 = features1[:min_len]
        f2 = features2[:min_len]
        
        # Create feature weights (55 features)
        if min_len >= 55:
            weights = np.concatenate([
                np.full(12, 2.0),  # Chroma - highest weight
                np.full(13, 1.5),  # MFCC mean - high weight  
                np.full(13, 1.0),  # MFCC std - medium weight
                np.full(6, 1.2),   # Spectral features - medium-high weight
                np.full(7, 1.3),   # Spectral contrast - medium-high weight
                np.full(2, 0.8),   # Rhythm - lower weight for short clips
                np.full(2, 0.7)    # ZCR - lowest weight
            ])
        else:
            # Fallback to uniform weights if feature vector is different length
            weights = np.ones(min_len)
        
        weights = weights[:min_len]  # Ensure same length as features
        
        # Apply weights
        f1_weighted = f1 * weights
        f2_weighted = f2 * weights
        
        # Normalize vectors
        norm1 = np.linalg.norm(f1_weighted)
        norm2 = np.linalg.norm(f2_weighted)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Weighted cosine similarity
        return float(np.dot(f1_weighted, f2_weighted) / (norm1 * norm2))
    
    def get_matches(self, fp_hash: str, query_file_path: str = None) -> List[Fingerprint]:
        """
        Find fingerprints similar to the uploaded audio using stored features.
        
        Args:
            fp_hash: The fingerprint hash (not used in similarity matching)
            query_file_path: Path to the uploaded audio file for feature extraction
        """
        if not query_file_path:
            print("No query file path provided for similarity matching")
            return []
        
        # Extract features from the uploaded file
        query_features = self._extract_query_features(query_file_path)
        if len(query_features) == 0:
            print("Could not extract features from query file")
            return []
        
        matches = []
        similarity_scores = []
        
        try:
            # Get all stored song features
            from core.repository.song_feature_repository import SongFeatureRepository
            feature_repo = SongFeatureRepository()
            all_features = feature_repo.get_all_features()
            
            print(f"Comparing against {len(all_features)} stored songs")
            
            # Compare with each stored song's features
            for song_id, stored_features in all_features.items():
                similarity = self._compute_weighted_cosine_similarity(query_features, stored_features)
                similarity_scores.append((song_id, similarity))
                
                if similarity >= self.similarity_threshold:
                    # Get the fingerprint for this song to maintain consistency
                    fingerprints = list(Fingerprint.objects(song_id=song_id))
                    matches.extend(fingerprints)
            
            # Sort by similarity for debugging
            similarity_scores.sort(key=lambda x: x[1], reverse=True)
            print(f"Top 5 similarities: {similarity_scores[:5]}")
            print(f"Found {len(matches)} matches above threshold {self.similarity_threshold}")
            
        except Exception as e:
            print(f"Error in similarity matching: {e}")
            return []
        
        return matches

class FeatureBasedMatchStrategy(ThresholdStrategy):
    """
    A more advanced strategy that directly uses audio features for matching
    without requiring fingerprint hashes. This is better for partial song recognition.
    """
    
    def __init__(self, similarity_threshold: float = 0.6, max_results: int = 5):
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
    
    def _extract_query_features(self, file_path: str) -> np.ndarray:
        """Extract audio features from the uploaded file."""
        from core.reco.features import extract_features
        try:
            features = extract_features(file_path)
            if isinstance(features, np.ndarray) and len(features) > 0:
                return features
            return np.array([])
        except Exception as e:
            print(f"Error extracting features: {e}")
            return np.array([])
    
    def _compute_weighted_cosine_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Compute weighted cosine similarity optimized for partial song recognition.
        """
        if len(features1) == 0 or len(features2) == 0:
            return 0.0
        
        # Ensure same length
        min_len = min(len(features1), len(features2))
        f1 = features1[:min_len]
        f2 = features2[:min_len]
        
        # Create feature weights (55 features expected)
        if min_len >= 55:
            weights = np.concatenate([
                np.full(12, 2.0),  # Chroma - highest weight for harmony/melody
                np.full(13, 1.5),  # MFCC mean - high weight for timbre
                np.full(13, 1.0),  # MFCC std - medium weight
                np.full(6, 1.2),   # Spectral features - medium-high weight
                np.full(7, 1.3),   # Spectral contrast - medium-high weight
                np.full(2, 0.8),   # Rhythm - lower weight for short clips
                np.full(2, 0.7)    # ZCR - lowest weight
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
    
    def get_matches(self, fp_hash: str, query_file_path: str = None) -> List[Fingerprint]:
        """
        Find similar songs based on audio features and return their fingerprints 
        weighted by similarity scores.
        """
        if not query_file_path:
            return []
        
        query_features = self._extract_query_features(query_file_path)
        if len(query_features) == 0:
            return []
        
        try:
            from core.repository.song_feature_repository import SongFeatureRepository
            feature_repo = SongFeatureRepository()
            all_features = feature_repo.get_all_features()
            
            # Calculate similarities and sort
            similarities = []
            for song_id, stored_features in all_features.items():
                similarity = self._compute_weighted_cosine_similarity(query_features, stored_features)
                if similarity >= self.similarity_threshold:
                    similarities.append((song_id, similarity))
            
            # Sort by similarity descending and limit results
            similarities.sort(key=lambda x: x[1], reverse=True)
            similarities = similarities[:self.max_results]
            
            print(f"Feature-based matching found {len(similarities)} similar songs")
            if similarities:
                print(f"Best match: song_id={similarities[0][0]}, similarity={similarities[0][1]:.3f}")
                print(f"Top matches: {[(s[0], f'{s[1]:.3f}') for s in similarities]}")
            
            # Create weighted fingerprints based on similarity scores
            weighted_matches = []
            for song_id, similarity in similarities:
                # Get fingerprints for this song
                fingerprints = list(Fingerprint.objects(song_id=song_id))
                
                # Create multiple copies based on similarity score to weight the results
                # Scale similarity to get integer weights (multiply by 100 and round)
                weight = max(1, int(similarity * 100))  # Minimum weight of 1
                
                # Add weighted copies of fingerprints
                for _ in range(weight):
                    weighted_matches.extend(fingerprints)
            
            return weighted_matches
            
        except Exception as e:
            print(f"Error in feature-based matching: {e}")
            return []

class HybridMatchStrategy(ThresholdStrategy):
    """
    Strategy that first tries exact matching, then falls back to feature-based similarity matching.
    Best approach for partial song recognition.
    """
    
    def __init__(self, similarity_threshold: float = 0.65):
        self.exact_strategy = ExactMatchStrategy()
        self.feature_strategy = FeatureBasedMatchStrategy(similarity_threshold, max_results=3)
    
    def get_matches(self, fp_hash: str, query_file_path: str = None) -> List[Fingerprint]:
        # First try exact matching
        exact_matches = self.exact_strategy.get_matches(fp_hash)
        
        if exact_matches:
            print(f"Found {len(exact_matches)} exact matches")
            return exact_matches
        
        # Fall back to feature-based similarity matching
        print("No exact matches, trying weighted feature-based similarity matching...")
        return self.feature_strategy.get_matches(fp_hash, query_file_path)
