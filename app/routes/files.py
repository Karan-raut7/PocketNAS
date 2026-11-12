import uuid
import shutil

from pathlib import Path
from sqlalchemy import select

from fastapi import Query
from sqlalchemy import func

from fastapi import status
from app.config import STORAGE_DIR, MAX_FILE_SIZE, CHUNK_SIZE
from app.utils.file_validation import validate_file

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File as FastAPIFile,
    HTTPException,
    Header,
    Query,
    status
)
from fastapi.responses import FileResponse as FastAPIFileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.file import File as FileModel
from app.models.user import User
from app.schemas.file import FileResponse
from app.utils.dependencies import get_current_user
from fastapi.responses import FileResponse as FastAPIFileResponse


router = APIRouter(
    prefix="/files",
    tags=["Files"]
)
@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file = db.scalar(
        select(FileModel).where(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        )
    )

    if not file:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    file_path = STORAGE_DIR / file.storage_key

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored file not found"
        )

    return FastAPIFileResponse(
        path=file_path,
        filename=file.filename,
        media_type=file.content_type
    )
def iter_file_range(file_path: Path, start: int, end: int, chunk_size: int = CHUNK_SIZE):
    """Yields chunks of bytes from start to end inclusive."""
    with file_path.open("rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_length = min(chunk_size, remaining)
            data = f.read(read_length)
            if not data:
                break
            remaining -= len(data)
            yield data



@router.get("/{file_id}/stream")
def stream_file(
    file_id: int,
    range: str | None = Header(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
   
    file = db.scalar(
        select(FileModel).where(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        )
    )

    if not file:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    file_path = STORAGE_DIR / file.storage_key

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored file not found"
        )

   
    file_size = file_path.stat().st_size
    media_type = file.content_type or "application/octet-stream"

    
    if range is None:
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Disposition": f'inline; filename="{file.filename}"',
        }
        return StreamingResponse(
            iter_file_range(file_path, 0, file_size - 1),
            status_code=200,
            media_type=media_type,
            headers=headers,
        )

    
    try:
        range_unit, range_spec = range.strip().split("=", 1)
        if range_unit.lower() != "bytes":
            raise ValueError("Unsupported range unit")

        start_str, end_str = range_spec.split("-", 1)

        if start_str == "":
            
            suffix_length = int(end_str)
            start = max(0, file_size - suffix_length)
            end = file_size - 1
        else:
            start = int(start_str)
            end = int(end_str) if end_str else file_size - 1

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Range header")

   
    if start < 0 or end >= file_size or start > end:
        raise HTTPException(
            status_code=416,
            detail="Requested Range Not Satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    content_length = end - start + 1
    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Disposition": f'inline; filename="{file.filename}"',
    }

    
    return StreamingResponse(
        iter_file_range(file_path, start, end),
        status_code=206,
        media_type=media_type,
        headers=headers,
    )

@router.get("/")
def list_files(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    offset = (page - 1) * limit

    total = db.scalar(
        select(func.count())
        .select_from(FileModel)
        .where(FileModel.owner_id == current_user.id)
    )

    files = db.scalars(
        select(FileModel)
        .where(FileModel.owner_id == current_user.id)
        .order_by(FileModel.uploaded_at.desc(), FileModel.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "files": files
    }

@router.post(
    "/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_file(
    uploaded_file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not uploaded_file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    original_filename = Path(uploaded_file.filename).name

    file_extension = Path(original_filename).suffix.lower()

    storage_key = f"{uuid.uuid4().hex}{file_extension}"

    file_path = STORAGE_DIR / storage_key

    file_size = 0

    try:
        first_chunk = await uploaded_file.read(CHUNK_SIZE)

        if not first_chunk:
            raise HTTPException(
                status_code=400,
                detail="Empty files are not allowed"
            )

        content_type = validate_file(
            original_filename,
            first_chunk
        )

        with file_path.open("xb") as buffer:

            chunk = first_chunk

            while chunk:
                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds maximum size of 50 MB"
                    )

                buffer.write(chunk)

                chunk = await uploaded_file.read(CHUNK_SIZE)

        new_file = FileModel(
            filename=original_filename,
            storage_key=storage_key,
            file_size=file_size,
            content_type=content_type,
            owner_id=current_user.id
        )

        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        return new_file

    except Exception:
        db.rollback()

        if file_path.exists():
            file_path.unlink()

        raise

    finally:
        await uploaded_file.close()

@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file = db.scalar(
        select(FileModel).where(
            FileModel.id == file_id,
            FileModel.owner_id == current_user.id
        )
    )

    if not file:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    file_path = STORAGE_DIR / file.storage_key

    if file_path.exists():
        file_path.unlink()

    db.delete(file)
    db.commit()

    return {"message": "File deleted successfully"}

