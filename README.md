## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Migrations](#database-migrations)
- [Running the Service](#running-the-service)
- [Usage](#usage)
- [Testing](#testing)
- [The Mobile App](#the-mobile-app)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

-----

## Project Overview

TuneLeap is a high-performance music recognition and recommendation engine. It provides:

  * A **FastAPI**-driven API for submitting audio files, managing users, and getting recommendations.
  * A **dual-database system** using **PostgreSQL** for structured data (users, song metadata) and **MongoDB** for audio fingerprints and feature vectors.
  * **Alembic** migrations to manage the SQL database schema.
  * A **Celery** worker that processes intensive audio tasks asynchronously.
  * **Docker-first design** for easy, consistent deployment.

-----

## Features
![transparency](https://github.com/user-attachments/assets/3373ec2b-5d76-4f6f-8f7e-185e904cdb32)



  * **Asynchronous Recognition**
    Jobs are enqueued using Celery and processed in the background by a dedicated worker, keeping the API responsive.

  * **Robust Audio Fingerprinting**
    Employs the `SpectralMatch` algorithm to generate and match fingerprints, enabling recognition of partial or noisy audio clips.

  * **Schema Migrations**
    Alembic safely tracks and applies changes to the PostgreSQL schema, enabling safe, iterative development.

  * **Interactive API Docs**
    FastAPI auto-generates Swagger UI and ReDoc for easy API exploration and testing at `/docs` and `/redoc`.

  * **Comprehensive Test Suite**
    A full suite of tests using Pytest ensures that core functionality remains stable and reliable.

-----

## Architecture

The system is designed with a service-oriented architecture, separating the API, background worker, and databases for scalability and maintainability.


![chart](https://github.com/user-attachments/assets/87aa2065-e2c1-48eb-bc4d-28c697e5978b)

  * **FastAPI Server**: Acts as the main entry point for all client application requests. It handles various API endpoints, including authentication, playlist management, song history, and recommendations.
  * **Core Components**: Contains the business logic, including modules for fingerprinting, database repositories, recommendation engine, security, and I/O operations.
  * **Database Models**: The system uses a dual-database approach:
      * **PostgreSQL**: Stores structured, relational data such as artists, albums, songs, users, playlists, and recognition history.
      * **MongoDB**: Stores audio fingerprints for fast and efficient matching.
  * **Celery Worker**: Offloads heavy tasks like audio processing and fingerprint extraction to run asynchronously, ensuring the API remains responsive.
  * **Redis Task Queue**: Manages the queue of tasks for the Celery worker.

-----

## Tech Stack

  * **Language**: Python 3.9+
  * **Web Framework**: FastAPI
  * **Web Server**: Gunicorn, Uvicorn
  * **ORM / ODM**: SQLAlchemy (SQL), MongoEngine (NoSQL)
  * **Migrations**: Alembic
  * **Task Queue**: Celery
  * **Broker / Cache**: Redis
  * **Database**: PostgreSQL, MongoDB
  * **Testing**: Pytest
  * **Mobile App**: Flutter

-----

## Installation

This project is containerized with Docker for simple and reliable setup.

1.  **Clone the repository**

    ```bash
    git clone https://github.com/arifdag/TuneLeap-Music-Recognition.git
    cd TuneLeap-Music-Recognition
    ```

2.  **Create the environment file**
    Create a `.env` file in the project root. See the [Configuration](https://www.google.com/search?q=%23configuration) section below for the required variables.

3.  **Build and run the services**

    ```bash
    docker-compose up --build
    ```

-----

## Configuration

Create a `.env` file in the project root and add the following environment variables.

```ini
# PostgreSQL Settings
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=tunedb
DATABASE_URL=postgresql://myuser:mypassword@postgres:5432/tunedb

# MongoDB Settings
MONGODB_URI=mongodb://mongo:27017
DB_NAME=tuneleap_db

# Redis (Celery) Settings
CELERY_BROKER_URL=redis://redis:6379/0

# JWT Settings
SECRET_KEY=A_VERY_SECRET_KEY_SHOULD_BE_PLACED_HERE
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Settings
PORT=8000
WEB_CONCURRENCY=4
LOG_LEVEL=info
```

-----

## Database Migrations

After making changes to the SQLAlchemy models in `db/sql/models.py`, generate a new migration file.

```bash
# Generate a new revision
docker-compose exec api alembic revision --autogenerate -m "Describe your model changes"

# Apply the migration to the database
docker-compose exec api alembic upgrade head
```

-----

## Running the Service

1.  **Start all services**

    ```bash
    docker-compose up
    ```

    This command starts the API server, the Celery worker, and the databases. The `run.sh` script handles the startup process inside the container.
-----

## Usage

The primary interaction involves uploading an audio file and polling for the result.

### 1\. Submit an Audio File for Recognition

Send a `POST` request with a multipart/form-data payload containing the audio file.

`POST /recognize/`

**Request:**

```http
POST /recognize/ HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW

------WebKitFormBoundary7MA4YWxkTrZu0gW
Content-Disposition: form-data; name="file"; filename="my-recording.wav"
Content-Type: audio/wav

<audio file binary content>
------WebKitFormBoundary7MA4YWxkTrZu0gW--
```

**Success Response (202 Accepted):**
The API immediately returns a `task_id`.

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

### 2\. Check Recognition Result

Poll the results endpoint using the `task_id` from the previous step.

`GET /recognize/result/{task_id}`

**Pending Response:**

```json
{
  "status": "PENDING"
}
```

**Completed Response (200 OK):**

```json
{
  "status": "SUCCESS",
  "results": [
    {
      "song_id": 101,
      "probability": 0.98,
      "match_score": 150,
      "title": "Bohemian Rhapsody",
      "artist_id": 25,
      "artist_name": "Queen",
      "album_id": 42,
      "album_name": "A Night at the Opera",
      "album_image": "http://example.com/album_art.jpg"
    }
  ]
}
```

-----

## Testing

Run the full test suite using Pytest. The command will discover and run all tests in the `tests/` directory.

```bash
pytest
```

-----

## The Mobile App

This project includes a fully-featured Flutter application that consumes the API.

| Login Screen                                      | Recognition Screen                                      | Result Screen                                    |
| ------------------------------------------------- | ------------------------------------------------------- | ------------------------------------------------ |
|![image](https://github.com/user-attachments/assets/8b67c82d-ac49-4e47-b300-72eb4a5d7b35)| ![image](https://github.com/user-attachments/assets/0aa30245-6e84-4255-9675-0e5a3577b0aa)| ![image](https://github.com/user-attachments/assets/95bcca55-bd09-4df4-910f-6a137f774ba6) |

-----

## Contributing

Contributions are welcome\! Please follow these steps:

1.  Fork this repository.
2.  Create a feature branch (`git checkout -b feat/YourAmazingFeature`).
3.  Commit your changes (`git commit -m "Add some amazing feature"`).
4.  Push to your branch (`git push origin feat/YourAmazingFeature`).
5.  Open a Pull Request.

Please ensure your code adheres to the existing style and that you add tests for any new features.

-----

## License

This project is licensed under the MIT License.

-----

## Contact

`dg.arifdag@gmail.com`
