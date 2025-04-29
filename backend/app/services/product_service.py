from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app.models.products.product import Product
from sqlalchemy import asc, desc

def list_products_service(
    db: Session,
    limit: int = 10,
    offset: int = 0,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    include_deleted: bool = False,
    sort_dir: str = "desc",
) -> Tuple[List[Product], int]:
    """
    Business logic for listing paginated, searchable products.
    Returns (products_list, total_count).
    """
    query = db.query(Product)

    if not include_deleted:
        query = query.filter(Product.is_deleted == False)

    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    total = query.count()

    sort_order = desc(Product.created_at) if sort_dir == "desc" else asc(Product.created_at)

    products = (
        query.order_by(sort_order)
        .limit(limit)
        .offset(offset)
        .all()
    )

    return products, total
