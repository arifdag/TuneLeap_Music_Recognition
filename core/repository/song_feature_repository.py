from typing import List, Dict, Optional
import numpy as np
from db.nosql.collections import SongFeature

class SongFeatureRepository:
    def create_or_update(self, song_id: int, feature_vector: np.ndarray) -> SongFeature:
        feature_list = feature_vector.tolist()
        song_feature = SongFeature.objects(song_id=song_id).modify(
            upsert=True, # Create if not exists, update if it does
            new=True,    # Return the new/modified document
            set__song_id=song_id,
            set__feature_vector=feature_list
        )
        # modify might not automatically call save's updated_at logic, so handle manually if needed
        # or use `update_one` with `SongFeature.objects(song_id=song_id).update_one(...)`
        if not song_feature: # If upsert created a new one but modify didn't return it as expected
             song_feature = SongFeature(song_id=song_id, feature_vector=feature_list)
             song_feature.save()
        elif hasattr(song_feature, 'save'): # If it's a full document instance
            song_feature.save() # To trigger updated_at
        return song_feature

    def get_by_song_id(self, song_id: int) -> Optional[SongFeature]:
        return SongFeature.objects(song_id=song_id).first()

    def get_all_features(self) -> Dict[int, np.ndarray]:
        feature_map = {}
        for sf_doc in SongFeature.objects.all():
            feature_map[sf_doc.song_id] = np.array(sf_doc.feature_vector)
        return feature_map