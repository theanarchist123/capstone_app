"""api/routes/auth.py"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from models.user import User
from schemas import (
    LoginRequest, RefreshRequest, TokenPair,
    UserCreate, UserOut, SuccessResponse
)
from api.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=SuccessResponse, status_code=201)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check duplicate
    existing = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        hospital=body.hospital,
        designation=body.designation,
        license_number=body.license_number,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return SuccessResponse(data=UserOut.model_validate(user), message="Registration successful")


@router.post("/login", response_model=SuccessResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    q = select(User).where(User.email == body.email, User.is_active == True)
    user = (await db.execute(q)).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access = create_access_token(str(user.id), user.role)
    refresh = create_refresh_token(str(user.id))
    return SuccessResponse(
        data=TokenPair(access_token=access, refresh_token=refresh),
        message="Login successful",
    )


@router.post("/refresh", response_model=SuccessResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    from jwt.exceptions import InvalidTokenError as JWTError
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        user_id = payload["sub"]
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    import uuid
    q = select(User).where(User.id == uuid.UUID(user_id), User.is_active == True)
    user = (await db.execute(q)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access = create_access_token(str(user.id), user.role)
    refresh = create_refresh_token(str(user.id))
    return SuccessResponse(data=TokenPair(access_token=access, refresh_token=refresh))


@router.post("/logout", response_model=SuccessResponse)
async def logout():
    # Stateless JWT — inform client to discard tokens
    return SuccessResponse(message="Logged out. Discard tokens on client side.")


@router.get("/me", response_model=SuccessResponse)
async def me(current_user: User = Depends(get_current_user)):
    return SuccessResponse(data=UserOut.model_validate(current_user))
