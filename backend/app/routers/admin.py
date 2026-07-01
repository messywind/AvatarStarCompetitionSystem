import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
    Bracket,
    TeamOut,
    TeamReview,
    TeamUpdate,
    TournamentCreate,
    TournamentOut,
    TournamentUpdate,
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


# ---------- Teams ----------


@router.get("/teams", response_model=list[TeamOut])
def list_all_teams(
    status: str | None = None,
    tournament_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Team)
    if tournament_id is not None:
        q = q.filter(Team.tournament_id == tournament_id)
    if status:
        q = q.filter(Team.status == status)
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
