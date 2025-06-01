import numpy as np
from typing import Dict, List, Tuple

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two 1D numpy arrays.
    """
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

class RecommenderEngine:
    """
    Given a mapping of song_id to feature vectors, compute top-N similar songs.
    """

    def __init__(self, feature_map: Dict[int, np.ndarray]):
        """
        :param feature_map: { song_id: feature_vector }
        """
        self.feature_map = feature_map

    def recommend(self, song_id: int, top_n: int = 5) -> List[Tuple[int, float]]:
        """
        Return a list of (other_song_id, similarity_score), sorted descending,
        excluding the input song_id itself.

        :param song_id: the query song ID
        :param top_n: how many recommendations to return
        :return: list of tuples
        """
        if song_id not in self.feature_map:
            return []

        query_vec = self.feature_map[song_id]
        scores: List[Tuple[int, float]] = []
        for sid, vec in self.feature_map.items():
            if sid == song_id:
                continue
            sim = cosine_similarity(query_vec, vec)
            scores.append((sid, sim))

        # Sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]
