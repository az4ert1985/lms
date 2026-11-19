from fastapi import HTTPException, status

from app.core.security import hash_password
from app.db.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def create_user(self, payload: UserCreate) -> User:
        existing = await self.users.get_by_email(str(payload.email))

        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=str(payload.email),
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=UserRole.STUDENT,
        )

        self.users.add(user)
        await self.users.commit()
        await self.users.refresh(user)

        return user
