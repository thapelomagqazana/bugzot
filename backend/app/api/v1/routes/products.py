"""Routes for managing product-related operations."""
from fastapi import APIRouter, Depends, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal
import logging

from app.schemas.products import ProductOutPaginated
from app.db.session import get_db
from app.services.product_service import list_products_service
from app.core.log_decorator import audit_log

router = APIRouter(prefix="/products", tags=["Products"])
logger = logging.getLogger("audit")

@router.get(
    "/", 
    response_model=ProductOutPaginated,
    status_code=status.HTTP_200_OK,
    summary="List all products (paginated, searchable, scalable)"
)
@audit_log("List All Products")
async def list_products(
    request: Request,
    db: Session = Depends(get_db),
    sort_dir: Literal["asc", "desc"] = "desc",
    is_active: Optional[bool] = None,
    include_deleted: Optional[bool] = False,
    limit: int = Query(default=10, ge=0, le=100, description="Number of products per page."),
    offset: int = Query(default=0, ge=0, description="Offset index for pagination."),
    search: Optional[str] = Query(default=None, description="Search by product name."),
):
    """
    Retrieve paginated, optionally filtered and searchable list of products.

    - Supports limit/offset paging
    - Supports searching by name
    - Filters by active/inactive
    - Optionally includes soft-deleted products
    - Future-proof for category and other metadata filters
    """
    products, total = list_products_service(
        db,
        limit=limit,
        offset=offset,
        search=search,
        is_active=is_active,
        include_deleted=include_deleted,
        sort_dir=sort_dir
    )

    logger.info(
        "[LIST_PRODUCTS] Products fetched",
        extra={
            "ip": request.client.host,
            "request_id": getattr(request.state, "request_id", "-"),
            "total_products": total,
            "search_query": search,
            "include_deleted": include_deleted,
            "limit": limit,
            "offset": offset
        }
    )

    return ProductOutPaginated(
        total=total,
        limit=limit,
        offset=offset,
        data=products
    )
