from fastapi import APIRouter, Depends, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal
import logging

from app.schemas.roles import RoleOutPaginated
from app.db.session import get_db
from app.services.role_service import list_roles_service
from app.core.log_decorator import audit_log

router = APIRouter(prefix="/roles", tags=["Roles"])
logger = logging.getLogger("audit")

@router.get(
    "/", 
    response_model=RoleOutPaginated,
    status_code=status.HTTP_200_OK,
    summary="List all roles (with pagination and search)"
)
@audit_log("List All Roles")
async def list_roles(
    request: Request,
    db: Session = Depends(get_db),
    sort_dir: Literal["asc", "desc"] = "desc",
    is_active: Optional[bool] = None,
    limit: int = Query(default=10, ge=0, le=100, description="Number of roles to return."),
    offset: int = Query(default=0, ge=0, description="Starting index for pagination."),
    search: Optional[str] = Query(default=None, description="Search roles by name."),
):
    """
    Retrieve paginated, optionally searchable list of active roles.

    - Supports pagination (limit, offset)
    - Supports search by partial name match
    - Future-proof for scalable Role Management
    """
    roles, total = list_roles_service(
                        db,
                        limit=limit,
                        offset=offset,
                        search=search,
                        is_active=is_active,
                        sort_dir=sort_dir,
                    )

    logger.info(
        "[LIST_ROLES] Roles fetched successfully",
        extra={
            "ip": request.client.host,
            "request_id": getattr(request.state, "request_id", "-"),
            "total_roles": total,
            "search_query": search,
            "limit": limit,
            "offset": offset
        }
    )

    return RoleOutPaginated(
        total=total,
        limit=limit,
        offset=offset,
        data=roles
    )
