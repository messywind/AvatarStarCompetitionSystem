import json
from collections import Counter
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import PROFESSIONS, REGISTRATION_SOLO, REGISTRATION_TEAM

REGISTRATION_TYPES = (REGISTRATION_TEAM, REGISTRATION_SOLO)
MAX_SUBSTITUTES = 1

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
    # 参赛公告（每行一条，支持 **文字** 高亮）
    announcement: str = Field(default="", max_length=4000)
    announcement_footer: str = Field(default="", max_length=200)  # 公告底部标语


def poster_from_json(raw: str | None) -> "PosterConfig":
    if not raw:
        return PosterConfig()
    try:
        return PosterConfig(**json.loads(raw))
    except (ValueError, TypeError):
        return PosterConfig()


class RegistrationRules(BaseModel):
    """Per-tournament registration restrictions (报名类型与可选职业)."""

    registration_types: list[str] = Field(default_factory=lambda: list(REGISTRATION_TYPES))
    professions: list[str] = Field(default_factory=lambda: list(PROFESSIONS))

    @field_validator("registration_types")
    @classmethod
    def valid_types(cls, v: list[str]) -> list[str]:
        v = list(dict.fromkeys(v))  # dedupe, keep order
        if not v:
            raise ValueError("至少允许一种报名类型")
        for t in v:
            if t not in REGISTRATION_TYPES:
                raise ValueError("报名类型不合法")
        return v

    @field_validator("professions")
    @classmethod
    def valid_professions(cls, v: list[str]) -> list[str]:
        v = list(dict.fromkeys(v))
        if not v:
            raise ValueError("至少允许一个职业")
        for p in v:
            if p not in PROFESSIONS:
                raise ValueError(f"职业必须是 {PROFESSIONS} 之一")
        return v


def rules_from_json(raw: str | None) -> "RegistrationRules":
    if not raw:
        return RegistrationRules()
    try:
        return RegistrationRules(**json.loads(raw))
    except (ValueError, TypeError):
        return RegistrationRules()


REGISTRATION_TYPE_LABEL = {REGISTRATION_TEAM: "战队报名", REGISTRATION_SOLO: "个人报名"}


def registration_rule_error(
    registration_type: str, players: list["PlayerIn"], rules: RegistrationRules
) -> str | None:
    """Check a signup against the tournament's rules. Returns a message or None."""
    if registration_type not in rules.registration_types:
        label = REGISTRATION_TYPE_LABEL.get(registration_type, registration_type)
        return f"该赛事不支持{label}"
    allowed = "/".join(rules.professions)
    for p in players:
        if p.profession not in rules.professions:
            return f"该赛事仅限职业 {allowed}，「{p.profession}」不可报名"
    return None


# 头像以 data URL 存库；前端上传前已压缩，这里再兜底限制大小（约 1.5MB 图片）
MAX_AVATAR_LENGTH = 2_000_000


def _valid_avatar(v: Optional[str]) -> Optional[str]:
    if not v:
        return v
    if not v.startswith("data:image/"):
        raise ValueError("头像必须是 data:image/ 开头的图片数据")
    if len(v) > MAX_AVATAR_LENGTH:
        raise ValueError("头像图片过大，请压缩后再上传")
    return v


class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    registration_deadline: datetime
    poster: Optional[PosterConfig] = None
    rules: Optional[RegistrationRules] = None
    avatar: str = ""

    @field_validator("avatar")
    @classmethod
    def check_avatar(cls, v: str) -> str:
        return _valid_avatar(v) or ""


class TournamentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = Field(default=None, max_length=2000)
    registration_deadline: Optional[datetime] = None
    poster: Optional[PosterConfig] = None
    rules: Optional[RegistrationRules] = None
    # None = 不修改；空字符串 = 清除头像（回退默认图）
    avatar: Optional[str] = None

    @field_validator("avatar")
    @classmethod
    def check_avatar(cls, v: Optional[str]) -> Optional[str]:
        return _valid_avatar(v)


class TournamentOut(BaseModel):
    id: int
    name: str
    description: str
    registration_deadline: datetime
    registration_open: bool
    results_public: bool
    team_count: int = 0
    poster: PosterConfig = PosterConfig()
    rules: RegistrationRules = RegistrationRules()
    avatar: str = ""


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Admin: user management ----------


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    role: str = "admin"

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("admin", "user"):
            raise ValueError("角色不合法")
        return v


class AdminUserRoleUpdate(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in ("admin", "user"):
            raise ValueError("角色不合法")
        return v


class AdminUserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime
    team_count: int = 0


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
        if len(self.players) - len(formal) > MAX_SUBSTITUTES:
            raise ValueError(f"替补队员最多 {MAX_SUBSTITUTES} 人")

        counts = Counter(p.profession for p in formal)
        for prof in PROFESSIONS:
            c = counts.get(prof, 0)
            # 生化可以缺席：缺出的名额换成一个非突击职业（护卫/重装），
            # 由每职业最多 2 人的上限保证突击不会借此超员
            if c == 0 and prof != "生化":
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
                if len(self.players) - len(formal) > MAX_SUBSTITUTES:
                    raise ValueError(f"替补队员最多 {MAX_SUBSTITUTES} 人")
                counts = Counter(p.profession for p in formal)
                for prof in PROFESSIONS:
                    c = counts.get(prof, 0)
                    # 生化可以缺席：缺出的名额换成一个非突击职业（护卫/重装）
                    if c == 0 and prof != "生化":
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

# Stage layouts understood by the frontend renderer:
#   elimination  — classic single-elimination tree with connectors
#   pairs        — parallel BO duels, no cross-round connectors
#   swiss        — round-robin/swiss rounds with an auto-computed standings table
#   double_final — 4-team double-elimination final (semis, loser final, winner final)
STAGE_TYPES = {"elimination", "pairs", "swiss", "double_final"}


class BracketMatch(BaseModel):
    team1: Optional[int] = None  # team id or null
    team2: Optional[int] = None
    winner: Optional[int] = None
    score1: Optional[int] = None  # e.g. 2 in a 2:1 BO3
    score2: Optional[int] = None


class BracketRound(BaseModel):
    name: str
    note: str = ""
    matches: list[BracketMatch]


class BracketStage(BaseModel):
    name: str
    type: str = "elimination"
    note: str = ""
    # Swiss stages: how many top-ranked teams advance (highlighted in the standings).
    advance: Optional[int] = None
    rounds: list[BracketRound] = []

    @field_validator("type")
    @classmethod
    def _known_type(cls, v: str) -> str:
        if v not in STAGE_TYPES:
            raise ValueError(f"未知的阶段类型: {v}")
        return v


class Bracket(BaseModel):
    stages: list[BracketStage] = []

    @model_validator(mode="before")
    @classmethod
    def _upgrade_legacy(cls, data):
        """Accept the pre-stage format {"rounds": [...]} and wrap it in one stage."""
        if isinstance(data, dict) and "stages" not in data:
            rounds = data.get("rounds") or []
            data = {"stages": [{"name": "淘汰赛", "type": "elimination", "rounds": rounds}]} if rounds else {"stages": []}
        return data
