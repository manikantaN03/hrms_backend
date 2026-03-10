from sqlalchemy import Column, Integer, String,ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class ExitReason(BaseModel):
    __tablename__ = "exit_reasons"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    esi_mapping = Column(String, default="None")
    business = relationship("Business", back_populates="exit_reasons")
