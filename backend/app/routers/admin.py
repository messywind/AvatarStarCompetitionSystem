import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Player, Setting, Team, User
from ..schemas import Bracket, TeamOut, TeamReview, TeamUpdate

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])

BRACKET_KEY = "bracket"


def _get_team_or_404(db: Session, team_id: int) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="队伍不存在")
    return team


@router.get("/teams", response_model=list[TeamOut])
def list_all_teams(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Team)
    if status:
        q = q.filter(Team.status == status)
    return q.order_by(Team.created_at.desc()).all()


@router.get("/teams/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    return _get_team_or_404(db, team_id)


@router.put("/teams/{team_id}", response_model=TeamOut)
def edit_team(team_id: int, payload: TeamUpdate, db: Session = Depends(get_db)):
    team = _get_team_or_404(db, team_id)
    if payload.name is not None:
        team.name = payload.name
    if payload.captain is not None:
        team.captain = payload.captain
    if payload.declaration is not None:
        team.declaration = payload.declaration
    if payload.players is not None:
        team.players.clear()
        db.flush()
        team.players = [
            Player(nickname=p.nickname, profession=p.profession, is_substitute=p.is_substitute)
            for p in payload.players
        ]
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


# ---------- Bracket configuration ----------


@router.get("/bracket", response_model=Bracket)
def get_bracket(db: Session = Depends(get_db)):
    row = db.query(Setting).filter(Setting.key == BRACKET_KEY).first()
    if not row or not row.value:
        return Bracket(rounds=[])
    return Bracket(**json.loads(row.value))


@router.put("/bracket", response_model=Bracket)
def save_bracket(payload: Bracket, db: Session = Depends(get_db)):
    row = db.query(Setting).filter(Setting.key == BRACKET_KEY).first()
    value = payload.model_dump_json()
    if row:
        row.value = value
    else:
        db.add(Setting(key=BRACKET_KEY, value=value))
    db.commit()
    return payload


@router.get("/users", response_model=list[dict])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id).all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]
