"""
Business Information Schemas
"""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Any
from datetime import datetime


class BusinessInformationBase(BaseModel):
    business_id: int

    # Bank Details
    bank_name: Optional[str] = Field(None, max_length=255)
    bank_branch: Optional[str] = Field(None, max_length=255)
    bank_ifsc: Optional[str] = Field(None, max_length=50)
    bank_account: Optional[str] = Field(None, max_length=100)

    # Statutory Information
    pan: Optional[str] = Field(None, max_length=50)
    tan: Optional[str] = Field(None, max_length=50)
    gstin: Optional[str] = Field(None, max_length=50)
    esi: Optional[str] = Field(None, max_length=100)
    pf: Optional[str] = Field(None, max_length=100)
    shop_act: Optional[str] = Field(None, max_length=100)
    labour_act: Optional[str] = Field(None, max_length=100)

    # Employee Additional Info
    employee_info: List[str] = Field(
        default_factory=lambda: [f"Other Info {i+1}" for i in range(10)]
    )
    
    @model_validator(mode='before')
    @classmethod
    def trim_strings(cls, data: Any) -> Any:
        """Trim whitespace from string fields"""
        if isinstance(data, dict):
            string_fields = [
                'bank_name', 'bank_branch', 'bank_ifsc', 'bank_account',
                'pan', 'tan', 'gstin', 'esi', 'pf', 'shop_act', 'labour_act'
            ]
            
            for field in string_fields:
                if field in data and isinstance(data[field], str):
                    trimmed = data[field].strip()
                    data[field] = trimmed if trimmed else None
            
            # Trim employee_info array elements
            if 'employee_info' in data and isinstance(data['employee_info'], list):
                data['employee_info'] = [
                    item.strip() if isinstance(item, str) else item
                    for item in data['employee_info']
                ]
        
        return data


class BusinessInformationCreate(BusinessInformationBase):
    pass


class BusinessInformationUpdate(BaseModel):
    # Bank Details
    business_id: int

    bank_name: Optional[str] = Field(None, max_length=255)
    bank_branch: Optional[str] = Field(None, max_length=255)
    bank_ifsc: Optional[str] = Field(None, max_length=50)
    bank_account: Optional[str] = Field(None, max_length=100)

    # Statutory Information
    pan: Optional[str] = Field(None, max_length=50)
    tan: Optional[str] = Field(None, max_length=50)
    gstin: Optional[str] = Field(None, max_length=50)
    esi: Optional[str] = Field(None, max_length=100)
    pf: Optional[str] = Field(None, max_length=100)
    shop_act: Optional[str] = Field(None, max_length=100)
    labour_act: Optional[str] = Field(None, max_length=100)

    # Employee Additional Info
    employee_info: Optional[List[str]] = None
    
    @model_validator(mode='before')
    @classmethod
    def trim_strings(cls, data: Any) -> Any:
        """Trim whitespace from string fields"""
        if isinstance(data, dict):
            string_fields = [
                'bank_name', 'bank_branch', 'bank_ifsc', 'bank_account',
                'pan', 'tan', 'gstin', 'esi', 'pf', 'shop_act', 'labour_act'
            ]
            
            for field in string_fields:
                if field in data and data[field] is not None and isinstance(data[field], str):
                    trimmed = data[field].strip()
                    data[field] = trimmed if trimmed else None
            
            # Trim employee_info array elements
            if 'employee_info' in data and data['employee_info'] is not None and isinstance(data['employee_info'], list):
                data['employee_info'] = [
                    item.strip() if isinstance(item, str) else item
                    for item in data['employee_info']
                ]
        
        return data


class BusinessInformationResponse(BusinessInformationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
