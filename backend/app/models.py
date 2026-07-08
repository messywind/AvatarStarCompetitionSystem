from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# Team review states
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
REGISTRATION_TEAM = "team"
REGISTRATION_SOLO = "solo"

# The four allowed professions
PROFESSIONS = ["生化", "突击", "护卫", "重装"]


def registration_open(tournament: "Tournament") -> bool:
    """Registration is open until the deadline is reached."""
    return datetime.now() < tournament.registration_deadline


def results_public(tournament: "Tournament") -> bool:
    """Teams and bracket become public only once registration has closed."""
    return datetime.now() >= tournament.registration_deadline


class Tournament(Base):
    """A single competition edition, e.g. 百变兵团第一届选花杯."""

    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    # After this moment registration closes and teams/bracket become public.
    registration_deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Per-tournament bracket configuration, stored as JSON text.
    bracket_json: Mapped[str] = mapped_column(Text, default="")
    # Poster content (rules & rewards), stored as JSON text.
    poster_json: Mapped[str] = mapped_column(Text, default="")
    # Registration restrictions (allowed types & professions), stored as JSON text.
    # Empty means no restriction: both types, all professions.
    rules_json: Mapped[str] = mapped_column(Text, default="")
    # Card avatar image as a data URL; empty falls back to the frontend default.
    # MEDIUMTEXT on MySQL: base64 images easily exceed TEXT's 64KB cap.
    avatar: Mapped[str] = mapped_column(Text().with_variant(MEDIUMTEXT(), "mysql"), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    teams: Mapped[list["Team"]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="user", nullable=False)  # user | admin
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    teams: Mapped[list["Team"]] = relationship(back_populates="owner")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    registration_type: Mapped[str] = mapped_column(
        String(16), default=REGISTRATION_TEAM, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    captain: Mapped[str] = mapped_column(String(64), nullable=False)
    contact: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    declaration: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default=STATUS_PENDING, nullable=False)
    review_note: Mapped[str] = mapped_column(String(255), default="")

    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    tournament: Mapped["Tournament"] = relationship(back_populates="teams")
    owner: Mapped["User"] = relationship(back_populates="teams")
    players: Mapped[list["Player"]] = relationship(
        back_populates="team", cascade="all, delete-orphan", order_by="Player.id"
    )


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    nickname: Mapped[str] = mapped_column(String(64), nullable=False)
    profession: Mapped[str] = mapped_column(String(16), nullable=False)
    is_substitute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    team: Mapped["Team"] = relationship(back_populates="players")


class Setting(Base):
    """Generic key/value store. Used to persist the bracket configuration JSON."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
