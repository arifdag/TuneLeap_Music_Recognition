from typing import List, Dict, Any, Optional, Tuple

from db.nosql.collections import Fingerprint


class FingerprintRepository:
    """
    Repository for Fingerprint document: provides CRUD and bulk-insert operations.
    """

    def create(self, song_id: int, hash: str, time_offset: int = 0) -> Fingerprint:
        """
        Create and save a new Fingerprint document.
        """
        fp = Fingerprint(song_id=song_id, hash=hash, time_offset=time_offset)
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

    def store_spectral_fingerprints(self, song_id: int, fingerprints: List[Tuple[str, int]]) -> int:
        """
        Store multiple SpectralMatch fingerprints for a song.
        Each fingerprint is a (hash, time_offset) tuple.
        Returns the number of fingerprints stored.
        """
        # Delete existing fingerprints for this song
        Fingerprint.objects(song_id=song_id).delete()
        
        # Prepare documents for bulk insert
        documents = []
        for hash_value, time_offset in fingerprints:
            doc = Fingerprint(
                song_id=song_id,
                hash=hash_value,
                time_offset=time_offset
            )
            documents.append(doc)
        
        if documents:
            Fingerprint.objects.insert(documents)
        
        return len(documents)

    def get_all_fingerprints_by_hash(self) -> Dict[str, List[Tuple[int, int]]]:
        """
        Get all fingerprints grouped by hash.
        Returns dict: {hash: [(song_id, time_offset), ...]}
        """
        result = {}

        # Query all fingerprints
        for fp in Fingerprint.objects():
            if fp.hash not in result:
                result[fp.hash] = []
            result[fp.hash].append((fp.song_id, fp.time_offset))

        return result
    
    def get_fingerprints_by_hashes(self, hashes: List[str]) -> Dict[str, List[Tuple[int, int]]]:
        """
        Get fingerprints for specific hashes.
        Returns dict: {hash: [(song_id, time_offset), ...]}
        """
        result = {}
        
        # Query fingerprints matching the given hashes
        fingerprints = Fingerprint.objects(hash__in=hashes)
        
        for fp in fingerprints:
            if fp.hash not in result:
                result[fp.hash] = []
            result[fp.hash].append((fp.song_id, fp.time_offset))
        
        return result
    
    def delete_by_song_id(self, song_id: int) -> int:
        """Delete all fingerprints for a song. Returns number deleted."""
        result = Fingerprint.objects(song_id=song_id).delete()
        return result

    def count_by_song_id(self, song_id: int) -> int:
        """Count fingerprints for a song."""
        return Fingerprint.objects(song_id=song_id).count()