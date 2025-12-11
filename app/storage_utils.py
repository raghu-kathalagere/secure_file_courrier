import os
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

def save_encrypted_file(original_filename: str, encrypted_bytes: bytes) -> str:
    """
    Save encrypted bytes to the data folder.
    Returns the stored_path (relative or absolute).
    """
    filename = secure_filename(original_filename)
    # Use UUID to avoid collisions and info leaks
    unique_name = f"{uuid.uuid4().hex}__{filename}"

    storage_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    with open(storage_path, "wb") as f:
        f.write(encrypted_bytes)

    return storage_path

def load_encrypted_file(stored_path: str) -> bytes:
    with open(stored_path, "rb") as f:
        return f.read()

def delete_file_if_exists(stored_path: str):
    if stored_path and os.path.exists(stored_path):
        os.remove(stored_path)
