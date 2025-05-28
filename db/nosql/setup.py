from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "musicdb"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def init_fingerprint_indexes():
    # Ensure an index on the fingerprint hash for fast lookups
    await db.fingerprints.create_index("hash")
    # Ensure an index on song_id for efficient song-based queries
    await db.fingerprints.create_index("song_id")
