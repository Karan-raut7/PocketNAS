from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, UserResponse,LoginRequest,TokenResponse
from app.utils.security import hash_password,verify_password,create_access_token
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.scalar(
        select(User).where(
            (User.email == user_data.email) |
            (User.username == user_data.username)
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email or username already exists"
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login", response_model=TokenResponse)
def login(
    user_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if not user or not verify_password(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }