from abc import ABC, abstractmethod
from typing import List
from db.nosql.collections import Fingerprint

class ThresholdStrategy(ABC):
    """
    Abstract base class for fingerprint matching strategies.
    """

    @abstractmethod
    def get_matches(self, fp_hash: str) -> List[Fingerprint]:
        """
        Return list of Fingerprint docs matching the strategy.
        """
        pass

class ExactMatchStrategy(ThresholdStrategy):
    """
    Strategy that matches fingerprints with exact hash equality.
    """

    def get_matches(self, fp_hash: str) -> List[Fingerprint]:
        return list(Fingerprint.objects(hash=fp_hash))
