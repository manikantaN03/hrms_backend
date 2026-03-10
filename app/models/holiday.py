from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    name = Column(String, nullable=False)

    # relationship to Location
    location = relationship("Location", back_populates="holidays")
    # relationship to Business
    business = relationship("Business", back_populates="holidays")
    
    



class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
