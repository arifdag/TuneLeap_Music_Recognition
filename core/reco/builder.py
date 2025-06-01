from typing import List, Dict
from core.reco.engine import RecommenderEngine

class PlaylistBuilder:
    """
    Builds a playlist of recommended songs given precomputed features.
    """

    def __init__(self, feature_map: Dict[int, any]):
        """
        :param feature_map: { song_id: feature_vector }
        """
        self.engine = RecommenderEngine(feature_map)

    def build(self, song_id: int, top_n: int = 5) -> List[int]:
        """
        Return list of recommended song_ids.
        """
        recs = self.engine.recommend(song_id, top_n=top_n)
        # Only return song_id part
        return [song for song, _ in recs]
