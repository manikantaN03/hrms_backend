# Pagination utilities

from typing import Tuple, Any
from sqlalchemy.orm import Query

def paginate(query: Query, skip: int = 0, limit: int = 100) -> Tuple[list, int]:
    """
    Paginate a SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        Tuple of (items, total_count)
    """
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total