from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── Users ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentCreate(BaseModel):
    title: str = "Untitled Document"
    content: str = ""


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ShareOut(BaseModel):
    user: UserOut
    permission: str

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    owner: UserOut
    created_at: datetime
    updated_at: datetime
    role: Optional[str] = None          # 'owner' | 'editor' | 'viewer' — computed
    shares: List[ShareOut] = []

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    id: int
    title: str
    owner: UserOut
    updated_at: datetime
    role: str                           # 'owner' | 'editor' | 'viewer'

    model_config = {"from_attributes": True}


# ── Sharing ───────────────────────────────────────────────────────────────────

class ShareRequest(BaseModel):
    user_id: int
    permission: str                     # 'viewer' | 'editor'


class ShareResponse(BaseModel):
    document_id: int
    user_id: int
    permission: str

    model_config = {"from_attributes": True}


# Forward ref resolution
TokenResponse.model_rebuild()
