# Custom exceptions for the application

from fastapi import HTTPException


class ValidationError(HTTPException):
    """Exception raised for validation errors"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=400, detail=detail)


class NotFoundError(HTTPException):
    """Exception raised when a resource is not found"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)