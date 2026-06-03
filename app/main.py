from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine
from . import models
from .routers import scans, packages
from .tasks.updater import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    print("Database tables ready.")

    start_scheduler()
    yield
    stop_scheduler()
    print("Server shut down.")

app = FastAPI(
    title       = "LicenseWatch",
    description = "License & CVE compliance checker for container images",
    version     = "1.0.0",
    lifespan    = lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)

app.include_router(scans.router)
app.include_router(packages.router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")