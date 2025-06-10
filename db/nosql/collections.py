from mongoengine import Document, IntField, StringField, DateTimeField, ListField, FloatField
from datetime import datetime

class Fingerprint(Document):
    meta = {
        "collection": "fingerprints",
        "indexes": [
            "hash",  # fast query by fingerprint hash
            "song_id",  # query by song identifier
            {"fields": ["hash", "song_id"], "unique": False},
            ("hash", "time_offset")  # For efficient Shazam-style lookups
        ]
    }

    # ID of the song this fingerprint belongs to
    song_id = IntField(required=True)
    # Hash string representing the audio fingerprint
    hash = StringField(required=True)
    # Time offset in frames (for Shazam-style matching)
    time_offset = IntField(default=0)
    # Timestamp when this fingerprint document was created
    created_at = DateTimeField(default=datetime.utcnow)

class SongFeature(Document):
    meta = {
        "collection": "song_features",
        "indexes": [
            "song_id", # Query by song ID
        ]
    }
    song_id = IntField(required=True, unique=True) # SQL Song ID
    feature_vector = ListField(FloatField(), required=True) # Store feature vector as list of floats
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super(SongFeature, self).save(*args, **kwargs)
