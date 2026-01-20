from fastapi import Depends, HTTPException, Request
import jwt

from settings import get_settings


def get_current_user(request: Request):
    settings = get_settings()
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("sub"),
            "role": payload.get("role", "viewer"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_role(*allowed_roles: str):
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}",
            )
        return user

    return role_checker


def require_authenticated(user: dict = Depends(get_current_user)):
    return user
