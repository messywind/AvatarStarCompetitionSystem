import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    STATUS_APPROVED,
    Team,
    Tournament,
    registration_open,
    results_public,
)
from ..schemas import Bracket, TeamPublicOut, TournamentOut

router = APIRouter(prefix="/api/public", tags=["public"])


def _get_tournament_or_404(db: Session, tournament_id: int) -> Tournament:
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="赛事不存在")
    return t


def _tournament_out(db: Session, t: Tournament) -> TournamentOut:
    count = (
        db.query(Team)
        .filter(Team.tournament_id == t.id, Team.status == STATUS_APPROVED)
        .count()
    )
    return TournamentOut(
        id=t.id,
        name=t.name,
        description=t.description or "",
        registration_deadline=t.registration_deadline,
        registration_open=registration_open(t),
        results_public=results_public(t),
        team_count=count,
    )


@router.get("/tournaments", response_model=list[TournamentOut])
def list_tournaments(db: Session = Depends(get_db)):
    rows = db.query(Tournament).order_by(Tournament.created_at.desc()).all()
    return [_tournament_out(db, t) for t in rows]


@router.get("/tournaments/{tournament_id}", response_model=TournamentOut)
def get_tournament(tournament_id: int, db: Session = Depends(get_db)):
    return _tournament_out(db, _get_tournament_or_404(db, tournament_id))


@router.get("/tournaments/{tournament_id}/teams", response_model=list[TeamPublicOut])
def tournament_teams(tournament_id: int, db: Session = Depends(get_db)):
    """Approved teams — only visible to the public once registration has closed."""
    t = _get_tournament_or_404(db, tournament_id)
    if not results_public(t):
        raise HTTPException(status_code=403, detail="报名截止后才可查看参赛名单")
    return (
        db.query(Team)
        .filter(Team.tournament_id == t.id, Team.status == STATUS_APPROVED)
        .order_by(Team.name)
        .all()
    )


@router.get("/tournaments/{tournament_id}/bracket")
def tournament_bracket(tournament_id: int, db: Session = Depends(get_db)):
    """Bracket plus id->name lookup — only public once registration has closed."""
    t = _get_tournament_or_404(db, tournament_id)
    if not results_public(t):
        raise HTTPException(status_code=403, detail="报名截止后才可查看对阵图")
    bracket = Bracket(**json.loads(t.bracket_json)) if t.bracket_json else Bracket(rounds=[])
    teams = (
        db.query(Team)
        .filter(Team.tournament_id == t.id, Team.status == STATUS_APPROVED)
        .all()
    )
    team_map = {t.id: t.name for t in teams}
    return {"bracket": bracket.model_dump(), "teams": team_map}
