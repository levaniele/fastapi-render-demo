import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.services import dashboard_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    limit: int = Query(5, ge=1, le=20, description="Top N entities per section"),
    db: Session = Depends(get_db_session),
):
    """
    Dashboard highlights: top players, clubs, and coaches.
    """
    try:
        return dashboard_service.get_dashboard_summary(db, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard summary",
        )
