from typing import Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Cookie, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.service import login_user, register_user
from backend.config import settings
from backend.db.models import User
from backend.db.session import get_session
from backend.exercises.service import get_exercise_by_id, get_exercises
from backend.trainings.service import get_training_by_id, get_trainings
from backend.users.schema import POOL_SIZE_MAX, POOL_SIZE_MIN
from backend.users.service import get_user_profile, update_user_profile
from backend.users.schema import UserUpdateRequest
from backend.workouts.service import get_workout_by_id, get_workouts

templates = Jinja2Templates(directory="templates")

web_router = APIRouter(include_in_schema=False)

logger = logging.getLogger(__name__)


# Auth helper

async def get_web_user(
    token: Optional[str] = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            return None
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except JWTError:
        return None


def _login_redirect() -> RedirectResponse:
    return RedirectResponse("/login", status_code=302)


# Public routes

@web_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: Optional[User] = Depends(get_web_user)) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"user": user})


@web_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: Optional[User] = Depends(get_web_user)) -> HTMLResponse:
    if user:
        return RedirectResponse("/dashboard", status_code=302)  # type: ignore[return-value]
    return templates.TemplateResponse(request, "login.html", {"error": None})


@web_router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(),
    password: str = Form(),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    try:
        access_token, _ = await login_user(session, email=email, password=password)
        response = RedirectResponse("/dashboard", status_code=302)
        response.set_cookie("token", access_token, httponly=True, max_age=3600, samesite="lax")
        return response
    except Exception as e:
        logger.exception(f"Login exception for user {email}: {str(e)}")
        return templates.TemplateResponse(  # type: ignore[return-value]
            request, "login.html", {"error": "Invalid email or password"}, status_code=401
        )


@web_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: Optional[User] = Depends(get_web_user)) -> HTMLResponse:
    if user:
        return RedirectResponse("/dashboard", status_code=302)  # type: ignore[return-value]
    return templates.TemplateResponse(request, "register.html", {"error": None})


@web_router.post("/register")
async def register_submit(
    request: Request,
    email: str = Form(),
    password: str = Form(),
    full_name: str = Form(),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    try:
        await register_user(session, email=email, password=password, full_name=full_name)
        access_token, _ = await login_user(session, email=email, password=password)
        response = RedirectResponse("/dashboard", status_code=302)
        response.set_cookie("token", access_token, httponly=True, max_age=3600, samesite="lax")
        return response
    except Exception as e:
        logger.exception(f"Registration exception: {str(e)}")
        return templates.TemplateResponse(  # type: ignore[return-value]
            request, "register.html", {"error": "Something went wrong during registration. Try again later."}, status_code=400
        )


@web_router.post("/logout")
async def logout_submit() -> RedirectResponse:
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("token")
    return response


# Auth-required routes

@web_router.get("/trainings", response_class=HTMLResponse)
async def trainings_list(
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: Optional[User] = Depends(get_web_user),
) -> HTMLResponse:
    if user is None:
        return _login_redirect()  # type: ignore[return-value]
    trainings, total = await get_trainings(session)
    return templates.TemplateResponse(request, "trainings.html", {
        "user": user, "trainings": trainings, "total": total,
    })


@web_router.get("/trainings/{training_id}", response_class=HTMLResponse)
async def training_detail(
    request: Request,
    training_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: Optional[User] = Depends(get_web_user),
) -> HTMLResponse:
    if user is None:
        return _login_redirect()  # type: ignore[return-value]
    training = await get_training_by_id(session, training_id)
    if training is None:
        return templates.TemplateResponse(request, "404.html", {"user": user}, status_code=404)
    return templates.TemplateResponse(request, "training.html", {"user": user, "training": training})


@web_router.get("/exercises", response_class=HTMLResponse)
async def exercises_list(
    request: Request,
    session: AsyncSession = Depends(get_session),
    user: Optional[User] = Depends(get_web_user),
) -> HTMLResponse:
    if user is None:
        return _login_redirect()  # type: ignore[return-value]
    exercises, total = await get_exercises(session, limit=100)
    return templates.TemplateResponse(request, "exercises.html", {
        "user": user, "exercises": exercises, "total": total,
    })


@web_router.get("/exercises/{exercise_id}", response_class=HTMLResponse)
async def exercise_detail(
    request: Request,
    exercise_id: UUID,
    session: AsyncSession = Depends(get_session),
    user: Optional[User] = Depends(get_web_user),
) -> HTMLResponse:
    if user is None:
        return _login_redirect()  # type: ignore[return-value]
    exercise = await get_exercise_by_id(session, exercise_id)
    if exercise is None:
        return templates.TemplateResponse(request, "404.html", {"user": user}, status_code=404)
    return templates.TemplateResponse(request, "exercise.html", {"user": user, "exercise": exercise})


@web_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: Optional[User] = Depends(get_web_user),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    if user is None:
        return _login_redirect()  # type: ignore[return-value]
    profile = await get_user_profile(session, user_id=user.id)
    workouts_resp = await get_workouts(session, user_id=user.id, limit=5)
    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user, "profile": profile, "recent_workouts": workouts_resp.workouts,
    })


