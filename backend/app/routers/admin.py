import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import hash_password
from ..database import get_db
from ..deps import require_admin
from ..models import (
    Player,
    REGISTRATION_SOLO,
    Team,
    Tournament,
    User,
    registration_open,
    results_public,
)
from ..schemas import (
    AdminTeamCreate,
    AdminUserCreate,
    AdminUserOut,
    AdminUserRoleUpdate,
    Bracket,
    TeamOut,
    TeamReview,
    TeamUpdate,
    TournamentCreate,
    TournamentOut,
    TournamentUpdate,
    poster_from_json,
)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _normalize_team_fields(payload) -> tuple[str, str]:
    if payload.registration_type == REGISTRATION_SOLO:
        nickname = payload.players[0].nickname.strip()
        return (nickname, nickname)
    return (payload.name.strip(), payload.captain.strip())


def _get_team_or_404(db: Session, team_id: int) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    return team


def _get_tournament_or_404(db: Session, tournament_id: int) -> Tournament:
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="赛事不存在")
    return t


def _tournament_out(db: Session, t: Tournament) -> TournamentOut:
    count = db.query(Team).filter(Team.tournament_id == t.id).count()
    return TournamentOut(
        id=t.id,
        name=t.name,
        description=t.description or "",
        registration_deadline=t.registration_deadline,
        registration_open=registration_open(t),
        results_public=results_public(t),
        team_count=count,
        poster=poster_from_json(t.poster_json),
    )


# ---------- Tournaments ----------


@router.get("/tournaments", response_model=list[TournamentOut])
def list_tournaments(db: Session = Depends(get_db)):
    rows = db.query(Tournament).order_by(Tournament.created_at.desc()).all()
    return [_tournament_out(db, t) for t in rows]


@router.post("/tournaments", response_model=TournamentOut, status_code=201)
def create_tournament(payload: TournamentCreate, db: Session = Depends(get_db)):
    t = Tournament(
        name=payload.name,
        description=payload.description,
        registration_deadline=payload.registration_deadline,
        poster_json=payload.poster.model_dump_json() if payload.poster else "",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _tournament_out(db, t)


@router.put("/tournaments/{tournament_id}", response_model=TournamentOut)
def update_tournament(tournament_id: int, payload: TournamentUpdate, db: Session = Depends(get_db)):
    t = _get_tournament_or_404(db, tournament_id)
    if payload.name is not None:
        t.name = payload.name
    if payload.description is not None:
        t.description = payload.description
    if payload.registration_deadline is not None:
        t.registration_deadline = payload.registration_deadline
    if payload.poster is not None:
        t.poster_json = payload.poster.model_dump_json()
    db.commit()
    db.refresh(t)
    return _tournament_out(db, t)


@router.delete("/tournaments/{tournament_id}", status_code=204)
def delete_tournament(tournament_id: int, db: Session = Depends(get_db)):
    t = _get_tournament_or_404(db, tournament_id)
    if db.query(Tournament).count() <= 1:
        raise HTTPException(status_code=400, detail="至少需要保留一个赛事")
    db.delete(t)
    db.commit()


# ---------- Users ----------


def _user_out(u: User, team_count: int) -> AdminUserOut:
    return AdminUserOut(
        id=u.id, username=u.username, role=u.role, created_at=u.created_at, team_count=team_count
    )


@router.get("/users", response_model=list[AdminUserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id).all()
    counts = dict(db.query(Team.owner_id, func.count(Team.id)).group_by(Team.owner_id).all())
    return [_user_out(u, counts.get(u.id, 0)) for u in users]


@router.post("/users", response_model=AdminUserOut, status_code=201)
def create_user(payload: AdminUserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_out(user, 0)


@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
def update_user_role(
    user_id: int,
    payload: AdminUserRoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="账号不存在")
    if user.id == admin.id and payload.role != "admin":
        raise HTTPException(status_code=400, detail="不能取消自己的管理员身份")
    user.role = payload.role
    db.commit()
    team_count = db.query(Team).filter(Team.owner_id == user.id).count()
    return _user_out(user, team_count)


# ---------- Teams ----------


@router.get("/teams", response_model=list[TeamOut])
def list_all_teams(
    status: str | None = None,
    registration_type: str | None = None,
    tournament_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Team)
    if tournament_id is not None:
        q = q.filter(Team.tournament_id == tournament_id)
    if status:
        q = q.filter(Team.status == status)
    if registration_type:
        q = q.filter(Team.registration_type == registration_type)
    return q.order_by(Team.created_at.desc()).all()


@router.post("/teams", response_model=TeamOut, status_code=201)
def create_team(
    payload: AdminTeamCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin manually adds a team; owned by the admin account, status set directly."""
    _get_tournament_or_404(db, payload.tournament_id)
    name, captain = _normalize_team_fields(payload)
    team = Team(
        tournament_id=payload.tournament_id,
        registration_type=payload.registration_type,
        name=name,
        captain=captain,
        contact=payload.contact.strip(),
        declaration=payload.declaration,
        owner_id=admin.id,
        status=payload.status,
    )
    team.players = [
        Player(nickname=p.nickname, profession=p.profession, is_substitute=p.is_substitute)
        for p in payload.players
    ]
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/teams/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    return _get_team_or_404(db, team_id)


@router.put("/teams/{team_id}", response_model=TeamOut)
def edit_team(team_id: int, payload: TeamUpdate, db: Session = Depends(get_db)):
    team = _get_team_or_404(db, team_id)
    next_registration_type = payload.registration_type or team.registration_type
    if payload.registration_type is not None:
        team.registration_type = payload.registration_type
    if payload.name is not None:
        team.name = payload.name
    if payload.captain is not None:
        team.captain = payload.captain
    if payload.contact is not None:
        team.contact = payload.contact.strip()
    if payload.declaration is not None:
        team.declaration = payload.declaration
    if payload.players is not None:
        team.players.clear()
        db.flush()
        team.players = [
            Player(nickname=p.nickname, profession=p.profession, is_substitute=p.is_substitute)
            for p in payload.players
        ]
        if next_registration_type == REGISTRATION_SOLO and payload.players:
            nickname = payload.players[0].nickname.strip()
            team.name = nickname
            team.captain = nickname
    db.commit()
    db.refresh(team)
    return team


@router.patch("/teams/{team_id}/review", response_model=TeamOut)
def review_team(team_id: int, payload: TeamReview, db: Session = Depends(get_db)):
    team = _get_team_or_404(db, team_id)
    team.status = payload.status
    team.review_note = payload.review_note
    db.commit()
    db.refresh(team)
    return team


@router.delete("/teams/{team_id}", status_code=204)
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = _get_team_or_404(db, team_id)
    db.delete(team)
    db.commit()


# ---------- Bracket (per tournament) ----------


@router.get("/tournaments/{tournament_id}/bracket", response_model=Bracket)
def get_bracket(tournament_id: int, db: Session = Depends(get_db)):
    t = _get_tournament_or_404(db, tournament_id)
    if not t.bracket_json:
        return Bracket(rounds=[])
    return Bracket(**json.loads(t.bracket_json))


@router.put("/tournaments/{tournament_id}/bracket", response_model=Bracket)
def save_bracket(tournament_id: int, payload: Bracket, db: Session = Depends(get_db)):
    t = _get_tournament_or_404(db, tournament_id)
    t.bracket_json = payload.model_dump_json()
    db.commit()
    return payload


@router.get("/users", response_model=list[dict])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id).all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]
