from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database.models import Base
from app.database.session import engine
from app.routers import admin, public


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Vesnaidet Landing", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(public.router)
app.include_router(admin.router)
