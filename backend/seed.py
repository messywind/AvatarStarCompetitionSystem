"""Insert demo teams so the browsing page and bracket have content.

Run after the API has created the tables at least once:
    python seed.py
"""

from datetime import datetime, timedelta

from app.auth import hash_password
from app.database import Base, SessionLocal, engine, ensure_database_exists
from app.models import Player, Team, Tournament, User

DEMO_TEAMS = [
    {
        "name": "烈焰星辰",
        "captain": "阿焰",
        "declaration": "以火之名，燃尽对手！",
        "roster": [("阿焰", "突击"), ("小护", "护卫"), ("毒姐", "生化"), ("铁墙", "重装"), ("疾风", "突击")],
        "subs": [("替补一", "生化")],
    },
    {
        "name": "深蓝突击队",
        "captain": "蓝翔",
        "declaration": "稳扎稳打，一击制胜。",
        "roster": [("蓝翔", "护卫"), ("波塞冬", "生化"), ("重炮", "重装"), ("飞刀", "突击"), ("盾墙", "护卫")],
        "subs": [],
    },
    {
        "name": "紫电风暴",
        "captain": "紫月",
        "declaration": "风暴将至，无人可挡！",
        "roster": [("紫月", "生化"), ("雷神", "重装"), ("影刺", "突击"), ("坚壁", "护卫"), ("腐蚀", "生化")],
        "subs": [("风替", "突击"), ("盾替", "护卫")],
    },
    {
        "name": "黄金战团",
        "captain": "金戈",
        "declaration": "荣耀属于金色战团！",
        "roster": [("金戈", "重装"), ("铁马", "护卫"), ("狙神", "突击"), ("瘟疫", "生化"), ("突锋", "突击")],
        "subs": [],
    },
]


def run():
    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.username == "admin").first()
        if not owner:
            owner = User(username="admin", password_hash=hash_password("admin123"), role="admin")
            db.add(owner)
            db.commit()
            db.refresh(owner)

        tournament = db.query(Tournament).order_by(Tournament.id).first()
        if not tournament:
            tournament = Tournament(
                name="百变兵团第一届选花杯",
                description="百变兵团官方赛事 · 第一届选花杯",
                registration_deadline=datetime.now() + timedelta(days=30),
            )
            db.add(tournament)
            db.commit()
            db.refresh(tournament)

        for spec in DEMO_TEAMS:
            if db.query(Team).filter(Team.name == spec["name"]).first():
                continue
            team = Team(
                tournament_id=tournament.id,
                name=spec["name"],
                captain=spec["captain"],
                declaration=spec["declaration"],
                owner_id=owner.id,
                status="approved",
            )
            team.players = [
                Player(nickname=n, profession=p, is_substitute=False) for n, p in spec["roster"]
            ] + [Player(nickname=n, profession=p, is_substitute=True) for n, p in spec["subs"]]
            db.add(team)
        db.commit()
        print("Seed complete:", db.query(Team).count(), "teams total")
    finally:
        db.close()


if __name__ == "__main__":
    run()
