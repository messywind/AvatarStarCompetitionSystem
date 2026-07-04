"""Insert demo teams so the browsing page and bracket have content.

Run after the API has created the tables at least once:
    python seed.py
"""

import json
from datetime import datetime, timedelta

from app.auth import hash_password
from app.database import Base, SessionLocal, engine, ensure_database_exists
from app.models import Player, Team, Tournament, User

DEMO_POSTER = {
    "format": "5v5",
    "profession_limit": "各职业不得超过两名\n若没有生化，可换成一个非突击职业",
    "mode_limit": "预选赛模式为 占点 夺旗 团战 纯随机",
    "other_limit": "其余以赛事官方为准",
    "reward_champion": "三把 ROG 夜魔键盘 价值 5000 元（队伍自行分配）",
    "reward_runner_up": "三把龙鳞 2 鼠标 价值 3000 元",
    "reward_third": "每人 1500 兑换卷",
    "reward_fourth": "每人 500 兑换卷",
    "reward_other": "更有众多参与奖神秘奖等待抽选",
    "announcement": (
        "本活动绝对**公平免费**\n"
        "面向**全服玩家**，欢迎大家踊跃报名\n"
        "设计奖励金额不小，为保证公平比赛，每位参赛选手请**私自录屏**（N卡录制/其他软件/手机录屏），有异议者请移交裁判席，有**专业鉴挂团队**介入\n"
        "比赛期间**直播间不停给参赛选手抽奖**，所以希望大家都参与进来\n"
        "**单人**也可以报名\n"
        "满**16支队伍**开赛"
    ),
    "announcement_footer": "快来组队参赛，赢取丰厚奖励！",
}

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
                description="百变兵团民间赛事 · 第一届选花杯",
                registration_deadline=datetime.now() + timedelta(days=30),
            )
            db.add(tournament)
            db.commit()
            db.refresh(tournament)

        if not tournament.poster_json:
            tournament.poster_json = json.dumps(DEMO_POSTER, ensure_ascii=False)
            db.commit()

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
