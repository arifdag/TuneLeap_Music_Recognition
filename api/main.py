﻿import os
from fastapi import FastAPI
from api.v1.songs import router as songs_router
from api.v1.recognition import router as recog_router
from api.v1.song_recommendations import router as rec_router, playlist_router
from api.v1 import auth as auth_router
from api.v1 import user_playlists as user_playlists_router
from api.v1 import user_history as user_history_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Music Recognition and Recommendation API",
    version="0.1.0"
)

# CORS (if mobile/web clients need it)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 routers
app.include_router(songs_router)
app.include_router(recog_router)
app.include_router(rec_router)
app.include_router(playlist_router)
app.include_router(auth_router.router, prefix="/auth")
app.include_router(user_playlists_router.router)
app.include_router(user_history_router.router)


@app.get("/health", tags=["health"])
def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}
