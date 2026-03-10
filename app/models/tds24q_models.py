from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.models.base import Base
from sqlalchemy.orm import relationship

class TDS24Q(Base):
    __tablename__ = "tds_24q_info"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    # General Info
    deductor_type = Column(String(100), nullable=False)
    section_code = Column(String(100), nullable=False)
    state = Column(String(100))
    ministry = Column(String(100))
    ministry_name = Column(String(200), nullable=True)
    ain_number = Column(String(50), nullable=True)
    pao_code = Column(String(50), nullable=True)
    pao_registration = Column(String(100), nullable=True)
    ddo_code = Column(String(50), nullable=True)
    ddo_registration = Column(String(100), nullable=True)
    
    # Employer Details
    employer_name = Column(String(200), nullable=False)
    branch = Column(String(200), nullable=False)
    address1 = Column(String(200), nullable=False)
    address2 = Column(String(200), nullable=True)
    address3 = Column(String(200), nullable=True)
    address4 = Column(String(200), nullable=True)
    address5 = Column(String(200), nullable=True)
    employer_state = Column(String(100), nullable=False)
    pin = Column(String(10), nullable=False)
    pan = Column(String(10), nullable=False)
    tan = Column(String(10), nullable=False)
    email = Column(String(100), nullable=False)
    std_code = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    alt_email = Column(String(100), nullable=True)
    alt_std_code = Column(String(10), nullable=True)
    alt_phone = Column(String(20), nullable=True)
    gst = Column(String(15), nullable=True)
    
    # Responsible Person Details
    name = Column(String(200), nullable=False)
    designation = Column(String(100), nullable=False)
    res_address1 = Column(String(200), nullable=False)
    res_address2 = Column(String(200), nullable=True)
    res_address3 = Column(String(200), nullable=True)
    res_address4 = Column(String(200), nullable=True)
    res_address5 = Column(String(200), nullable=True)
    res_state = Column(String(100), nullable=False)
    res_pin = Column(String(10), nullable=False)
    res_pan = Column(String(10), nullable=False)
    res_mobile = Column(String(15), nullable=False)
    res_email = Column(String(100), nullable=False)
    res_std_code = Column(String(10), nullable=True)
    res_phone = Column(String(20), nullable=True)
    res_alt_email = Column(String(100), nullable=True)
    res_alt_std_code = Column(String(10), nullable=True)
    res_alt_phone = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship - MUST be inside the class
    business = relationship("Business", back_populates="tds_24q_info")