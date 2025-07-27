"""
Custom middleware for the ViMenu application
"""
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.core.logging import get_logger
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing and request ID"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Log request completion
        process_time = time.time() - start_time
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": round(process_time, 4)
            }
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app, calls_per_minute: int = 300):  # Increased from 60 to 300
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.clients: Dict[str, list] = {}
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks, static files, and docs
        excluded_paths = ["/health", "/api/health", "/", "/docs", "/redoc", "/openapi.json"]
        if (request.url.path in excluded_paths or 
            request.url.path.startswith("/static") or 
            request.url.path.startswith("/css") or 
            request.url.path.startswith("/js")):
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        current_time = datetime.utcnow()
        
        # Clean old entries and check rate limit
        if self._is_rate_limited(client_ip, current_time):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        # Record this request
        self._record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first (for reverse proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str, current_time: datetime) -> bool:
        """Check if client is rate limited"""
        if client_ip not in self.clients:
            return False
        
        # Remove old entries (older than 1 minute)
        cutoff_time = current_time - timedelta(minutes=1)
        self.clients[client_ip] = [
            timestamp for timestamp in self.clients[client_ip]
            if timestamp > cutoff_time
        ]
        
        # Check if limit exceeded
        return len(self.clients[client_ip]) >= self.calls_per_minute
    
    def _record_request(self, client_ip: str, current_time: datetime):
        """Record a request for the client"""
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        self.clients[client_ip].append(current_time)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Add CSP for static files
        if request.url.path.startswith("/static") or request.url.path == "/":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'"
            )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            logger.error(
                f"Unhandled exception in request {request_id}: {str(e)}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error_type": type(e).__name__
                }
            )
            
            # Return a generic error response
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "message": "Internal server error",
                    "request_id": request_id,
                    "type": "InternalServerError"
                }
            )


class FileValidationMiddleware(BaseHTTPMiddleware):
    """Validate file uploads"""
    
    def __init__(self, app, max_file_size: int = 5 * 1024 * 1024):
        super().__init__(app)
        self.max_file_size = max_file_size
        self.allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only check file upload endpoints
        if request.method == "POST" and "/analyze-menu" in request.url.path:
            content_type = request.headers.get("content-type", "")
            
            # Check if it's a multipart form (file upload)
            if "multipart/form-data" in content_type:
                # Read the body to check file size
                body = await request.body()
                
                if len(body) > self.max_file_size:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size allowed: {self.max_file_size // (1024*1024)}MB"
                    )
                
                # Recreate the request with the body we read
                from starlette.requests import Request as StarletteRequest
                
                async def receive():
                    return {"type": "http.request", "body": body, "more_body": False}
                
                request._receive = receive
        
        return await call_next(request)