@web_router.get("/workouts", response_class=HTMLResponse)
async def workouts_list(
    request: Request,
    user: Optional[User] = Depends(get_web_user),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    if user is None:
        return _login_redirect()  # type: ignore[return-value]
    workouts_resp = await get_workouts(session, user_id=user.id, limit=50)
    return templates.TemplateResponse(request, "workouts.html", {
        "user": user, "workouts": workouts_resp.workouts, "total": workouts_resp.total,
    })


@web_router.get("/workouts/{workout_id}", response_class=HTMLResponse)
async def workout_detail(
    request: Request,
    workout_id: UUID,
    user: Optional[User] = Depends(get_web_user),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    if user is None:
        return _login_redirect()  # type: ignore[return-value]
    try:
        workout = await get_workout_by_id(session, workout_id=workout_id, user_id=user.id)
    except Exception:
        return templates.TemplateResponse(request, "404.html", {"user": user}, status_code=404)
    return templates.TemplateResponse(request, "workout.html", {"user": user, "workout": workout})


@web_router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    user: Optional[User] = Depends(get_web_user),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    if user is None:
        return _login_redirect()  # type: ignore[return-value]
    profile_data = await get_user_profile(session, user_id=user.id)
    return templates.TemplateResponse(request, "profile.html", {
        "user": user,
        "profile": profile_data,
        "pool_size_min": POOL_SIZE_MIN,
        "pool_size_max": POOL_SIZE_MAX,
        "error": None,
    })


@web_router.post("/profile", response_class=HTMLResponse)
async def profile_update(
    request: Request,
    full_name: str = Form(),
    preferred_pool_size: int = Form(),
    user: Optional[User] = Depends(get_web_user),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    if user is None:
        return _login_redirect()  # type: ignore[return-value]
    profile_data = await get_user_profile(session, user_id=user.id)

    if preferred_pool_size < POOL_SIZE_MIN or preferred_pool_size > POOL_SIZE_MAX:
        return templates.TemplateResponse(  # type: ignore[return-value]
            request, "profile.html", {
                "user": user,
                "profile": profile_data,
                "pool_size_min": POOL_SIZE_MIN,
                "pool_size_max": POOL_SIZE_MAX,
                "error": f"Pool size must be between {POOL_SIZE_MIN}m and {POOL_SIZE_MAX}m.",
            }, status_code=400,
        )

    await update_user_profile(
        session,
        user_id=user.id,
        data=UserUpdateRequest(full_name=full_name, preferred_pool_size=preferred_pool_size),
    )
    return RedirectResponse("/profile", status_code=302)  # type: ignore[return-value]
