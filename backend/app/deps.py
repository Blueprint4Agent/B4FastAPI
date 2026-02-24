from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.settings import SETTINGS
from app.models.user import UserResponse, Users

security = HTTPBearer(auto_error=False)


async def get_current_user(
    token_auth: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> UserResponse:
    if token_auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token."
        )

    try:
        payload = jwt.decode(
            token_auth.credentials,
            SETTINGS.SECRET_KEY,
            algorithms=[SETTINGS.ALGORITHM],
        )
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        ) from None

    user = await Users.get_user_response_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    return user
