from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Player, Team, User
from ..schemas import TeamCreate, TeamOut

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.post("", response_model=TeamOut, status_code=201)
def create_team(payload: TeamCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Registered users submit a team. Starts as pending review."""
    team = Team(
        name=payload.name,
        captain=payload.captain,
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
def my_teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The teams the current user has registered."""
    return (
        db.query(Team)
        .filter(Team.owner_id == user.id)
        .order_by(Team.created_at.desc())
        .all()
    )


@router.delete("/{team_id}", status_code=204)
def delete_my_team(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="队伍不存在")
    if team.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除该队伍")
    db.delete(team)
    db.commit()
