from collections import Counter
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import PROFESSIONS

# ---------- Auth ----------


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class PasswordChange(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


# ---------- Tournaments ----------


class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    registration_deadline: datetime


class TournamentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)
    registration_deadline: Optional[datetime] = None


class TournamentOut(BaseModel):
    id: int
    name: str
    description: str
    registration_deadline: datetime
    registration_open: bool
    results_public: bool
    team_count: int = 0


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Players / Teams ----------


class PlayerIn(BaseModel):
    nickname: str = Field(min_length=1, max_length=64)
    profession: str
    is_substitute: bool = False

    @field_validator("profession")
    @classmethod
    def valid_profession(cls, v: str) -> str:
        if v not in PROFESSIONS:
            raise ValueError(f"职业必须是 {PROFESSIONS} 之一")
        return v


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nickname: str
    profession: str
    is_substitute: bool


class TeamCreate(BaseModel):
    tournament_id: int
    name: str = Field(min_length=1, max_length=128)
    captain: str = Field(min_length=1, max_length=64)
    declaration: str = Field(default="", max_length=2000)
    players: list[PlayerIn]

    @model_validator(mode="after")
    def validate_roster(self):
        formal = [p for p in self.players if not p.is_substitute]

        # exactly five formal members
        if len(formal) != 5:
            raise ValueError("正式队员必须严格为 5 人")

        # profession distribution rules (only formal players count)
        counts = Counter(p.profession for p in formal)
        for prof in PROFESSIONS:
            c = counts.get(prof, 0)
            if c == 0:
                raise ValueError(f"职业「{prof}」的人数不得为 0")
            if c > 2:
                raise ValueError(f"职业「{prof}」的人数不得超过 2 个")

        # substitutes: unlimited count, but if present must still be valid professions
        # (validated per-field already)
        return self


class AdminTeamCreate(TeamCreate):
    """Admin manually adds a team; may set the initial review status directly."""

    status: str = "approved"

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        if v not in ("approved", "rejected", "pending"):
            raise ValueError("状态不合法")
        return v


class TeamUpdate(BaseModel):
    """Admin edit — all fields optional; if players provided, same roster rules apply."""

    name: Optional[str] = Field(default=None, max_length=128)
    captain: Optional[str] = Field(default=None, max_length=64)
    declaration: Optional[str] = Field(default=None, max_length=2000)
    players: Optional[list[PlayerIn]] = None

    @model_validator(mode="after")
    def validate_roster(self):
        if self.players is not None:
            formal = [p for p in self.players if not p.is_substitute]
            if len(formal) != 5:
                raise ValueError("正式队员必须严格为 5 人")
            counts = Counter(p.profession for p in formal)
            for prof in PROFESSIONS:
                c = counts.get(prof, 0)
                if c == 0:
                    raise ValueError(f"职业「{prof}」的人数不得为 0")
                if c > 2:
                    raise ValueError(f"职业「{prof}」的人数不得超过 2 个")
        return self


class TeamReview(BaseModel):
    status: str  # approved | rejected | pending
    review_note: str = Field(default="", max_length=255)

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        if v not in ("approved", "rejected", "pending"):
            raise ValueError("状态不合法")
        return v


class OwnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tournament_id: int
    name: str
    captain: str
    declaration: str
    status: str
    review_note: str
    owner: OwnerOut
    players: list[PlayerOut]
    created_at: datetime
    updated_at: datetime


class TeamPublicOut(BaseModel):
    """Public browsing view — no owner account details exposed."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    captain: str
    declaration: str
    players: list[PlayerOut]


# ---------- Bracket ----------


class BracketMatch(BaseModel):
    team1: Optional[int] = None  # team id or null
    team2: Optional[int] = None
    winner: Optional[int] = None


class BracketRound(BaseModel):
    name: str
    matches: list[BracketMatch]


class Bracket(BaseModel):
    rounds: list[BracketRound] = []
