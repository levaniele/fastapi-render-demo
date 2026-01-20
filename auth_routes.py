from datetime import datetime, timedelta
import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from passlib.context import CryptContext

import auth_service
from db import get_db
from schemas import LoginRequest, ChangePasswordRequest
from dependencies import get_current_user
from settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def _create_access_token(data: dict, expires_hours: int, secret_key: str, algorithm: str):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=expires_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


@router.post("/login")
def login(data: LoginRequest, response: Response, db=Depends(get_db)):
    settings = get_settings()
    try:
        user = auth_service.get_user_by_email(db, data.email)
        if not user or not pwd_context.verify(data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = _create_access_token(
            data={"sub": user["email"], "user_id": user["id"], "role": user["role"] or "viewer"},
            expires_hours=settings.access_token_expire_hours,
            secret_key=settings.secret_key,
            algorithm=settings.algorithm,
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.is_production,
            samesite="lax",
            max_age=3600 * settings.access_token_expire_hours,
            path="/",
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name") or "",
                "role": user["role"] or "viewer",
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Login error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )


@router.post("/logout")
def logout(response: Response):
    try:
        response.delete_cookie(
            key="access_token", path="/", httponly=True, samesite="lax"
        )
        return {"message": "Successfully logged out", "status": "success"}
    except Exception as exc:
        logger.error("Logout error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.get("/verify")
def verify_token(request: Request):
    settings = get_settings()
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return {
            "authenticated": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("sub"),
            "role": payload.get("role", "viewer"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )




@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    try:
        db_user = auth_service.get_user_by_id(db, user["user_id"])
        if not db_user or not pwd_context.verify(
            data.current_password, db_user["password_hash"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        new_hash = pwd_context.hash(data.new_password)
        auth_service.update_password(db, db_user["id"], new_hash)

        return {"status": "password_updated"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Change password error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password update failed",
        )


@router.post("/register")
def register(data: LoginRequest, db=Depends(get_db)):
    try:
        if auth_service.check_email_exists(db, data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = pwd_context.hash(data.password)
        user = auth_service.create_user(db, data.email, hashed_password, "viewer")

        return {
            "status": "registered",
            "user": {"id": user["id"], "email": user["email"], "role": user["role"]},
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Registration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )
