"""Veri modeli (MVP: SQLite WAL, tek kullanıcı)."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint


def simdi() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    locale: str = "tr"
    xp: int = 0
    streak: int = 0


class LabSession(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    challenge: str
    state: str = "hazirlaniyor"  # hazirlaniyor|saglikli|bitti|hata|kuyrukta
    started_at: datetime = Field(default_factory=simdi)
    expires_at: datetime
    flag_hash: str


class Attempt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="labsession.id")
    result: str  # dogru|yanlis|baska-oturum
    created_at: datetime = Field(default_factory=simdi)


class Progress(SQLModel, table=True):
    __table_args__ = (UniqueConstraint('user_id', 'slug'),)
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    slug: str
    status: str = "basladi"  # basladi|saldiri-tamam|tamam
    completed_at: datetime | None = None

class Hint(SQLModel, table=True):
    __table_args__ = (UniqueConstraint('user_id', 'slug'),)
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id')
    slug: str
    count: int = 0

class Activity(SQLModel, table=True):
    __table_args__ = (UniqueConstraint('user_id', 'day'),)
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id')
    day: str

class Audit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    action: str
    subject: str
    result: str
    created_at: datetime = Field(default_factory=simdi)
