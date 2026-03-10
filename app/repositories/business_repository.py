"""
Business Repository
Data access layer for business operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .base_repository import BaseRepository
from app.models.business import Business


class BusinessRepository(BaseRepository[Business]):
    """Repository for business-related database operations."""
    
    def __init__(self, db: Session):
        super().__init__(Business, db)
    
    # ========================================================================
    # Get by Owner
    # ========================================================================
    
    def get_by_owner(
        self,
        owner_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Business]:
        """
        Get all businesses for a specific owner.
        
        Args:
            owner_id: User ID of the owner
            skip: Pagination offset
            limit: Maximum records
            active_only: Filter only active businesses
        
        Returns:
            List of businesses owned by user
        """
        query = self.db.query(Business).filter(Business.owner_id == owner_id)
        
        if active_only:
            query = query.filter(Business.is_active == True)
        
        return query.order_by(Business.created_at.desc()).offset(skip).limit(limit).all()
    
    def count_by_owner(self, owner_id: int, active_only: bool = True) -> int:
        """Count businesses for owner"""
        query = self.db.query(Business).filter(Business.owner_id == owner_id)
        
        if active_only:
            query = query.filter(Business.is_active == True)
        
        return query.count()
    
    # ========================================================================
    # Get by ID with Owner Check
    # ========================================================================
    
    def get_by_id_and_owner(
        self,
        business_id: int,
        owner_id: int
    ) -> Optional[Business]:
        """
        Get business by ID only if owned by specified user.
        
        Args:
            business_id: Business ID
            owner_id: User ID of expected owner
        
        Returns:
            Business if found and owned by user, None otherwise
        """
        return (
            self.db.query(Business)
            .filter(
                Business.id == business_id,
                Business.owner_id == owner_id
            )
            .first()
        )
    
    # ========================================================================
    # Check Uniqueness
    # ========================================================================
    
    def gstin_exists(self, gstin: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if GSTIN already exists.
        
        Args:
            gstin: GSTIN to check
            exclude_id: Business ID to exclude from check (for updates)
        
        Returns:
            True if GSTIN exists, False otherwise
        """
        if not gstin:
            return False
        
        query = self.db.query(Business).filter(Business.gstin == gstin)
        
        if exclude_id:
            query = query.filter(Business.id != exclude_id)
        
        return query.first() is not None
    
    def pan_exists_for_owner(
        self,
        pan: str,
        owner_id: int,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Check if PAN already exists for this owner.
        
        Args:
            pan: PAN to check
            owner_id: User ID
            exclude_id: Business ID to exclude (for updates)
        
        Returns:
            True if PAN exists for owner, False otherwise
        """
        query = self.db.query(Business).filter(
            Business.pan == pan,
            Business.owner_id == owner_id
        )
        
        if exclude_id:
            query = query.filter(Business.id != exclude_id)
        
        return query.first() is not None
    
    def business_url_exists(
        self,
        business_url: str,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Check if business URL is already taken.
        
        Args:
            business_url: URL to check
            exclude_id: Business ID to exclude (for updates)
        
        Returns:
            True if URL exists, False otherwise
        """
        if not business_url:
            return False
        
        query = self.db.query(Business).filter(Business.business_url == business_url)
        
        if exclude_id:
            query = query.filter(Business.id != exclude_id)
        
        return query.first() is not None
    
    # ========================================================================
    # Search
    # ========================================================================
    
    def search_by_name_or_gstin(
        self,
        owner_id: int,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Business]:
        """
        Search businesses by name or GSTIN for specific owner.
        
        Args:
            owner_id: User ID
            search_term: Search query
            skip: Pagination offset
            limit: Maximum records
        
        Returns:
            List of matching businesses
        """
        search = f"%{search_term}%"
        
        return (
            self.db.query(Business)
            .filter(
                Business.owner_id == owner_id,
                or_(
                    Business.business_name.ilike(search),
                    Business.gstin.ilike(search)
                )
            )
            .order_by(Business.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    # ========================================================================
    # Superadmin Operations
    # ========================================================================
    
    def get_all_businesses(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[Business]:
        """
        Get all businesses (for superadmin).
        
        Args:
            skip: Pagination offset
            limit: Maximum records
            active_only: Filter only active
        
        Returns:
            List of all businesses
        """
        query = self.db.query(Business)
        
        if active_only:
            query = query.filter(Business.is_active == True)
        
        return query.order_by(Business.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_businesses_by_state(self, state: str) -> List[Business]:
        """Get all businesses in a specific state"""
        return (
            self.db.query(Business)
            .filter(Business.state == state, Business.is_active == True)
            .order_by(Business.business_name)
            .all()
        )
    
    def get_businesses_by_plan(self, plan: str) -> List[Business]:
        """Get all businesses on a specific plan"""
        return (
            self.db.query(Business)
            .filter(Business.plan == plan, Business.is_active == True)
            .order_by(Business.created_at.desc())
            .all()
        )