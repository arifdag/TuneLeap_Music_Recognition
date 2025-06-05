import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.main import app
from db.sql.models import Base
from db.sql.database import get_db

# Import the module whose attributes we want to patch
from core.security import security as core_security_module

# --- Now, import application components and other necessary modules ---
import mongoengine
import mongomock

# --- Database Fixtures ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    return create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

@pytest.fixture(scope="function")
def sqlite_session(engine):
    Base.metadata.create_all(bind=engine) # Create tables
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine) # Drop tables after test

# --- App and Client Fixtures ---
@pytest.fixture(scope="function")
def client(sqlite_session, monkeypatch):
    # Dependency override for get_db
    def override_get_db():
        try:
            yield sqlite_session
        finally:
            pass # Session is closed by its own fixture

    app.dependency_overrides[get_db] = override_get_db

    # Monkeypatch the SECRET_KEY in the core.security.security module.
    # This ensures that create_access_token (imported by api.v1.auth)
    # uses this specific key for the duration of the test.
    monkeypatch.setattr(core_security_module, "SECRET_KEY", "fallback-secret-key-for-dev")
    
    # ALGORITHM is hardcoded in core.security.security.py as "HS256"
    # and TEST_DECODE_ALGORITHM in test_auth.py is "HS256", so they match.


    with TestClient(app) as c:
        yield c

    # Clean up dependency override
    del app.dependency_overrides[get_db]
    # monkeypatch automatically reverts its changes after the fixture scope ends.

# --- MongoDB Mocking Fixture (if not already in test_api_endpoints.py or similar) ---
@pytest.fixture(scope="session", autouse=True) # Changed to session scope
def mongo_connection_session():
    """
    Connect to mongomock in-memory for the test session.
    Autouse=True means it runs for every test session.
    """
    # Ensure no previous connections are active if tests run multiple times in one go
    try:
        mongoengine.disconnect()
    except mongoengine.connection.MongoEngineConnectionError:
        pass # No active connection, which is fine

    mongo_client_instance = mongoengine.connect(
        db="testdb_auth", # Use a distinct DB name for this test session if needed
        host="mongodb://localhost", # mongomock intercepts this
        mongo_client_class=mongomock.MongoClient,
        alias="default" # Ensure this is the alias your app uses or override
    )
    yield mongo_client_instance # Provide the client if needed, though connect sets global state

    mongoengine.disconnect(alias="default")