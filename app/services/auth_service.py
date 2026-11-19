from fastapi import HTTPException, status

from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def login(self, email: str, password: str) -> str:
        user = await self.users.get_by_email(email)

        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.hashed_password)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        return create_access_token(str(user.id))
