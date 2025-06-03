from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB URI and DB name from environment variables
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def init_fingerprint_indexes():
    # Ensure an index on the fingerprint hash for fast lookups
    await db.fingerprints.create_index("hash")
    # Ensure an index on song_id for efficient song-based queries
    await db.fingerprints.create_index("song_id")
