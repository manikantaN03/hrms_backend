"""Tax & TDS setup endpoints"""
from typing import List, Optional, Annotated
from datetime import date
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.deps import get_current_admin
from app.models.user import User
from app.models.business import Business
from sqlalchemy.orm import Session as DBSession
from typing import Optional as _Optional
from app.schemas.tax_schemas import (
    TDSSettingResponse,
    TDSSettingUpdate,
    FinancialYearCreate,
    FinancialYearUpdate,
    FinancialYearResponse,
    SalaryComponentResponse,
    SalaryComponentCreate,
    TaxRateResponse,
)
from app.services.tax_service import get_tax_service

router = APIRouter()
logger = logging.getLogger(__name__)


def _resolve_business_id(current_admin: User, db: DBSession, business_id: _Optional[int] = None) -> int:
    bid = business_id or getattr(current_admin, "business_id", None)
    if bid is None:
        try:
            businesses = getattr(current_admin, "businesses", None)
            if businesses:
                bid = businesses[0].id
        except Exception:
            bid = None
    if not bid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business context missing")
    if not db.query(Business).filter(Business.id == bid).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Business with id {bid} does not exist")
    return bid


@router.get("/tds-settings", response_model=TDSSettingResponse)
def get_tds_settings(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin), business_id: int = Query(..., description="business_id is required")):
    service = get_tax_service(db)
    bid = _resolve_business_id(current_admin, db, business_id)
    setting = service.get_tds_setting(business_id=bid)
    return {"deduct_tds": setting.deduct_tds}


@router.put("/tds-settings", response_model=TDSSettingResponse)
def update_tds_settings(settings: TDSSettingUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin), business_id: int = Query(..., description="business_id is required")):
    service = get_tax_service(db)
    bid = _resolve_business_id(current_admin, db, business_id)
    updated = service.update_tds_setting(settings.deduct_tds, business_id=bid)
    return {"deduct_tds": updated.deduct_tds}


@router.get("/financial-years", response_model=List[FinancialYearResponse])
def get_financial_years(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin), business_id: int = Query(..., description="business_id is required")):
    service = get_tax_service(db)
    bid = _resolve_business_id(current_admin, db, business_id)
    # TaxService.list_financial_years doesn't accept business_id param — call it and filter locally
    years = service.list_financial_years()
    filtered = [
        y for y in years
        if (isinstance(y, dict) and y.get("business_id") == bid) or (not isinstance(y, dict) and getattr(y, "business_id", None) == bid)
    ]
    normalized = []
    for y in filtered:
        if isinstance(y, dict):
            y.setdefault("business_id", bid)
            normalized.append(y)
        else:
            normalized.append({
                "id": getattr(y, "id", None),
                "year": getattr(y, "year", None),
                "open": getattr(y, "open", None),
                "start_date": getattr(y, "start_date", None),
                "end_date": getattr(y, "end_date", None),
                "business_id": getattr(y, "business_id", bid) or bid,
            })
    return normalized


@router.post("/financial-years", response_model=FinancialYearResponse, status_code=status.HTTP_201_CREATED)
def create_financial_year(payload: FinancialYearCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    service = get_tax_service(db)
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    # business_id required in payload; validate/resolve if needed
    bid = data.get("business_id")
    bid = _resolve_business_id(current_admin, db, bid)
    data["business_id"] = bid
    created = service.create_financial_year(data)
    # ensure response includes business_id
    if isinstance(created, dict):
        created["business_id"] = created.get("business_id", bid)
        return created
    return {
        "id": getattr(created, "id", None),
        "year": getattr(created, "year", data.get("year")),
        "open": getattr(created, "open", data.get("open")),
        "start_date": getattr(created, "start_date", data.get("start_date")),
        "end_date": getattr(created, "end_date", data.get("end_date")),
        "business_id": getattr(created, "business_id", bid) or bid,
    }


@router.put("/financial-years/{year_id}", response_model=FinancialYearResponse)
def update_financial_year(
    year_id: Annotated[str, Path(..., description="financial year id, e.g. '2025-26' or '2025-2026'")],
    year_data: FinancialYearUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required"),
):
    service = get_tax_service(db)
    bid = _resolve_business_id(admin, db, business_id)

    update_payload = {}
    if year_data.open is not None:
        update_payload["open"] = year_data.open
    if year_data.start_date:
        update_payload["start_date"] = date.fromisoformat(year_data.start_date)
    if year_data.end_date:
        update_payload["end_date"] = date.fromisoformat(year_data.end_date)

    # call existing service update (keeps compatibility)
    fy = service.update_financial_year(year_id, update_payload)
    if not fy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial year not found")

    # ensure financial year belongs to requested business
    fy_business_id = getattr(fy, "business_id", bid)
    if fy_business_id != bid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial year not found for this business")

    return {
        "id": fy.id,
        "year": fy.year,
        "open": fy.open,
        "start_date": fy.start_date.strftime("%Y-%m-%d") if fy.start_date else None,
        "end_date": fy.end_date.strftime("%Y-%m-%d") if fy.end_date else None,
        "business_id": fy_business_id,
    }


@router.get("/tax-rates", response_model=List[TaxRateResponse])
def get_tax_rates(financial_year: Optional[str] = "2025-26", db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin), business_id: int = Query(..., description="business_id is required")):
    service = get_tax_service(db)
    bid = _resolve_business_id(current_admin, db, business_id)
    logger.debug("get_tax_rates called: financial_year=%s business_id=%s", financial_year, bid)
    results = service.list_tax_rates(financial_year, business_id=bid)
    logger.debug("list_tax_rates returned %d items for business_id=%s", len(results) if results is not None else 0, bid)
    if not results:
        logger.debug("no business-specific rates, checking global rates")
        results = service.list_tax_rates(financial_year, business_id=None)
        logger.debug("global list_tax_rates returned %d items", len(results) if results is not None else 0)
    return results


