"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.dietician import DieticianProfile
from ..models.user import User, UserRole
from ..schemas.auth import (
    LoginIn,
    RegisterDietician,
    RegisterUser,
    TokenOut,
    UserOut,
)
from ..utils.auth_utils import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _ensure_unique(db: Session, email: str, username: str) -> None:
    existing = (
        db.query(User)
        .filter(or_(User.email == email, User.username == username))
        .first()
    )
    if existing:
        if existing.email == email:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterUser, db: Session = Depends(get_db)) -> TokenOut:
    _ensure_unique(db, payload.email, payload.username)
    user = User(
        name=payload.name,
        username=payload.username,
        email=payload.email,
        mobile_number=payload.mobile_number,
        hashed_password=hash_password(payload.password),
        role=UserRole.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id), user.role.value)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post(
    "/register/dietician", response_model=TokenOut, status_code=status.HTTP_201_CREATED
)
def register_dietician(
    payload: RegisterDietician, db: Session = Depends(get_db)
) -> TokenOut:
    _ensure_unique(db, payload.email, payload.username)
    user = User(
        name=payload.name,
        username=payload.username,
        email=payload.email,
        mobile_number=payload.mobile_number,
        hashed_password=hash_password(payload.password),
        role=UserRole.dietician,
    )
    db.add(user)
    db.flush()
    profile = DieticianProfile(
        user_id=user.id,
        speciality=payload.speciality,
        per_hour_charge=payload.per_hour_charge,
        per_two_hour_charge=payload.per_two_hour_charge,
        bio=payload.bio,
        location=payload.location,
        is_available=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id), user.role.value)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = (
        db.query(User)
        .filter(
            or_(
                User.email == payload.username_or_email,
                User.username == payload.username_or_email,
            )
        )
        .first()
    )
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_access_token(str(user.id), user.role.value)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
