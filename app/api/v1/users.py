from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import DBSession
from app.core.security import hash_password
from app.db.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreate,
    db: DBSession,
) -> UserResponse:
    existing = await db.execute(select(User).where(User.email == payload.email))

    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=str(payload.email),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)