@router.get("/tax-rates/years")
def get_available_tax_years(db: Session = Depends(get_db), admin=Depends(get_current_admin), business_id: int = Query(..., description="business_id is required")):
    service = get_tax_service(db)
    bid = _resolve_business_id(admin, db, business_id)

    # prefer service support for business_id, fallback if signature differs
    try:
        years = service.get_available_tax_years(business_id=bid)
    except TypeError:
        years = service.get_available_tax_years()

    # normalize response to simple list of year strings for this business
    normalized = []
    for y in years or []:
        if isinstance(y, dict):
            if y.get("business_id") in (None, bid):
                normalized.append(y.get("year") or y.get("label"))
        else:
            # model instance or plain string
            year_val = getattr(y, "year", None) or getattr(y, "label", None) or y
            biz_val = getattr(y, "business_id", None)
            if biz_val is None or biz_val == bid:
                normalized.append(year_val)

    return {"years": normalized}


@router.post("/initialize-data")
def initialize_default_data(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin), business_id: int = Query(..., description="business_id is required")):
    service = get_tax_service(db)
    bid = _resolve_business_id(current_admin, db, business_id)
    return service.initialize_default_data(business_id=bid)


@router.get("/salary-components", response_model=List[SalaryComponentResponse])
def get_salary_components(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required")
):
    """Get all salary components with their tax category settings"""
    service = get_tax_service(db)
    bid = _resolve_business_id(current_admin, db, business_id)
    components = service.list_salary_components(business_id=bid)
    
    return [
        {
            "id": comp.id,
            "name": comp.name,
            "type": comp.component_type,
            "business_id": comp.business_id,
            "basic": getattr(comp, 'basic', False),
            "hra": getattr(comp, 'hra', False),
            "profit": getattr(comp, 'profit', False),
            "perk": getattr(comp, 'perk', False),
            "ent_all": getattr(comp, 'ent_all', False),
            "exempt": getattr(comp, 'exempt', False),
            "exempt_new": getattr(comp, 'exempt_new', False),
        }
        for comp in components
    ]


@router.put("/salary-components/{component_id}/category")
def update_salary_component_category(
    component_id: int,
    category: str = Query(..., description="Category field name (basic, hra, profit, perk, ent_all, exempt, exempt_new)"),
    value: bool = Query(..., description="True to enable, False to disable"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
    business_id: int = Query(..., description="business_id is required")
):
    """Update a specific tax category for a salary component"""
    service = get_tax_service(db)
    bid = _resolve_business_id(current_admin, db, business_id)
    
    # Validate category field
    valid_categories = ['basic', 'hra', 'profit', 'perk', 'ent_all', 'exempt', 'exempt_new']
    if category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )
    
    updated = service.update_salary_component_category(component_id, category, value, business_id=bid)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salary component not found"
        )
    
    return {
        "id": updated.id,
        "name": updated.name,
        "type": updated.component_type,
        "business_id": updated.business_id,
        "basic": getattr(updated, 'basic', False),
        "hra": getattr(updated, 'hra', False),
        "profit": getattr(updated, 'profit', False),
        "perk": getattr(updated, 'perk', False),
        "ent_all": getattr(updated, 'ent_all', False),
        "exempt": getattr(updated, 'exempt', False),
        "exempt_new": getattr(updated, 'exempt_new', False),
    }
