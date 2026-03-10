"""
Packages Endpoints
API endpoints for subscription plan management (SuperAdmin Packages module)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.core.database import get_db
from app.api.v1.deps import get_current_superadmin
from app.models.user import User
from app.models.subscription import SubscriptionPlan, Subscription
from app.schemas.subscription import (
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SubscriptionPlanResponse
)
from app.services.subscription_service import SubscriptionPlanService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# SUPERADMIN PACKAGES MANAGEMENT
# ============================================================================

@router.get("/", response_model=List[Dict[str, Any]])
def get_all_packages(
    search: Optional[str] = Query(None, description="Search term"),
    plan_type: Optional[str] = Query(None, description="Filter by plan type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get all packages (subscription plans) for superadmin dashboard.
    
    Returns packages in the format expected by frontend:
    - name, type, subscribers, price, date, status
    
    Each plan creates TWO entries: one for Monthly and one for Yearly pricing.
    """
    try:
        # Get all subscription plans from database, ordered by name and ID
        # Use distinct to avoid duplicates if there are any database issues
        plans = (
            db.query(SubscriptionPlan)
            .order_by(SubscriptionPlan.name, SubscriptionPlan.id)
            .all()
        )
        
        # Log the plans retrieved for debugging
        logger.info(f"Retrieved {len(plans)} unique plans from database")
        
        packages = []
        seen_combinations = set()  # Track unique plan+type combinations
        
        for plan in plans:
            # Count active subscribers for Monthly plan type
            monthly_subscribers = db.query(Subscription).filter(
                Subscription.plan_name == plan.name,
                Subscription.plan_type == "Monthly",
                Subscription.is_active == True
            ).count()
            
            # Count active subscribers for Yearly plan type
            yearly_subscribers = db.query(Subscription).filter(
                Subscription.plan_name == plan.name,
                Subscription.plan_type == "Yearly", 
                Subscription.is_active == True
            ).count()
            
            # Create unique identifier for Monthly package
            monthly_key = f"{plan.id}_Monthly"
            if monthly_key not in seen_combinations:
                seen_combinations.add(monthly_key)
                monthly_package = {
                    "id": f"{plan.id}_M",  # Unique ID combining plan ID and type
                    "plan_id": plan.id,  # Original plan ID for reference
                    "name": plan.name,
                    "type": "Monthly",
                    "subscribers": monthly_subscribers,
                    "price": f"${float(plan.monthly_price):.2f}",
                    "date": plan.created_at.strftime("%d %b %Y") if plan.created_at else "",
                    "status": "Active" if plan.is_active else "Inactive"
                }
                packages.append(monthly_package)
            
            # Create unique identifier for Yearly package
            yearly_key = f"{plan.id}_Yearly"
            if yearly_key not in seen_combinations:
                seen_combinations.add(yearly_key)
                yearly_package = {
                    "id": f"{plan.id}_Y",  # Unique ID combining plan ID and type
                    "plan_id": plan.id,  # Original plan ID for reference
                    "name": plan.name,
                    "type": "Yearly",
                    "subscribers": yearly_subscribers,
                    "price": f"${float(plan.yearly_price):.2f}",
                    "date": plan.created_at.strftime("%d %b %Y") if plan.created_at else "",
                    "status": "Active" if plan.is_active else "Inactive"
                }
                packages.append(yearly_package)
        
        # Apply filters after creating all packages
        if search and isinstance(search, str):
            packages = [p for p in packages if search.lower() in p["name"].lower()]
        
        if plan_type and isinstance(plan_type, str):
            packages = [p for p in packages if p["type"] == plan_type]
            
        if status and isinstance(status, str):
            packages = [p for p in packages if p["status"] == status]
        
        # Sort packages by name and type for consistent ordering
        packages.sort(key=lambda x: (x["name"], x["type"]))
        
        logger.info(f"Superadmin {superadmin.email} retrieved {len(packages)} packages from {len(plans)} unique plans")
        return packages
        
    except Exception as e:
        logger.error(f"Error fetching packages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching packages: {str(e)}"
        )


