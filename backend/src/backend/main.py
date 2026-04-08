from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from backend.auth.router import auth_router
from backend.config import settings
from backend.exercises.router import exercises_router
from backend.limiter import limiter, rate_limit_handler
from backend.logging_config import setup_logging
from backend.middleware import LoggingMiddleware
from backend.trainings.router import trainings_router
from backend.users.router import users_router
from backend.web.router import web_router
from backend.workouts.router import workouts_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(debug=settings.debug)
    # Before app
    yield
    # After app

app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(web_router)
app.include_router(auth_router, prefix="/api")
app.include_router(exercises_router, prefix="/api")
app.include_router(trainings_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(workouts_router, prefix="/api")
