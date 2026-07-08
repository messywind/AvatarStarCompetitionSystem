import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .auth import hash_password
from .config import settings
from .database import Base, SessionLocal, engine, ensure_database_exists
from .models import Setting, Team, Tournament, User
from .routers import admin, auth, public, teams

DEFAULT_TOURNAMENT_NAME = "百变兵团第一届选花杯"
LEGACY_BRACKET_KEY = "bracket"

SECOND_TOURNAMENT_NAME = "百变兵团第二届选花杯"
SECOND_TOURNAMENT_FLAG = "bootstrap_xuanhua_2"  # 只自动创建一次，管理员删除后不再重建
SECOND_TOURNAMENT_RULES = {
    "registration_types": ["solo"],
    "professions": ["突击", "重装", "护卫"],
}
SECOND_TOURNAMENT_POSTER = {
    "format": "三职业 SOLO 单人赛",
    "profession_limit": "仅限 突击 / 重装 / 护卫 三职业\n本届不开放生化职业",
    "other_limit": "其余以赛事官方为准",
    "announcement": (
        "第二届选花杯为**三职业 SOLO 赛**\n"
        "仅限**突击 / 重装 / 护卫**职业报名\n"
        "采用**个人报名**，无需组队\n"
        "**8 月 8 日**正式开赛"
    ),
    "announcement_footer": "单人报名，8 月 8 日开战！",
}


def bootstrap_admin() -> None:
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not admin_user:
            db.add(
                User(
                    username=settings.ADMIN_USERNAME,
                    password_hash=hash_password(settings.ADMIN_PASSWORD),
                    role="admin",
                )
            )
            db.commit()
    finally:
        db.close()


def run_migrations() -> None:
    """Lightweight schema migration for pre-existing databases (no Alembic)."""
    # 仅针对存量 MySQL 库；SQLite 等本地开发库由 create_all 直接建全表
    if not engine.dialect.name.startswith("mysql"):
        return
    with engine.begin() as conn:
        col = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'teams' "
                "AND COLUMN_NAME = 'tournament_id'"
            )
        ).scalar()
        if not col:
            conn.execute(text("ALTER TABLE teams ADD COLUMN tournament_id INT NULL"))
            conn.execute(text("ALTER TABLE teams ADD INDEX ix_teams_tournament_id (tournament_id)"))

        registration_type_col = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'teams' "
                "AND COLUMN_NAME = 'registration_type'"
            )
        ).scalar()
        if not registration_type_col:
            conn.execute(
                text(
                    "ALTER TABLE teams "
                    "ADD COLUMN registration_type VARCHAR(16) NOT NULL DEFAULT 'team'"
                )
            )

        contact_col = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'teams' "
                "AND COLUMN_NAME = 'contact'"
            )
        ).scalar()
        if not contact_col:
            conn.execute(
                text(
                    "ALTER TABLE teams "
                    "ADD COLUMN contact VARCHAR(128) NOT NULL DEFAULT ''"
                )
            )

        poster_col = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tournaments' "
                "AND COLUMN_NAME = 'poster_json'"
            )
        ).scalar()
        if not poster_col:
            conn.execute(text("ALTER TABLE tournaments ADD COLUMN poster_json TEXT NULL"))

        rules_col = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tournaments' "
                "AND COLUMN_NAME = 'rules_json'"
            )
        ).scalar()
        if not rules_col:
            conn.execute(text("ALTER TABLE tournaments ADD COLUMN rules_json TEXT NULL"))

        avatar_col = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tournaments' "
                "AND COLUMN_NAME = 'avatar'"
            )
        ).scalar()
        if not avatar_col:
            # 头像为 base64 data URL，TEXT 的 64KB 不够用
            conn.execute(text("ALTER TABLE tournaments ADD COLUMN avatar MEDIUMTEXT NULL"))


def bootstrap_default_tournament() -> None:
    """Ensure at least one tournament exists and every team belongs to one.

    On first run this creates 百变兵团第一届选花杯, migrates the legacy global
    bracket into it, and back-fills every existing team's tournament_id.
    """
    db = SessionLocal()
    try:
        default = db.query(Tournament).order_by(Tournament.id).first()
        if not default:
            default = Tournament(
                name=DEFAULT_TOURNAMENT_NAME,
                description="百变兵团民间赛事 · 第一届选花杯",
                registration_deadline=datetime.now() + timedelta(days=30),
            )
            # Carry over the legacy single-bracket setting, if any.
            legacy = db.query(Setting).filter(Setting.key == LEGACY_BRACKET_KEY).first()
            if legacy and legacy.value:
                default.bracket_json = legacy.value
            db.add(default)
            db.commit()
            db.refresh(default)

        # Back-fill any teams that predate the multi-tournament model.
        db.query(Team).filter(Team.tournament_id.is_(None)).update(
            {Team.tournament_id: default.id}, synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


def bootstrap_second_tournament() -> None:
    """One-time creation of 第二届选花杯 (8.8 开赛，三职业 SOLO 赛).

    Guarded by a settings flag so it is not recreated if an admin deletes it.
    """
    db = SessionLocal()
    try:
        if db.query(Setting).filter(Setting.key == SECOND_TOURNAMENT_FLAG).first():
            return
        if not db.query(Tournament).filter(Tournament.name == SECOND_TOURNAMENT_NAME).first():
            db.add(
                Tournament(
                    name=SECOND_TOURNAMENT_NAME,
                    description="百变兵团民间赛事 · 第二届选花杯 · 三职业 SOLO 赛（8 月 8 日开赛）",
                    registration_deadline=datetime(2026, 8, 8, 0, 0, 0),
                    rules_json=json.dumps(SECOND_TOURNAMENT_RULES, ensure_ascii=False),
                    poster_json=json.dumps(SECOND_TOURNAMENT_POSTER, ensure_ascii=False),
                )
            )
        db.add(Setting(key=SECOND_TOURNAMENT_FLAG, value="done"))
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
    run_migrations()
    bootstrap_admin()
    bootstrap_default_tournament()
    bootstrap_second_tournament()
    yield


app = FastAPI(title="百变兵团选花杯 报名系统 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(admin.router)
app.include_router(public.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "event": "百变兵团选花杯"}
