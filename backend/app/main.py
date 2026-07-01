from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import hash_password
from .config import settings
from .database import Base, SessionLocal, engine, ensure_database_exists
from .models import User
from .routers import admin, auth, public, teams


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
    bootstrap_admin()
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
