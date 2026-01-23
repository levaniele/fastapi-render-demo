# ============================================================================
# FILE: app/routes/auth.py
# COMPLETE AUTHENTICATION SYSTEM - Service layer integration
# Includes: Login, Logout, Verify, JWT with Roles
# ============================================================================

# ============================================================================
# SUMMARY OF ENDPOINTS:
# ============================================================================
# POST /auth/login       - Login with email/password, get JWT cookie
# POST /auth/logout      - Logout, delete JWT cookie
# GET  /auth/verify      - Check if authenticated, return user info
# POST /auth/register    - Register new user (optional)

from fastapi import APIRouter, HTTPException, status, Response, Request, Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.database import get_db_session
from app.schemas import LoginRequest, PasswordResetRequest, PasswordResetConfirm
from app.core.config import get_settings
from app.services import auth_service
from datetime import datetime, timedelta, timezone
import jwt
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
settings = get_settings()


# ============================================================================
# HELPER FUNCTION: Create JWT Token
# ============================================================================


def create_access_token(data: dict):
    """Create JWT access token with expiration"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.access_token_expire_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.reset_token_expire_minutes)
    payload = {"sub": email, "purpose": "password_reset", "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


# ============================================================================
# ENDPOINT 1: LOGIN
# ============================================================================


@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db_session)):
    """
    Authenticate user with email and password
    Returns JWT token with user role in HTTP-only cookie
    """
    try:
        # Query user with role from database using service
        user = auth_service.get_user_by_email(db, data.email)

        # Check if user exists
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not pwd_context.verify(data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Create JWT token WITH ROLE
        access_token = create_access_token(
            data={
                "sub": user["email"],
                "user_id": user["id"],
                "role": user["role"] or "viewer",  # Include role in token
            }
        )

        # Set HTTP-only cookie (cross-origin compatible)
        # For cross-origin cookies: secure=True + samesite="none" required
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.is_production,  # True for HTTPS in production
            samesite="none" if settings.is_production else "lax",  # "none" for cross-origin
            max_age=86400 * settings.access_token_expire_hours // 24,
            path="/",
        )

        # Return success response with user info
        return {
            "status": "authenticated",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"] or "viewer",
            },
            "access_token": access_token,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )


# ============================================================================
# ENDPOINT 2: LOGOUT
# ============================================================================


@router.post("/logout")
def logout(response: Response):
    """
    Logout user by deleting authentication cookie
    """
    try:
        # Delete the access_token cookie (must match set_cookie settings)
        response.delete_cookie(
            key="access_token",
            path="/",
            httponly=True,
            secure=settings.is_production,
            samesite="none" if settings.is_production else "lax",
        )

        return {"message": "Successfully logged out", "status": "success"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


# ============================================================================
# ENDPOINT 3: VERIFY TOKEN
# ============================================================================


@router.get("/verify")
def verify_token(request: Request):
    """
    Verify if user is authenticated
    Returns user info including role
    """
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    try:
        # Decode and verify JWT token
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        return {
            "authenticated": True,
            "user_id": payload.get("user_id"),
            "email": payload.get("sub"),
            "role": payload.get("role", "viewer"),  # Return role for permissions
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


# ============================================================================
# OPTIONAL: REGISTER ENDPOINT
# ============================================================================


@router.post("/register")
def register(data: LoginRequest, db: Session = Depends(get_db_session)):
    """
    Register a new user account
    """
    try:
        # Check if email already exists using service
        if auth_service.check_email_exists(db, data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password
        hashed_password = pwd_context.hash(data.password)

        # Create user using service
        user = auth_service.create_user(db, data.email, hashed_password, "viewer")

        return {
            "status": "registered",
            "user": {"id": user["id"], "email": user["email"], "role": user["role"]},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/password/forgot")
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db_session)):
    """
    Request a password reset token.
    """
    try:
        user = auth_service.get_user_by_email(db, data.email)
        if not user:
            return {"status": "ok"}
        token = create_password_reset_token(data.email)
        return {"status": "ok", "reset_token": token}
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed",
        )


@router.post("/password/reset")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db_session)):
    """
    Reset password using a short-lived token.
    """
    try:
        payload = jwt.decode(
            data.token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("purpose") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )
        hashed_password = pwd_context.hash(data.new_password)
        user = auth_service.update_user_password(db, email, hashed_password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return {"status": "password_updated", "user": {"id": user["id"]}}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        )