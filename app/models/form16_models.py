from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.models.base import Base
from sqlalchemy.orm import relationship
from app.models.business import Business


class PersonResponsible(Base):
    __tablename__ = "person_responsible"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(50), nullable=False)
    designation = Column(String(50), nullable=False)
    father_name = Column(String(50), nullable=False)
    signature_path = Column(String(255), nullable=True)

    # business relation
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    business = relationship("Business", back_populates="person_responsibles", lazy="joined")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmployerInfo(Base):
    __tablename__ = "employer_info"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    address1 = Column(String(512), nullable=True)
    address2 = Column(String(512), nullable=True)
    address3 = Column(String(512), nullable=True)
    place_of_issue = Column(String(255), nullable=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    business = relationship("Business", back_populates="employer_info", lazy="joined")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CitInfo(Base):
    __tablename__ = "cit_info"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    address1 = Column(String(512), nullable=True)
    address2 = Column(String(512), nullable=True)
    address3 = Column(String(512), nullable=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=True, index=True)
    business = relationship("Business", back_populates="cit_info", lazy="joined")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)