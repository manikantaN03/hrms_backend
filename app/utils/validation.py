"""
Validation Utilities for Employee APIs
Ensures no empty request bodies and proper field validation
"""

from fastapi import HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional


def validate_non_empty_request(data: BaseModel, operation_name: str) -> Dict[str, Any]:
    """
    🚨 MANDATORY VALIDATION: Reject empty {} request bodies
    Ensures at least one valid field is provided for any operation
    
    Args:
        data: Pydantic model instance
        operation_name: Name of the operation for error messages
        
    Returns:
        Dict of non-empty values
        
    Raises:
        HTTPException: If request body is empty or contains no valid data
    """
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request body cannot be empty for {operation_name}. Please provide valid data."
        )
    
    # Get all values excluding unset fields
    data_dict = data.dict(exclude_unset=True)
    
    # Filter out None values and empty strings
    non_empty_values = {}
    for key, value in data_dict.items():
        if value is not None:
            # For strings, check if they're not just whitespace
            if isinstance(value, str):
                if value.strip():
                    non_empty_values[key] = value.strip()
            else:
                non_empty_values[key] = value
    
    if not non_empty_values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request body cannot be empty for {operation_name}. At least one valid field must be provided. Empty {{}} request bodies are not allowed."
        )
    
    return non_empty_values


def validate_required_fields(data: Dict[str, Any], required_fields: List[str], operation_name: str) -> None:
    """
    Validate that all required fields are present and not empty
    
    Args:
        data: Dictionary of data to validate
        required_fields: List of field names that are required
        operation_name: Name of the operation for error messages
        
    Raises:
        HTTPException: If any required fields are missing or empty
    """
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            empty_fields.append(field)
    
    error_messages = []
    if missing_fields:
        error_messages.append(f"Missing required fields: {', '.join(missing_fields)}")
    if empty_fields:
        error_messages.append(f"Required fields cannot be empty: {', '.join(empty_fields)}")
    
    if error_messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed for {operation_name}. {' '.join(error_messages)}"
        )


def validate_email_format(email: str, field_name: str = "email") -> str:
    """
    Validate email format
    
    Args:
        email: Email string to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated email string
        
    Raises:
        HTTPException: If email format is invalid
    """
    import re
    
    if not email or not email.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty"
        )
    
    email = email.strip().lower()
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format. Please provide a valid email address."
        )
    
    return email


def validate_phone_number(phone: str, field_name: str = "phone") -> str:
    """
    Validate phone number format
    
    Args:
        phone: Phone number string to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated phone number string
        
    Raises:
        HTTPException: If phone number format is invalid
    """
    if not phone or not phone.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty"
        )
    
    # Remove any spaces, dashes, or parentheses for validation
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    if len(clean_phone) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be at least 10 digits long"
        )
    
    if len(clean_phone) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be longer than 15 digits"
        )
    
    return phone.strip()


def validate_date_format(date_str: str, field_name: str = "date") -> str:
    """
    Validate date format (YYYY-MM-DD)
    
    Args:
        date_str: Date string to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated date string
        
    Raises:
        HTTPException: If date format is invalid
    """
    from datetime import datetime
    
    if not date_str or not date_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty"
        )
    
    try:
        datetime.strptime(date_str.strip(), '%Y-%m-%d')
        return date_str.strip()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format. Use YYYY-MM-DD format (e.g., 2024-01-15)."
        )


def validate_positive_number(value: float, field_name: str = "value") -> float:
    """
    Validate that a number is positive
    
    Args:
        value: Number to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated number
        
    Raises:
        HTTPException: If number is not positive
    """
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty"
        )
    
    if value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be greater than 0"
        )
    
    return value


def validate_string_length(value: str, field_name: str, min_length: int = 1, max_length: int = 255) -> str:
    """
    Validate string length constraints
    
    Args:
        value: String to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        Validated string
        
    Raises:
        HTTPException: If string length is invalid
    """
    if not value or not value.strip():
        if min_length > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} cannot be empty"
            )
        return ""
    
    value = value.strip()
    
    if len(value) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be at least {min_length} characters long"
        )
    
    if len(value) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be longer than {max_length} characters"
        )
    
    return value


def validate_enum_value(value: str, field_name: str, allowed_values: List[str]) -> str:
    """
    Validate that a value is in the allowed enum values
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        allowed_values: List of allowed values
        
    Returns:
        Validated value
        
    Raises:
        HTTPException: If value is not in allowed values
    """
    if not value or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot be empty"
        )
    
    value = value.strip().lower()
    allowed_lower = [v.lower() for v in allowed_values]
    
    if value not in allowed_lower:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}. Allowed values are: {', '.join(allowed_values)}"
        )
    
    # Return the original case from allowed_values
    return allowed_values[allowed_lower.index(value)]


def create_validation_error_response(operation_name: str, error_details: str) -> Dict[str, Any]:
    """
    Create a standardized validation error response
    
    Args:
        operation_name: Name of the operation that failed
        error_details: Detailed error message
        
    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "error": f"Validation failed for {operation_name}",
        "details": error_details,
        "message": "Request body validation failed. Please check your input data and try again."
    }


def create_success_response(operation_name: str, data: Optional[Dict[str, Any]] = None, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a standardized success response
    
    Args:
        operation_name: Name of the operation that succeeded
        data: Optional data to include in response
        message: Optional custom message
        
    Returns:
        Standardized success response dictionary
    """
    return {
        "success": True,
        "message": message or f"{operation_name} completed successfully",
        "data": data or {}
    }