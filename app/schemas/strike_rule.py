from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrikeRuleBase(BaseModel):
    rule_type: str = Field(..., min_length=1, max_length=50, description="Rule type: Early Coming, Late Coming, Early Going, Late Going, Late Lunch")
    minutes: int = Field(default=0, ge=0, le=1440, description="Minutes threshold (0-1440)")
    strike: str = Field(default="None", description="Strike color: None, Green, Orange, Red, Yellow")
    full_day_only: bool = Field(default=False, description="Apply only if full-day present")
    time_adjustment: str = Field(default="No Adjustment", description="Time adjustment type: No Adjustment, Ignore Late/Early, Round")
    round_direction: str = Field(default="next", description="Round direction: next or previous")
    round_minutes: int = Field(default=5, ge=1, le=60, description="Round minutes (1-60)")
    business_id: int = Field(..., gt=0, description="Business ID")

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v):
        """Validate rule type is one of allowed values"""
        allowed = ["Early Coming", "Late Coming", "Early Going", "Late Going", "Late Lunch"]
        if v not in allowed:
            raise ValueError(f"rule_type must be one of {allowed}")
        return v

    @field_validator("strike")
    @classmethod
    def validate_strike(cls, v):
        """Validate strike is one of allowed values"""
        allowed = ["None", "Green", "Orange", "Red", "Yellow"]
        if v not in allowed:
            raise ValueError(f"strike must be one of {allowed}")
        return v

    @field_validator("time_adjustment")
    @classmethod
    def validate_time_adjustment(cls, v):
        """Validate time adjustment is one of allowed values"""
        allowed = ["No Adjustment", "Ignore Late/Early", "Round"]
        if v not in allowed:
            raise ValueError(f"time_adjustment must be one of {allowed}")
        return v

    @field_validator("round_direction")
    @classmethod
    def validate_round_direction(cls, v):
        """Validate round direction is one of allowed values"""
        allowed = ["next", "previous"]
        if v not in allowed:
            raise ValueError(f"round_direction must be one of {allowed}")
        return v


class StrikeRuleCreate(StrikeRuleBase):
    pass


class StrikeRuleUpdate(BaseModel):
    minutes: Optional[int] = Field(None, ge=0, le=1440, description="Minutes threshold (0-1440)")
    strike: Optional[str] = Field(None, description="Strike color: None, Green, Orange, Red, Yellow")
    full_day_only: Optional[bool] = Field(None, description="Apply only if full-day present")
    time_adjustment: Optional[str] = Field(None, description="Time adjustment type")
    round_direction: Optional[str] = Field(None, description="Round direction: next or previous")
    round_minutes: Optional[int] = Field(None, ge=1, le=60, description="Round minutes (1-60)")

    @field_validator("strike")
    @classmethod
    def validate_strike(cls, v):
        """Validate strike is one of allowed values"""
        if v is not None:
            allowed = ["None", "Green", "Orange", "Red", "Yellow"]
            if v not in allowed:
                raise ValueError(f"strike must be one of {allowed}")
        return v

    @field_validator("time_adjustment")
    @classmethod
    def validate_time_adjustment(cls, v):
        """Validate time adjustment is one of allowed values"""
        if v is not None:
            allowed = ["No Adjustment", "Ignore Late/Early", "Round"]
            if v not in allowed:
                raise ValueError(f"time_adjustment must be one of {allowed}")
        return v

    @field_validator("round_direction")
    @classmethod
    def validate_round_direction(cls, v):
        """Validate round direction is one of allowed values"""
        if v is not None:
            allowed = ["next", "previous"]
            if v not in allowed:
                raise ValueError(f"round_direction must be one of {allowed}")
        return v


class StrikeRuleResponse(StrikeRuleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
