import pytest
import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.reco.engine import RecommenderEngine
from core.reco.builder import PlaylistBuilder
from api.v1.song_recommendations import router as reco_router

@pytest.fixture
def sample_feature_map(monkeypatch):
    """
    Prepare a sample feature map with 3 songs:
      Song 1: vector [1, 0, 0]
      Song 2: vector [0.9, 0.1, 0]
      Song 3: vector [0, 1, 0]
    """
    feature_map_data = {
        1: np.array([1.0, 0.0, 0.0]),
        2: np.array([0.9, 0.1, 0.0]),
        3: np.array([0.0, 1.0, 0.0]),
    }
    monkeypatch.setattr("api.v1.playlists._feature_map_cache", feature_map_data.copy())
    monkeypatch.setattr("api.v1.playlists._feature_map_loaded", True)
    return feature_map_data

def test_cosine_similarity():
    from core.reco.engine import cosine_similarity
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 1.0, 0.0])
    c = np.array([1.0, 1.0, 0.0])
    assert pytest.approx(cosine_similarity(a, b)) == 0.0
    assert pytest.approx(cosine_similarity(a, c)) == pytest.approx(1.0 / np.sqrt(2))

def test_recommender_engine(sample_feature_map):
    engine = RecommenderEngine(sample_feature_map)
    # For song 1, best match is song 2, then song 3
    recs = engine.recommend(1, top_n=2)
    assert recs[0][0] == 2
    assert recs[1][0] == 3

def test_playlist_builder(sample_feature_map):
    builder = PlaylistBuilder(sample_feature_map)
    rec_list = builder.build(1, top_n=2)
    assert rec_list == [2, 3]

@pytest.fixture
def client_with_reco(sample_feature_map):
    app = FastAPI()
    app.include_router(reco_router)
    return TestClient(app)

def test_recommend_endpoint_success(client_with_reco):
    # Request recommendations for song_id=1
    response = client_with_reco.get("/recommend/1?top_n=2")
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    # Should return [2, 3] given the sample_feature_map
    assert result == [2, 3]

def test_recommend_endpoint_not_found(client_with_reco):
    # Request for a song_id not in feature_map
    response = client_with_reco.get("/recommend/999")
    assert response.status_code == 404
