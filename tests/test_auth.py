import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from jose import jwt


from api.main import app
from db.sql.models import User
from core.repository.user_repository import UserRepository
from core.security.security import get_password_hash


TEST_DECODE_SECRET_KEY = "fallback-secret-key-for-dev" # Matches the fallback in core.security.security.py
TEST_DECODE_ALGORITHM = "HS256"  # Assuming ALGORITHM in core.security.security.py defaults to or is set to HS256


@pytest.fixture(scope="function")
def test_user_data():
    return {
        "email": "testuser@example.com",
        "username": "testauthuser",
        "password": "testpassword123"
    }


@pytest.fixture(scope="function")
def created_user(sqlite_session: Session, test_user_data):
    user_repo = UserRepository(sqlite_session)
    existing_user = user_repo.get_user_by_email(test_user_data["email"])
    if existing_user:
        # Ensure user is active for the test
        if not existing_user.is_active:
            existing_user.is_active = True
            sqlite_session.commit()
            sqlite_session.refresh(existing_user)
        return existing_user

    hashed_password = get_password_hash(test_user_data["password"])
    user = User(
        email=test_user_data["email"],
        username=test_user_data["username"],
        hashed_password=hashed_password,
        is_active=True
    )
    sqlite_session.add(user)
    sqlite_session.commit()
    sqlite_session.refresh(user)
    return user


def test_register_new_user(client: TestClient, sqlite_session: Session, test_user_data):
    user_repo = UserRepository(sqlite_session)
    existing_user = user_repo.get_user_by_email(test_user_data["email"])
    if existing_user:  # Clean slate for this test
        sqlite_session.delete(existing_user)
        sqlite_session.commit()

    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert "id" in data
    assert data["is_active"] is True

    db_user = user_repo.get_user_by_email(test_user_data["email"])
    assert db_user is not None
    assert db_user.username == test_user_data["username"]


def test_register_duplicate_email(client: TestClient, created_user: User, test_user_data):
    new_user_data_same_email = {
        "email": test_user_data["email"],
        "username": "anotheruser",
        "password": "anotherpassword"
    }
    response = client.post("/auth/register", json=new_user_data_same_email)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in response.json()["detail"]


def test_register_duplicate_username(client: TestClient, created_user: User, test_user_data):
    new_user_data_same_username = {
        "email": "anotheremail@example.com",
        "username": test_user_data["username"],
        "password": "anotherpassword"
    }
    response = client.post("/auth/register", json=new_user_data_same_username)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already taken" in response.json()["detail"]


def test_login_for_access_token(client: TestClient, created_user: User, test_user_data):
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK, response.json()
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    token = data["access_token"]
    # Decode token using the key/algorithm the app is effectively using.
    payload = jwt.decode(token, TEST_DECODE_SECRET_KEY, algorithms=[TEST_DECODE_ALGORITHM])
    assert payload["sub"] == test_user_data["email"]


def test_login_incorrect_password(client: TestClient, created_user: User, test_user_data):
    login_data = {
        "username": test_user_data["email"],
        "password": "wrongpassword"
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_user_not_found(client: TestClient, test_user_data):
    login_data = {
        "username": "nonexistentuser@example.com",
        "password": test_user_data["password"]
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_inactive_user(client: TestClient, sqlite_session: Session, test_user_data, created_user: User):
    # Ensure we're modifying the user from the created_user fixture via the current session
    user_to_modify = sqlite_session.query(User).filter(User.id == created_user.id).first()
    assert user_to_modify is not None, "Created user not found in session for test_login_inactive_user"

    user_to_modify.is_active = False
    sqlite_session.commit()
    sqlite_session.refresh(user_to_modify)  # Ensure the change is reflected in the object

    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Inactive user" in response.json()["detail"]

    # Clean up: reactivate the user
    user_to_modify.is_active = True
    sqlite_session.commit()


def test_read_users_me_valid_token(client: TestClient, created_user: User, test_user_data, sqlite_session: Session):
    # Ensure the user is active for this test by fetching from current session and updating if necessary
    user_in_db = sqlite_session.query(User).filter(User.id == created_user.id).first()
    assert user_in_db is not None, "Created user not found in session for /me token test"
    if not user_in_db.is_active:
        user_in_db.is_active = True
        sqlite_session.commit()
        sqlite_session.refresh(user_in_db)

    login_data = {"username": test_user_data["email"], "password": test_user_data["password"]}
    login_response = client.post("/auth/token", data=login_data)
    assert login_response.status_code == status.HTTP_200_OK, f"Login failed: {login_response.json().get('detail')}"
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/auth/users/me", headers=headers)
    assert me_response.status_code == status.HTTP_200_OK, \
        f"GET /users/me failed: {me_response.status_code} - {me_response.json().get('detail') if me_response.content else 'No content'}"
    data = me_response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert data["id"] == created_user.id


def test_read_users_me_invalid_token(client: TestClient):
    response_no_token = client.get("/auth/users/me")
    assert response_no_token.status_code == status.HTTP_401_UNAUTHORIZED

    headers_invalid = {"Authorization": "Bearer invalidtokenstring"}
    response_invalid_token = client.get("/auth/users/me", headers=headers_invalid)
    assert response_invalid_token.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in response_invalid_token.json()["detail"]
