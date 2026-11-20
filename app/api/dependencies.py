import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.repositories.course_repository import CourseRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.module_repository import ModuleRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService
from app.services.lesson_service import LessonService
from app.services.module_service import ModuleService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)

DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSession,
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise credentials_error

        user_id = uuid.UUID(subject)

    except (jwt.InvalidTokenError, ValueError):
        raise credentials_error from None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_error

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(
    *roles: UserRole,
) -> Callable[..., Coroutine[User, Any, Any]]:
    async def role_checker(
        current_user: CurrentUser,
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


# Service providers.
# All repositories created for a request share one AsyncSession.


def build_auth_service(db: DBSession) -> AuthService:
    return AuthService(UserRepository(db))


def build_user_service(db: DBSession) -> UserService:
    return UserService(UserRepository(db))


def build_course_service(db: DBSession) -> CourseService:
    return CourseService(CourseRepository(db))


def build_module_service(db: DBSession) -> ModuleService:
    return ModuleService(
        CourseRepository(db),
        ModuleRepository(db),
    )


def build_lesson_service(db: DBSession) -> LessonService:
    return LessonService(LessonRepository(db))


def build_enrollment_service(db: DBSession) -> EnrollmentService:
    return EnrollmentService(EnrollmentRepository(db))


# Typed dependencies for API handlers.

AuthServiceDep = Annotated[
    AuthService,
    Depends(build_auth_service),
]

UserServiceDep = Annotated[
    UserService,
    Depends(build_user_service),
]

CourseServiceDep = Annotated[
    CourseService,
    Depends(build_course_service),
]

ModuleServiceDep = Annotated[
    ModuleService,
    Depends(build_module_service),
]

LessonServiceDep = Annotated[
    LessonService,
    Depends(build_lesson_service),
]

EnrollmentServiceDep = Annotated[
    EnrollmentService,
    Depends(build_enrollment_service),
]
