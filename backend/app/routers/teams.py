from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import (
    Player,
    Team,
    Tournament,
    User,
    REGISTRATION_SOLO,
    registration_open,
)
from ..schemas import TeamCreate, TeamOut

router = APIRouter(prefix="/api/teams", tags=["teams"])


def _normalize_team_fields(payload: TeamCreate) -> tuple[str, str]:
    if payload.registration_type == REGISTRATION_SOLO:
        nickname = payload.players[0].nickname.strip()
        return (nickname, nickname)
    return (payload.name.strip(), payload.captain.strip())


@router.post("", response_model=TeamOut, status_code=201)
def create_team(payload: TeamCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Registered users submit a team to a tournament. Starts as pending review."""
    tournament = db.query(Tournament).filter(Tournament.id == payload.tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="赛事不存在")
    if not registration_open(tournament):
        raise HTTPException(status_code=400, detail="该赛事报名已截止")
    name, captain = _normalize_team_fields(payload)
    team = Team(
        tournament_id=tournament.id,
        registration_type=payload.registration_type,
        name=name,
        captain=captain,
        contact=payload.contact.strip(),
        declaration=payload.declaration,
        owner_id=user.id,
        status="pending",
    )
    team.players = [
        Player(nickname=p.nickname, profession=p.profession, is_substitute=p.is_substitute)
        for p in payload.players
    ]
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/mine", response_model=list[TeamOut])
def my_teams(
    tournament_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """The teams the current user has registered (optionally scoped to a tournament)."""
    q = db.query(Team).filter(Team.owner_id == user.id)
    if tournament_id is not None:
        q = q.filter(Team.tournament_id == tournament_id)
    return q.order_by(Team.created_at.desc()).all()


@router.delete("/{team_id}", status_code=204)
def delete_my_team(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    is_admin = user.role == "admin"
    if team.owner_id != user.id and not is_admin:
        raise HTTPException(status_code=403, detail="无权删除该队伍")
    # Regular users can only withdraw while registration is still open.
    if not is_admin and team.tournament and not registration_open(team.tournament):
        raise HTTPException(status_code=400, detail="报名已截止，无法撤回")
    db.delete(team)
    db.commit()
