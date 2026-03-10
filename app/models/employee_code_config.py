from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
class EmployeeCodeSetting(BaseModel):
    __tablename__ = "employee_code_settings"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    auto_code = Column(Boolean, default=True)
    prefix = Column(String, default="EMP")
    length = Column(Integer, default=3)
    suffix = Column(String, default="")
    business = relationship("Business", back_populates="employee_code_settings")

    @property
    def autoCode(self):
        return self.auto_code

    @autoCode.setter
    def autoCode(self, value):
        self.auto_code = value
