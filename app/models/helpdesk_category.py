from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class HelpdeskCategory(BaseModel):
    __tablename__ = "helpdesk_categories"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    primary_approver = Column(String, nullable=True)
    backup_approver = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    business = relationship("Business", back_populates="helpdesk_categories")