from pathlib import Path
from fastapi import HTTPException


ALLOWED_TYPES = {
    ".png": ("image/png",),
    ".jpg": ("image/jpeg",),
    ".jpeg": ("image/jpeg",),
    ".webp": ("image/webp",),
    ".pdf": ("application/pdf",),
    ".txt": ("text/plain",),
    ".mp4": ("video/mp4",)
}


def validate_file(filename: str, content: bytes) -> str:

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="File type not supported"
        )

    valid = False

    if extension == ".png":
        valid = content.startswith(b"\x89PNG\r\n\x1a\n")

    elif extension in [".jpg", ".jpeg"]:
        valid = content.startswith(b"\xff\xd8\xff")

    elif extension == ".webp":
        valid = (
            content.startswith(b"RIFF")
            and content[8:12] == b"WEBP"
        )

    elif extension == ".pdf":
        valid = content.startswith(b"%PDF-")

    elif extension == ".mp4":
        valid = len(content) >= 8 and content[4:8] == b"ftyp"

    elif extension == ".txt":
        valid = b"\x00" not in content

    if not valid:
        raise HTTPException(
            status_code=415,
            detail="File content does not match its extension"
        )

    return ALLOWED_TYPES[extension][0]