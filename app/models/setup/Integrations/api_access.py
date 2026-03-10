from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import Base


class APIAccess(Base):
    __tablename__ = "api_access"

    id = Column(Integer, primary_key=True, index=True)

    business_id = Column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    api_key = Column("apiKey", String(100), nullable=True)
    is_enabled = Column("apiEnabled", Boolean, nullable=False, default=False)

    business = relationship("Business", back_populates="api_access")
