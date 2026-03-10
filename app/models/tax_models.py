from datetime import date
from sqlalchemy import Column, Integer, String, Boolean, Date, Numeric, ForeignKey
from .base import Base
from .setup.salary_and_deductions.salary_component import SalaryComponent
from sqlalchemy.orm import relationship

class TDSSetting(Base):
    __tablename__ = "tds_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    deduct_tds = Column(Boolean, default=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    updated_at = Column(Date, default=date.today)


class FinancialYear(Base):
    __tablename__ = "financial_years"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    year = Column(String, unique=True, index=True)
    open = Column(Boolean, default=False)
    start_date = Column(Date)
    end_date = Column(Date)

    business = relationship("Business", back_populates="financial_years")

class TaxRate(Base):
    __tablename__ = "tax_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True) 
    financial_year = Column(String, index=True)
    scheme = Column(String)  # Old Scheme, New Scheme
    category = Column(String)  # < 60 Yr., All
    income_from = Column(Numeric(12, 2))
    fixed_tax = Column(Numeric(12, 2))
    progressive_rate = Column(Numeric(5, 2))
    

    business = relationship("Business", back_populates="tax_rates")