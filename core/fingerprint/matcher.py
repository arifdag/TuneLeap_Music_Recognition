from typing import Dict, List, Optional
from db.nosql.collections import Fingerprint

class FingerprintMatcher:
    """
    Matcher to find songs by comparing fingerprint hashes and audio features.
    """

    def __init__(self, threshold_strategy=None):
        from core.fingerprint.threshold import ExactMatchStrategy
        # Use provided strategy or default to exact matching
        self.strategy = threshold_strategy or ExactMatchStrategy()

    def match(self, fp_hash: str, query_file_path: Optional[str] = None) -> Dict[int, int]:
        """
        Return a mapping of song_id to the number of matching fingerprints.
        
        Args:
            fp_hash: The fingerprint hash of the query audio
            query_file_path: Optional path to the query audio file for feature extraction
        """
        # Pass the query file path to strategies that support it
        if hasattr(self.strategy, 'get_matches'):
            try:
                # Try calling with query_file_path parameter
                fps: List[Fingerprint] = self.strategy.get_matches(fp_hash, query_file_path)
            except TypeError:
                # Fallback for strategies that don't support query_file_path
                fps: List[Fingerprint] = self.strategy.get_matches(fp_hash)
        else:
            fps: List[Fingerprint] = self.strategy.get_matches(fp_hash)
            
        counts: Dict[int, int] = {}
        for fp in fps:
            counts[fp.song_id] = counts.get(fp.song_id, 0) + 1
        return counts
