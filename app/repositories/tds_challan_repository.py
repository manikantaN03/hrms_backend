"""
TDS Challan Repository
Database operations for TDS challan management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.datacapture import TDSChallan


class TDSChallanRepository:
    """Repository for TDS challan database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_challans_by_financial_year(
        self,
        financial_year: str,
        business_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all TDS challans for a financial year with unique months
        
        Args:
            financial_year: Financial year in format "2024-25"
            business_id: Business ID filter
            
        Returns:
            List of challan data with unique months
        """
        try:
            query = self.db.query(TDSChallan).filter(
                TDSChallan.financial_year == financial_year
            )
            
            if business_id:
                query = query.filter(TDSChallan.business_id == business_id)
            
            challans = query.order_by(TDSChallan.deposit_date.desc()).all()
            
            # Format response and ensure unique months (latest entry per month)
            result = []
            seen_months = set()
            
            for challan in challans:
                # Extract month from deposit date
                month = self._format_month_from_challan(challan)
                
                # Skip if we've already processed this month (keep latest)
                if month in seen_months:
                    continue
                
                seen_months.add(month)
                
                result.append({
                    "id": challan.id,
                    "month": month,
                    "bsrcode": challan.branch_code or "",
                    "date": challan.deposit_date.strftime("%Y-%m-%d") if challan.deposit_date else "",
                    "challan": challan.challan_number or "",
                    "total_amount": float(challan.total_amount) if challan.total_amount else 0.0,
                    "tds_amount": float(challan.tds_amount) if challan.tds_amount else 0.0,
                    "created_at": challan.created_at.isoformat() if challan.created_at else None,
                    "updated_at": challan.updated_at.isoformat() if challan.updated_at else None
                })
            
            # Sort by month order (APR to MAR)
            month_order = ["APR", "MAY", "JUN", "JUL", "AUG", "SEP", 
                          "OCT", "NOV", "DEC", "JAN", "FEB", "MAR"]
            
            def month_sort_key(challan_data):
                try:
                    month_abbr = challan_data["month"].split('-')[0]
                    return month_order.index(month_abbr)
                except:
                    return 999  # Put invalid months at end
            
            result.sort(key=month_sort_key)
            
            return result
            
        except Exception as e:
            raise Exception(f"Database error in get_challans_by_financial_year: {str(e)}")
    
    def get_challan_by_month(
        self,
        financial_year: str,
        month: str,
        business_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get TDS challan for a specific month
        
        Args:
            financial_year: Financial year in format "2024-25"
            month: Month in format "APR-2024"
            business_id: Business ID
            
        Returns:
            Challan data or None if not found
        """
        try:
            # Parse month to get date range
            month_start, month_end = self._parse_month_to_date_range(month)
            
            query = self.db.query(TDSChallan).filter(
                TDSChallan.financial_year == financial_year,
                TDSChallan.deposit_date >= month_start,
                TDSChallan.deposit_date <= month_end
            )
            
            if business_id:
                query = query.filter(TDSChallan.business_id == business_id)
            
            challan = query.first()
            
            if challan:
                return {
                    "id": challan.id,
                    "month": month,
                    "bsrcode": challan.branch_code or "",
                    "date": challan.deposit_date.strftime("%Y-%m-%d") if challan.deposit_date else "",
                    "challan": challan.challan_number or "",
                    "created_at": challan.created_at.isoformat() if challan.created_at else None,
                    "updated_at": challan.updated_at.isoformat() if challan.updated_at else None
                }
            
            return None
            
        except Exception as e:
            raise Exception(f"Database error in get_challan_by_month: {str(e)}")
    
    def save_challan_month(
        self,
        financial_year: str,
        month: str,
        bsrcode: str,
        deposit_date: Optional[date],
        challan_number: str,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Save or update TDS challan for a specific month
        
        Args:
            financial_year: Financial year in format "2024-25"
            month: Month in format "APR-2024"
            bsrcode: BSR code
            deposit_date: Date of deposit
            challan_number: Challan number
            business_id: Business ID
            created_by: User ID who created
            
        Returns:
            Save result with challan ID
        """
        try:
            # Check if challan already exists for this month
            existing_challan = None
            if deposit_date:
                month_start, month_end = self._parse_month_to_date_range(month)
                
                query = self.db.query(TDSChallan).filter(
                    TDSChallan.financial_year == financial_year,
                    TDSChallan.deposit_date >= month_start,
                    TDSChallan.deposit_date <= month_end
                )
                
                if business_id:
                    query = query.filter(TDSChallan.business_id == business_id)
                
                existing_challan = query.first()
            
            if existing_challan:
                # Update existing challan
                if bsrcode:
                    existing_challan.branch_code = bsrcode
                if deposit_date:
                    existing_challan.deposit_date = deposit_date
                if challan_number:
                    existing_challan.challan_number = challan_number
                
                existing_challan.updated_at = datetime.now()
                
                self.db.commit()
                self.db.refresh(existing_challan)
                
                return {"challan_id": existing_challan.id}
            
            else:
                # Create new challan
                new_challan = TDSChallan(
                    business_id=business_id or 1,
                    challan_number=challan_number or f"CHALLAN_{month}_{datetime.now().strftime('%Y%m%d')}",
                    financial_year=financial_year,
                    quarter=self._get_quarter_from_month(month),
                    deposit_date=deposit_date or date.today(),
                    tds_amount=Decimal("0.00"),  # Default amount
                    interest=Decimal("0.00"),
                    penalty=Decimal("0.00"),
                    total_amount=Decimal("0.00"),
                    bank_name="",  # Will be updated later
                    branch_code=bsrcode or "",
                    remarks=f"TDS challan for {month}",
                    created_by=created_by
                )
                
                self.db.add(new_challan)
                self.db.commit()
                self.db.refresh(new_challan)
                
                return {"challan_id": new_challan.id}
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Database error in save_challan_month: {str(e)}")
    
    def delete_challan_month(
        self,
        financial_year: str,
        month: str,
        business_id: Optional[int] = None
    ) -> bool:
        """
        Delete TDS challan for a specific month
        
        Args:
            financial_year: Financial year in format "2024-25"
            month: Month in format "APR-2024"
            business_id: Business ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Parse month to get date range
            month_start, month_end = self._parse_month_to_date_range(month)
            
            query = self.db.query(TDSChallan).filter(
                TDSChallan.financial_year == financial_year,
                TDSChallan.deposit_date >= month_start,
                TDSChallan.deposit_date <= month_end
            )
            
            if business_id:
                query = query.filter(TDSChallan.business_id == business_id)
            
            challan = query.first()
            
            if challan:
                self.db.delete(challan)
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Database error in delete_challan_month: {str(e)}")
    
    def _parse_month_to_date_range(self, month: str) -> tuple[date, date]:
        """
        Parse month string to date range
        
        Args:
            month: Month in format "APR-2024"
            
        Returns:
            Tuple of (start_date, end_date) for the month
        """
        try:
            month_abbr, year_str = month.split('-')
            year = int(year_str)
            
            # Convert month abbreviation to number
            month_abbrs = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            month_num = month_abbrs.index(month_abbr) + 1
            
            # Calculate start and end dates
            start_date = date(year, month_num, 1)
            
            # Calculate last day of month
            if month_num == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month_num + 1, 1) - timedelta(days=1)
            
            return start_date, end_date
            
        except Exception as e:
            # Default to current month if parsing fails
            today = date.today()
            return date(today.year, today.month, 1), today
    
    def _format_month_from_challan(self, challan: TDSChallan) -> str:
        """
        Format month string from challan deposit date
        
        Args:
            challan: TDSChallan object
            
        Returns:
            Month string in format "APR-2024"
        """
        try:
            if challan.deposit_date:
                month_abbrs = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
                month_abbr = month_abbrs[challan.deposit_date.month - 1]
                return f"{month_abbr}-{challan.deposit_date.year}"
            else:
                # Fallback to quarter-based month
                quarter_months = {
                    "Q1": "JUN",  # Apr-Jun
                    "Q2": "SEP",  # Jul-Sep
                    "Q3": "DEC",  # Oct-Dec
                    "Q4": "MAR"   # Jan-Mar
                }
                month_abbr = quarter_months.get(challan.quarter, "APR")
                # Extract year from financial year
                year = int(challan.financial_year.split('-')[0])
                if month_abbr in ["JAN", "FEB", "MAR"]:
                    year += 1
                return f"{month_abbr}-{year}"
                
        except Exception:
            return "APR-2024"  # Default fallback
    
    def _get_quarter_from_month(self, month: str) -> str:
        """
        Get quarter from month string
        
        Args:
            month: Month in format "APR-2024"
            
        Returns:
            Quarter string (Q1, Q2, Q3, Q4)
        """
        try:
            month_abbr = month.split('-')[0]
            
            quarter_mapping = {
                "APR": "Q1", "MAY": "Q1", "JUN": "Q1",
                "JUL": "Q2", "AUG": "Q2", "SEP": "Q2",
                "OCT": "Q3", "NOV": "Q3", "DEC": "Q3",
                "JAN": "Q4", "FEB": "Q4", "MAR": "Q4"
            }
            
            return quarter_mapping.get(month_abbr, "Q1")
            
        except Exception:
            return "Q1"  # Default fallback