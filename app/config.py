import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# External storage configuration
DEFAULT_STORAGE_DIR = Path.home() / "PocketServerData" / "files"

STORAGE_DIR = Path(
    os.getenv("POCKET_SERVER_STORAGE", str(DEFAULT_STORAGE_DIR))
).expanduser().resolve()

# Automatically create storage directory
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Upload configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
CHUNK_SIZE = 1024 * 1024          # 1 MB