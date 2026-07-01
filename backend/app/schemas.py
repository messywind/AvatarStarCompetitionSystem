import json
from collections import Counter
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import PROFESSIONS, REGISTRATION_SOLO, REGISTRATION_TEAM

REGISTRATION_TYPES = (REGISTRATION_TEAM, REGISTRATION_SOLO)

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


class PosterConfig(BaseModel):
    """Configurable poster content for a tournament (rules + rewards)."""

    # 参赛规则
    format: str = Field(default="", max_length=2000)            # 比赛形式
    profession_limit: str = Field(default="", max_length=2000)  # 职业限制
    mode_limit: str = Field(default="", max_length=2000)        # 模式限制
    item_limit: str = Field(default="", max_length=2000)        # 药物及道具限制
    equipment_limit: str = Field(default="", max_length=2000)   # 装备限制
    other_limit: str = Field(default="", max_length=2000)       # 其他限制
    # 官方奖励
    reward_champion: str = Field(default="", max_length=2000)   # 冠军奖励
    reward_runner_up: str = Field(default="", max_length=2000)  # 亚军奖励
    reward_third: str = Field(default="", max_length=2000)      # 季军奖励
    reward_fourth: str = Field(default="", max_length=2000)     # 殿军奖励
    reward_other: str = Field(default="", max_length=2000)      # 其他奖励


def poster_from_json(raw: str | None) -> "PosterConfig":
    if not raw:
        return PosterConfig()
    try:
        return PosterConfig(**json.loads(raw))
    except (ValueError, TypeError):
        return PosterConfig()


class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    registration_deadline: datetime
    poster: Optional[PosterConfig] = None


class TournamentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)
    registration_deadline: Optional[datetime] = None
    poster: Optional[PosterConfig] = None


class TournamentOut(BaseModel):
    id: int
    name: str
    description: str
    registration_deadline: datetime
    registration_open: bool
    results_public: bool
    team_count: int = 0
    poster: PosterConfig = PosterConfig()


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
    registration_type: str = REGISTRATION_TEAM
    name: str = Field(default="", max_length=128)
    captain: str = Field(default="", max_length=64)
    contact: str = Field(min_length=1, max_length=128)
    declaration: str = Field(default="", max_length=2000)
    players: list[PlayerIn]

    @field_validator("registration_type")
    @classmethod
    def valid_registration_type(cls, v: str) -> str:
        if v not in REGISTRATION_TYPES:
            raise ValueError("报名类型不合法")
        return v

    @field_validator("contact")
    @classmethod
    def valid_contact(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("请填写联系方式")
        return v.strip()

    @model_validator(mode="after")
    def validate_roster(self):
        formal = [p for p in self.players if not p.is_substitute]
        if self.registration_type != REGISTRATION_SOLO and len(self.players) == 1 and len(formal) == 1:
            self.registration_type = REGISTRATION_SOLO

        if self.registration_type == REGISTRATION_SOLO:
            if len(self.players) != 1 or len(formal) != 1:
                raise ValueError("个人报名必须且只能填写 1 位正式选手")
            if self.players[0].is_substitute:
                raise ValueError("个人报名选手不能标记为替补")
            return self

        if not self.name.strip():
            raise ValueError("请填写队伍名称")
        if not self.captain.strip():
            raise ValueError("请填写队长")
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

    registration_type: Optional[str] = None
    name: Optional[str] = Field(default=None, max_length=128)
    captain: Optional[str] = Field(default=None, max_length=64)
    contact: Optional[str] = Field(default=None, max_length=128)
    declaration: Optional[str] = Field(default=None, max_length=2000)
    players: Optional[list[PlayerIn]] = None

    @field_validator("registration_type")
    @classmethod
    def valid_registration_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in REGISTRATION_TYPES:
            raise ValueError("报名类型不合法")
        return v

    @field_validator("contact")
    @classmethod
    def valid_contact(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("请填写联系方式")
        return v.strip() if v is not None else v

    @model_validator(mode="after")
    def validate_roster(self):
        if self.players is not None:
            formal = [p for p in self.players if not p.is_substitute]
            if self.registration_type != REGISTRATION_SOLO and len(self.players) == 1 and len(formal) == 1:
                self.registration_type = REGISTRATION_SOLO

            if self.registration_type == REGISTRATION_SOLO:
                if len(self.players) != 1 or len(formal) != 1:
                    raise ValueError("个人报名必须且只能填写 1 位正式选手")
                if self.players[0].is_substitute:
                    raise ValueError("个人报名选手不能标记为替补")
            else:
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
    registration_type: str
    name: str
    captain: str
    contact: str
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
    registration_type: str
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
