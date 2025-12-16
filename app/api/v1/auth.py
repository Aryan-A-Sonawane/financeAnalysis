"""Authentication endpoints."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from app.db.postgres import get_db
from app.models.database import User as DBUser
from app.models.schemas import Token, User, UserCreate
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Validate password strength
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters "
                   "and contain uppercase, lowercase, digit, and special character",
        )

    # Check if user exists
    result = await db.execute(
        select(DBUser).where(DBUser.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    password_hash = get_password_hash(user_data.password)
    db_user = DBUser(
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role,
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    logger.info("user_registered", user_id=str(db_user.user_id), email=db_user.email)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login and get access token."""
    # Find user
    result = await db.execute(
        select(DBUser).where(DBUser.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning("login_failed", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id), "email": user.email},
        expires_delta=access_token_expires,
    )
    
    logger.info("user_logged_in", user_id=str(user.user_id), email=user.email)
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def get_current_user_info(
    token_data = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user information."""
    from app.core.security import get_current_user
    
    result = await db.execute(
        select(DBUser).where(DBUser.user_id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user
