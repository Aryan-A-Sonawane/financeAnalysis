"""Custom middleware for FastAPI."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log."""
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Log request
        start_time = time.time()
        
        logger.info(
            "http_request_started",
            method=request.method,
            path=request.url.path,
            correlation_id=correlation_id,
            client_host=request.client.host if request.client else None,
        )

        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log response
            logger.info(
                "http_request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                correlation_id=correlation_id,
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Response-Time"] = str(duration_ms)
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.error(
                "http_request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                error=str(e),
                exc_info=True,
            )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app: ASGIApp):
        """Initialize rate limiter."""
        super().__init__(app)
        self.requests = {}  # Simple in-memory storage (use Redis in production)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and process request."""
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client identifier (IP or user ID)
        client_id = request.client.host if request.client else "unknown"
        
        # For authenticated requests, use user ID
        # TODO: Extract user ID from JWT token
        
        current_time = time.time()
        window_start = current_time - 60  # 1-minute window

        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
        else:
            self.requests[client_id] = []

        # Check rate limit
        if len(self.requests[client_id]) >= settings.RATE_LIMIT_PER_MINUTE:
            logger.warning(
                "rate_limit_exceeded",
                client_id=client_id,
                path=request.url.path,
                requests_in_window=len(self.requests[client_id]),
            )
            
            return Response(
                content='{"detail": "Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
            )

        # Add current request
        self.requests[client_id].append(current_time)

        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = settings.RATE_LIMIT_PER_MINUTE - len(self.requests[client_id])
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response
