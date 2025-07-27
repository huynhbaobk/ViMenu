"""
Custom exception handlers and error responses
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class ViMenuException(Exception):
    """Base exception for ViMenu application"""
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class OCRException(ViMenuException):
    """OCR processing exception"""
    def __init__(self, message: str = "OCR processing failed", details: Dict[str, Any] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class ImageProcessingException(ViMenuException):
    """Image processing exception"""
    def __init__(self, message: str = "Image processing failed", details: Dict[str, Any] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class CacheException(ViMenuException):
    """Cache operation exception"""
    def __init__(self, message: str = "Cache operation failed", details: Dict[str, Any] = None):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE, details)


async def vimenu_exception_handler(request: Request, exc: ViMenuException) -> JSONResponse:
    """Handle custom ViMenu exceptions"""
    logger.error(f"ViMenu error: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors"""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation failed",
            "details": exc.errors(),
            "type": "ValidationError"
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Internal server error",
            "type": "InternalServerError"
        }
    )
