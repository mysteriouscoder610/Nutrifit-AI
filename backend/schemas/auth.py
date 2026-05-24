"""Auth-related Pydantic schemas with strict validation."""
from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from ..models.user import UserRole


_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
_PASSWORD_RULES = (
    re.compile(r"[A-Z]"),
    re.compile(r"[a-z]"),
    re.compile(r"\d"),
    re.compile(r"[^A-Za-z0-9]"),
)


def _validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    for rule in _PASSWORD_RULES:
        if not rule.search(value):
            raise ValueError(
                "Password must include upper, lower, number and special character"
            )
    return value


def _validate_mobile(value: str) -> str:
    if not re.fullmatch(r"\d{10}", value):
        raise ValueError("Mobile number must be exactly 10 digits")
    return value


def _validate_username(value: str) -> str:
    if len(value) < 3:
        raise ValueError("Username must be at least 3 characters")
    if not _USERNAME_RE.fullmatch(value):
        raise ValueError("Username may contain only letters, numbers and underscores")
    return value


class RegisterUser(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    username: str = Field(..., min_length=3, max_length=40)
    email: EmailStr
    mobile_number: str
    password: str

    _u = field_validator("username")(lambda cls, v: _validate_username(v))
    _m = field_validator("mobile_number")(lambda cls, v: _validate_mobile(v))
    _p = field_validator("password")(lambda cls, v: _validate_password(v))


class RegisterDietician(RegisterUser):
    speciality: str = Field(..., min_length=2, max_length=120)
    per_hour_charge: Decimal = Field(..., ge=0)
    per_two_hour_charge: Decimal = Field(..., ge=0)
    bio: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=120)


class LoginIn(BaseModel):
    username_or_email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: UUID
    name: str
    username: str
    email: EmailStr
    mobile_number: str
    role: UserRole

    model_config = {"from_attributes": True}


TokenOut.model_rebuild()
