from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Workflow(BaseModel):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    fields = Column(Integer, default=0)
    steps = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    business = relationship("Business", back_populates="workflows")
