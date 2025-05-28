from typing import List, Dict, Any, Optional

from db.nosql.collections import Fingerprint


class FingerprintRepository:
    """
    Repository for Fingerprint document: provides CRUD and bulk-insert operations.
    """

    def create(self, song_id: int, hash: str) -> Fingerprint:
        """
        Create and save a new Fingerprint document.
        """
        fp = Fingerprint(song_id=song_id, hash=hash)
        fp.save()
        return fp

    def get_by_id(self, fp_id: str) -> Optional[Fingerprint]:
        """
        Retrieve a Fingerprint by its MongoDB ObjectId.
        """
        return Fingerprint.objects(id=fp_id).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[Fingerprint]:
        """
        List fingerprints with pagination.
        """
        return list(
            Fingerprint.objects.skip(skip).limit(limit)
        )

    def delete(self, fp_id: str) -> bool:
        """
        Delete a Fingerprint document by its ObjectId.
        Returns True if deletion was acknowledged.
        """
        result = Fingerprint.objects(id=fp_id).delete()
        return result > 0

    def bulk_insert(
        self, fps_data: List[Dict[str, Any]]
    ) -> List[Fingerprint]:
        """
        Bulk-insert multiple Fingerprint documents.
        Each dict should have keys 'song_id' and 'hash'.
        """
        fps = [Fingerprint(**data) for data in fps_data]
        # .insert is faster than saving one by one
        Fingerprint.objects.insert(fps)
        return fps
