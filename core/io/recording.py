import os
import uuid
from fastapi import UploadFile

def save_temp(upload_file: UploadFile, dir: str) -> str:
    """
    Save an incoming UploadFile to a temporary file on disk.

    :param upload_file: FastAPI UploadFile instance
    :param dir: directory in which to write the temp file
    :return: full path to the saved file
    """
    # ensure target directory exists
    os.makedirs(dir, exist_ok=True)

    # generate a unique filename
    filename = f"{uuid.uuid4().hex}_{upload_file.filename}"
    path = os.path.join(dir, filename)

    # rewind and read all bytes
    upload_file.file.seek(0)
    content = upload_file.file.read()

    # write to disk
    with open(path, "wb") as f:
        f.write(content)

    return path
