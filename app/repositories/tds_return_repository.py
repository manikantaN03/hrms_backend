"""
TDS Return Repository
Database operations for TDS return management
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.models.datacapture import TDSReturn


class TDSReturnRepository:
    """Repository for TDS return database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_returns_by_financial_year(
        self,
        financial_year: str,
        business_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all TDS returns for a financial year
        
        Args:
            financial_year: Financial year in format "2024-25"
            business_id: Business ID filter
            
        Returns:
            List of return data
        """
        try:
            query = self.db.query(TDSReturn).filter(
                TDSReturn.financial_year == financial_year
            )
            
            if business_id:
                query = query.filter(TDSReturn.business_id == business_id)
            
            returns = query.order_by(TDSReturn.quarter).all()
            
            # Format response
            result = []
            for return_record in returns:
                result.append({
                    "id": return_record.id,
                    "quarter": return_record.quarter,
                    "receipt_number": return_record.acknowledgment_number or "",
                    "return_type": return_record.return_type,
                    "filing_date": return_record.filing_date.strftime("%Y-%m-%d") if return_record.filing_date else "",
                    "total_tds_amount": float(return_record.total_tds_amount),
                    "total_deductees": return_record.total_deductees,
                    "is_filed": return_record.is_filed,
                    "created_at": return_record.created_at.isoformat() if return_record.created_at else None,
                    "updated_at": return_record.updated_at.isoformat() if return_record.updated_at else None
                })
            
            return result
            
        except Exception as e:
            raise Exception(f"Database error in get_returns_by_financial_year: {str(e)}")
    
    def get_return_by_quarter(
        self,
        financial_year: str,
        quarter: str,
        business_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get TDS return for a specific quarter
        
        Args:
            financial_year: Financial year in format "2024-25"
            quarter: Quarter (Q1, Q2, Q3, Q4)
            business_id: Business ID
            
        Returns:
            Return data or None if not found
        """
        try:
            query = self.db.query(TDSReturn).filter(
                TDSReturn.financial_year == financial_year,
                TDSReturn.quarter == quarter
            )
            
            if business_id:
                query = query.filter(TDSReturn.business_id == business_id)
            
            return_record = query.first()
            
            if return_record:
                return {
                    "id": return_record.id,
                    "quarter": return_record.quarter,
                    "receipt_number": return_record.acknowledgment_number or "",
                    "return_type": return_record.return_type,
                    "filing_date": return_record.filing_date.strftime("%Y-%m-%d") if return_record.filing_date else "",
                    "total_tds_amount": float(return_record.total_tds_amount),
                    "total_deductees": return_record.total_deductees,
                    "is_filed": return_record.is_filed,
                    "created_at": return_record.created_at.isoformat() if return_record.created_at else None,
                    "updated_at": return_record.updated_at.isoformat() if return_record.updated_at else None
                }
            
            return None
            
        except Exception as e:
            raise Exception(f"Database error in get_return_by_quarter: {str(e)}")
    
    def save_return_quarter(
        self,
        financial_year: str,
        quarter: str,
        receipt_number: str,
        return_type: str = "24Q",
        filing_date: Optional[date] = None,
        business_id: Optional[int] = None,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Save or update TDS return for a specific quarter
        
        Args:
            financial_year: Financial year in format "2024-25"
            quarter: Quarter (Q1, Q2, Q3, Q4)
            receipt_number: Acknowledgment/receipt number
            return_type: Type of return (24Q, 26Q, etc.)
            filing_date: Date of filing
            business_id: Business ID
            created_by: User ID who created
            
        Returns:
            Save result with return ID
        """
        try:
            # Check if return already exists for this quarter
            existing_return = self.db.query(TDSReturn).filter(
                TDSReturn.financial_year == financial_year,
                TDSReturn.quarter == quarter
            )
            
            if business_id:
                existing_return = existing_return.filter(TDSReturn.business_id == business_id)
            
            existing_return = existing_return.first()
            
            if existing_return:
                # Update existing return
                if receipt_number:
                    existing_return.acknowledgment_number = receipt_number
                if filing_date:
                    existing_return.filing_date = filing_date
                if return_type:
                    existing_return.return_type = return_type
                
                existing_return.is_filed = bool(receipt_number)
                existing_return.updated_at = datetime.now()
                
                self.db.commit()
                self.db.refresh(existing_return)
                
                return {"return_id": existing_return.id}
            
            else:
                # Create new return
                new_return = TDSReturn(
                    business_id=business_id or 1,
                    return_type=return_type,
                    financial_year=financial_year,
                    quarter=quarter,
                    filing_date=filing_date or date.today(),
                    acknowledgment_number=receipt_number or "",
                    total_deductees=0,  # Will be calculated later
                    total_tds_amount=Decimal("0.00"),  # Will be calculated later
                    total_deposited=Decimal("0.00"),  # Will be calculated later
                    is_filed=bool(receipt_number),
                    is_revised=False,
                    revision_number=0,
                    remarks=f"TDS return for {quarter} {financial_year}",
                    created_by=created_by
                )
                
                self.db.add(new_return)
                self.db.commit()
                self.db.refresh(new_return)
                
                return {"return_id": new_return.id}
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Database error in save_return_quarter: {str(e)}")
    
    def delete_return_quarter(
        self,
        financial_year: str,
        quarter: str,
        business_id: Optional[int] = None
    ) -> bool:
        """
        Delete TDS return for a specific quarter
        
        Args:
            financial_year: Financial year in format "2024-25"
            quarter: Quarter (Q1, Q2, Q3, Q4)
            business_id: Business ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            query = self.db.query(TDSReturn).filter(
                TDSReturn.financial_year == financial_year,
                TDSReturn.quarter == quarter
            )
            
            if business_id:
                query = query.filter(TDSReturn.business_id == business_id)
            
            return_record = query.first()
            
            if return_record:
                self.db.delete(return_record)
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Database error in delete_return_quarter: {str(e)}")
    
    def get_returns_summary(
        self,
        financial_year: str,
        business_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for TDS returns
        
        Args:
            financial_year: Financial year in format "2024-25"
            business_id: Business ID
            
        Returns:
            Summary statistics
        """
        try:
            query = self.db.query(TDSReturn).filter(
                TDSReturn.financial_year == financial_year
            )
            
            if business_id:
                query = query.filter(TDSReturn.business_id == business_id)
            
            returns = query.all()
            
            total_quarters = 4
            filed_quarters = len([r for r in returns if r.is_filed])
            pending_quarters = total_quarters - filed_quarters
            
            total_tds_amount = sum([float(r.total_tds_amount) for r in returns])
            total_deductees = sum([r.total_deductees for r in returns])
            
            return {
                "financial_year": financial_year,
                "total_quarters": total_quarters,
                "filed_quarters": filed_quarters,
                "pending_quarters": pending_quarters,
                "completion_percentage": round((filed_quarters / total_quarters) * 100, 2),
                "total_tds_amount": total_tds_amount,
                "total_deductees": total_deductees
            }
            
        except Exception as e:
            raise Exception(f"Database error in get_returns_summary: {str(e)}")