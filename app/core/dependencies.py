# ============================================================================
# FILE: app/core/dependencies.py
# Authentication dependencies for route protection
# ============================================================================
#
# USAGE:
#   from app.core.dependencies import get_current_user, require_role
#
#   # Require any authenticated user
#   @router.get("/protected")
#   def protected_route(current_user: dict = Depends(get_current_user)):
#       return {"user_id": current_user["user_id"]}
#
#   # Require specific role
#   @router.post("/admin/resource")
#   def admin_route(current_user: dict = Depends(require_role("admin"))):
#       return {"admin_id": current_user["user_id"]}
#
#   # Optional authentication (returns None if not authenticated)
#   @router.get("/public")
#   def public_route(current_user: dict | None = Depends(get_current_user_optional)):
#       if current_user:
#           return {"message": f"Hello {current_user['email']}"}
#       return {"message": "Hello guest"}
# ============================================================================

from typing import Optional
from fastapi import Request, HTTPException, status, Depends
import jwt
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_current_user(request: Request) -> dict:
    """
    Dependency that extracts and validates the current user from JWT cookie.

    Returns:
        dict with keys: user_id, email, role

    Raises:
        HTTPException 401 if not authenticated or token invalid
    """
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Dependency that extracts user from JWT cookie if present.
    Returns None if not authenticated (does not raise exception).

    Useful for routes that work for both guests and authenticated users.

    Returns:
        dict with keys: user_id, email, role - or None if not authenticated
    """
    token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        return {
            "user_id": payload.get("user_id"),
            "email": payload.get("sub"),
            "role": payload.get("role", "viewer"),
        }

    except jwt.PyJWTError:
        return None


def require_role(*allowed_roles: str):
    """
    Factory that creates a dependency requiring specific role(s).

    Args:
        allowed_roles: One or more roles that are permitted (e.g., "admin", "editor")

    Usage:
        @router.post("/admin/resource")
        def admin_only(current_user: dict = Depends(require_role("admin"))):
            ...

        @router.put("/resource")
        def admin_or_editor(current_user: dict = Depends(require_role("admin", "editor"))):
            ...

    Returns:
        Dependency function that validates user has required role

    Raises:
        HTTPException 401 if not authenticated
        HTTPException 403 if authenticated but wrong role
    """
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        # User is already authenticated by the dependency injection
        user_role = current_user.get("role", "viewer").lower()
        allowed_roles_lower = [r.lower() for r in allowed_roles]

        if user_role not in allowed_roles_lower:
            logger.warning(
                f"Access denied: user {current_user.get('email')} with role '{user_role}' "
                f"attempted to access resource requiring {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(allowed_roles)}",
            )

        return current_user

    return role_checker
