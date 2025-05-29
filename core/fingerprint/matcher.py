from typing import Dict, List
from db.nosql.collections import Fingerprint

class FingerprintMatcher:
    """
    Matcher to find songs by comparing fingerprint hashes.
    """

    def __init__(self, threshold_strategy=None):
        from core.fingerprint.threshold import ExactMatchStrategy
        # Use provided strategy or default to exact matching
        self.strategy = threshold_strategy or ExactMatchStrategy()

    def match(self, fp_hash: str) -> Dict[int, int]:
        """
        Return a mapping of song_id to the number of matching fingerprints.
        """
        fps: List[Fingerprint] = self.strategy.get_matches(fp_hash)
        counts: Dict[int, int] = {}
        for fp in fps:
            counts[fp.song_id] = counts.get(fp.song_id, 0) + 1
        return counts