@router.get("/summary", response_model=Dict[str, Any])
def get_packages_summary(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get packages statistics summary for dashboard.
    
    Returns:
    - total_plans: Total number of plan entries (each plan has Monthly + Yearly = 2 entries)
    - active_plans: Number of active plan entries
    - inactive_plans: Number of inactive plan entries
    - plan_types: Number of unique plan types (Monthly, Yearly)
    """
    try:
        # Get all plans from database
        all_plans = db.query(SubscriptionPlan).all()
        active_plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()
        inactive_plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == False).all()
        
        # Each plan creates 2 entries (Monthly + Yearly)
        total_plan_entries = len(all_plans) * 2
        active_plan_entries = len(active_plans) * 2
        inactive_plan_entries = len(inactive_plans) * 2
        
        # Count unique plan types (should always be 2: Monthly and Yearly)
        plan_types = set()
        for plan in all_plans:
            plan_types.add("Monthly")
            plan_types.add("Yearly")
        
        summary = {
            "total_plans": total_plan_entries,
            "active_plans": active_plan_entries,
            "inactive_plans": inactive_plan_entries,
            "plan_types": len(plan_types)
        }
        
        logger.info(f"Packages summary retrieved by {superadmin.email}: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Error fetching packages summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching packages summary: {str(e)}"
        )


@router.get("/{package_id}", response_model=Dict[str, Any])
def get_package(
    package_id: str,  # Changed to string to accept composite IDs like "4_M" or "4_Y"
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get package details by ID.
    
    Accepts composite IDs like "4_M" (plan 4, Monthly) or "4_Y" (plan 4, Yearly)
    or plain integer IDs for backward compatibility.
    """
    try:
        # Parse the package_id to extract plan_id and type
        plan_id = None
        plan_type = None
        
        if "_M" in package_id:
            # Monthly package: "4_M" -> plan_id=4, type=Monthly
            plan_id = int(package_id.replace("_M", ""))
            plan_type = "Monthly"
        elif "_Y" in package_id:
            # Yearly package: "4_Y" -> plan_id=4, type=Yearly
            plan_id = int(package_id.replace("_Y", ""))
            plan_type = "Yearly"
        else:
            # Backward compatibility: plain integer ID
            # Default to returning the plan with both types
            plan_id = int(package_id)
            plan_type = None
        
        # Fetch the plan from database
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # If specific type requested, return that package entry
        if plan_type:
            # Count subscribers for the specific type
            subscribers = db.query(Subscription).filter(
                Subscription.plan_name == plan.name,
                Subscription.plan_type == plan_type,
                Subscription.is_active == True
            ).count()
            
            price = plan.monthly_price if plan_type == "Monthly" else plan.yearly_price
            
            package = {
                "id": package_id,  # Return the composite ID
                "plan_id": plan.id,
                "name": plan.name,
                "display_name": plan.display_name,
                "description": plan.description,
                "type": plan_type,
                "subscribers": subscribers,
                "price": f"${float(price):.2f}",
                "price_value": float(price),
                "currency": plan.currency,
                "date": plan.created_at.strftime("%d %b %Y") if plan.created_at else "",
                "status": "Active" if plan.is_active else "Inactive",
                "is_active": plan.is_active,
                "max_employees": plan.max_employees,
                "max_businesses": plan.max_businesses,
                "features": plan.features,
                "trial_days": plan.trial_days,
                "is_popular": plan.is_popular
            }
            
            logger.info(f"Package {package_id} retrieved by {superadmin.email}")
            return package
        else:
            # Return full plan details (backward compatibility)
            monthly_subscribers = db.query(Subscription).filter(
                Subscription.plan_name == plan.name,
                Subscription.plan_type == "Monthly",
                Subscription.is_active == True
            ).count()
            
            yearly_subscribers = db.query(Subscription).filter(
                Subscription.plan_name == plan.name,
                Subscription.plan_type == "Yearly",
                Subscription.is_active == True
            ).count()
            
            package = {
                "id": plan.id,
                "plan_id": plan.id,
                "name": plan.name,
                "display_name": plan.display_name,
                "description": plan.description,
                "monthly_price": float(plan.monthly_price),
                "yearly_price": float(plan.yearly_price),
                "monthly_subscribers": monthly_subscribers,
                "yearly_subscribers": yearly_subscribers,
                "currency": plan.currency,
                "date": plan.created_at.strftime("%d %b %Y") if plan.created_at else "",
                "status": "Active" if plan.is_active else "Inactive",
                "is_active": plan.is_active,
                "max_employees": plan.max_employees,
                "max_businesses": plan.max_businesses,
                "features": plan.features,
                "trial_days": plan.trial_days,
                "is_popular": plan.is_popular
            }
            
            logger.info(f"Package {package_id} (full plan) retrieved by {superadmin.email}")
            return package
        
    except ValueError as ve:
        logger.error(f"Invalid package ID format: {package_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid package ID format: {package_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching package {package_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching package: {str(e)}"
        )


@router.post("/", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
def create_package(
    package_data: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Create a new package (subscription plan).
    """
    try:
        service = SubscriptionPlanService(db)
        
        # Check if plan name already exists
        existing_plan = service.get_plan_by_name(package_data.name)
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan name already exists"
            )
        
        # Create the plan
        plan_dict = package_data.model_dump()
        plan_dict["created_by"] = superadmin.id
        plan_dict["created_at"] = datetime.utcnow()
        
        plan = service.create_plan(plan_dict)
        
        logger.info(f"Package created by {superadmin.email}: {plan.name}")
        return plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating package: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating package: {str(e)}"
        )


@router.put("/{package_id}", response_model=SubscriptionPlanResponse)
def update_package(
    package_id: str,  # Changed to string to accept composite IDs
    update_data: SubscriptionPlanUpdate,
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Update an existing package.
    
    Accepts composite IDs like "4_M" or "4_Y", but updates the underlying plan.
    """
    try:
        # Parse the package_id to extract plan_id
        if "_M" in package_id or "_Y" in package_id:
            plan_id = int(package_id.replace("_M", "").replace("_Y", ""))
        else:
            plan_id = int(package_id)
        
        service = SubscriptionPlanService(db)
        
        # Check if plan exists
        existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if not existing_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Check if new name conflicts with existing plans
        if update_data.name and update_data.name != existing_plan.name:
            name_conflict = service.get_plan_by_name(update_data.name)
            if name_conflict and name_conflict.id != plan_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Plan name already exists"
                )
        
        # Update the plan
        update_dict = update_data.model_dump(exclude_unset=True)
        plan = service.update_plan(plan_id, update_dict)
        
        logger.info(f"Package {package_id} (plan {plan_id}) updated by {superadmin.email}")
        return plan
        
    except ValueError as ve:
        logger.error(f"Invalid package ID format: {package_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid package ID format: {package_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating package {package_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating package: {str(e)}"
        )


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    package_id: str,  # Changed to string to accept composite IDs
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Delete a package.
    
    Accepts composite IDs like "4_M" or "4_Y", but deletes the underlying plan.
    Note: Deleting a plan removes both Monthly and Yearly entries.
    """
    try:
        # Parse the package_id to extract plan_id
        if "_M" in package_id or "_Y" in package_id:
            plan_id = int(package_id.replace("_M", "").replace("_Y", ""))
        else:
            plan_id = int(package_id)
        
        service = SubscriptionPlanService(db)
        
        # Check if plan exists
        existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if not existing_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Check if plan has active subscriptions
        active_subscriptions = db.query(Subscription).filter(
            Subscription.plan_name == existing_plan.name,
            Subscription.is_active == True
        ).count()
        
        if active_subscriptions > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete plan with {active_subscriptions} active subscriptions"
            )
        
        success = service.delete_plan(plan_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        logger.info(f"Package {package_id} (plan {plan_id}) deleted by {superadmin.email}")
        
    except ValueError as ve:
        logger.error(f"Invalid package ID format: {package_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid package ID format: {package_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting package {package_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting package: {str(e)}"
        )


# ============================================================================
# PACKAGE ANALYTICS
# ============================================================================

@router.get("/analytics/subscribers", response_model=List[Dict[str, Any]])
def get_subscriber_analytics(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Get subscriber analytics by plan.
    """
    try:
        plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()
        
        analytics = []
        for plan in plans:
            monthly_count = db.query(Subscription).filter(
                Subscription.plan_name == plan.name,
                Subscription.plan_type == "Monthly",
                Subscription.is_active == True
            ).count()
            
            yearly_count = db.query(Subscription).filter(
                Subscription.plan_name == plan.name,
                Subscription.plan_type == "Yearly",
                Subscription.is_active == True
            ).count()
            
            analytics.append({
                "plan": plan.name,
                "monthly_subscribers": monthly_count,
                "yearly_subscribers": yearly_count,
                "total_subscribers": monthly_count + yearly_count
            })
        
        logger.info(f"Subscriber analytics retrieved by {superadmin.email}")
        return analytics
        
    except Exception as e:
        logger.error(f"Error fetching subscriber analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching subscriber analytics: {str(e)}"
        )


# ============================================================================
# DIAGNOSTIC ENDPOINTS (For debugging)
# ============================================================================

@router.get("/debug/plans", response_model=List[Dict[str, Any]])
def debug_subscription_plans(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Debug endpoint to see actual subscription plans in database.
    Shows raw data to identify duplicates or data issues.
    """
    try:
        plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.id).all()
        
        debug_data = []
        for plan in plans:
            debug_data.append({
                "id": plan.id,
                "name": plan.name,
                "display_name": plan.display_name,
                "monthly_price": float(plan.monthly_price),
                "yearly_price": float(plan.yearly_price),
                "is_active": plan.is_active,
                "created_at": plan.created_at.isoformat() if plan.created_at else None
            })
        
        logger.info(f"Debug: Found {len(plans)} plans in database")
        return debug_data
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching debug data: {str(e)}"
        )


@router.get("/debug/subscriptions", response_model=List[Dict[str, Any]])
def debug_subscriptions(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Debug endpoint to see actual subscriptions in database.
    Shows which plans have active subscriptions.
    """
    try:
        subscriptions = (
            db.query(Subscription)
            .filter(Subscription.is_active == True)
            .order_by(Subscription.plan_name, Subscription.plan_type)
            .all()
        )
        
        debug_data = []
        for sub in subscriptions:
            debug_data.append({
                "id": sub.id,
                "plan_name": sub.plan_name,
                "plan_type": sub.plan_type,
                "business_id": sub.business_id,
                "is_active": sub.is_active,
                "status": sub.status,
                "created_at": sub.created_at.isoformat() if sub.created_at else None
            })
        
        logger.info(f"Debug: Found {len(subscriptions)} active subscriptions")
        return debug_data
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching debug data: {str(e)}"
        )


# ============================================================================
# MAINTENANCE OPERATIONS
# ============================================================================

@router.post("/maintenance/sync-plans", response_model=Dict[str, Any])
def sync_subscription_plans(
    db: Session = Depends(get_db),
    superadmin: User = Depends(get_current_superadmin)
):
    """
    Sync subscription plans with active subscriptions.
    """
    try:
        # Get all unique plan names from subscriptions
        subscription_plans = db.query(Subscription.plan_name).distinct().all()
        existing_plans = db.query(SubscriptionPlan.name).all()
        
        existing_plan_names = {plan.name for plan in existing_plans}
        subscription_plan_names = {plan.plan_name for plan in subscription_plans}
        
        # Find missing plans
        missing_plans = subscription_plan_names - existing_plan_names
        
        created_count = 0
        for plan_name in missing_plans:
            # Create basic plan entry
            new_plan = SubscriptionPlan(
                name=plan_name,
                display_name=f"{plan_name} Plan",
                description=f"Auto-generated plan for {plan_name}",
                monthly_price=99.99,
                yearly_price=999.99,
                currency="USD",
                max_employees=100,
                max_businesses=1,
                features='["Basic Features"]',
                is_active=True,
                created_by=superadmin.id,
                created_at=datetime.utcnow()
            )
            db.add(new_plan)
            created_count += 1
        
        db.commit()
        
        logger.info(f"Plan sync completed by {superadmin.email}: {created_count} plans created")
        return {
            "message": f"Sync completed: {created_count} plans created",
            "created_plans": created_count,
            "existing_plans": len(existing_plan_names)
        }
        
    except Exception as e:
        logger.error(f"Error syncing subscription plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error syncing subscription plans: {str(e)}"
        )