from mongoengine import Document, IntField, StringField, DateTimeField
from datetime import datetime

class Fingerprint(Document):
    meta = {
        "collection": "fingerprints",
        "indexes": [
            "hash",  # fast query by fingerprint hash
            "song_id",  # query by song identifier
            {"fields": ["hash", "song_id"], "unique": False}
        ]
    }

    # ID of the song this fingerprint belongs to
    song_id = IntField(required=True)
    # Hash string representing the audio fingerprint
    hash = StringField(required=True)
    # Timestamp when this fingerprint document was created
    created_at = DateTimeField(default=datetime.utcnow)
