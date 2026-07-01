import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import STATUS_APPROVED, Setting, Team
from ..schemas import Bracket, TeamPublicOut

router = APIRouter(prefix="/api/public", tags=["public"])

BRACKET_KEY = "bracket"


@router.get("/teams", response_model=list[TeamPublicOut])
def approved_teams(db: Session = Depends(get_db)):
    """Anyone can view approved teams — no auth required."""
    return (
        db.query(Team)
        .filter(Team.status == STATUS_APPROVED)
        .order_by(Team.name)
        .all()
    )


@router.get("/bracket")
def public_bracket(db: Session = Depends(get_db)):
    """Bracket plus a lightweight lookup of team id -> name for rendering."""
    row = db.query(Setting).filter(Setting.key == BRACKET_KEY).first()
    bracket = Bracket(**json.loads(row.value)) if row and row.value else Bracket(rounds=[])
    teams = db.query(Team).filter(Team.status == STATUS_APPROVED).all()
    team_map = {t.id: t.name for t in teams}
    return {"bracket": bracket.model_dump(), "teams": team_map}
