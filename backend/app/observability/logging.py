"""
Structured Logging & Request ID Middleware
Provides structured JSON logging, correlation IDs, latency measurement,
and sensitive data masking for API requests and application events.
"""

from contextvars import ContextVar
import json
import logging
import re
import time
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request correlation ID
current_request_id: ContextVar[str] = ContextVar("current_request_id", default="")

# Patterns for sensitive keys to mask
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(authorization|token|password|secret|api[-_]?key|credit[-_]?card)"
)


def mask_sensitive_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively mask sensitive values in dictionaries."""
    if not isinstance(data, dict):
        return data

    masked = {}
    for key, value in data.items():
        if SENSITIVE_KEY_PATTERN.search(key):
            masked[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_dict(value)
        elif isinstance(value, list):
            masked[key] = [
                mask_sensitive_dict(v) if isinstance(v, dict) else v
                for v in value
            ]
        else:
            masked[key] = value
    return masked


class StructuredJsonFormatter(logging.Formatter):
    """Custom logging formatter that produces JSON with request_id and metadata."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = getattr(record, "request_id", None) or current_request_id.get() or "none"

        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": req_id,
        }

        # Include custom attributes if present
        for attr in ["latency_ms", "status_code", "outcome", "error_code", "path", "method"]:
            if hasattr(record, attr):
                log_data[attr] = getattr(record, attr)

        return json.dumps(log_data)


def get_structured_logger(name: str = "loyalty_app") -> logging.Logger:
    """Return a configured logger with StructuredJsonFormatter."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)

    return logger


class RequestIDLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns X-Request-ID to each incoming request,
    times execution latency, and logs structured outcomes.
    """

    def __init__(self, app, logger: Optional[logging.Logger] = None):
        super().__init__(app)
        self.logger = logger or get_structured_logger("api_request")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Extract or generate Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        token = current_request_id.set(request_id)

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            status_code = response.status_code
            outcome = (
                "SUCCESS"
                if status_code < 400
                else "CLIENT_ERROR"
                if status_code < 500
                else "SERVER_ERROR"
            )

            response.headers["X-Request-ID"] = request_id

            extra = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "latency_ms": duration_ms,
                "outcome": outcome,
            }

            self.logger.info(
                f"{request.method} {request.url.path} finished with {status_code}",
                extra=extra,
            )

            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            extra = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "latency_ms": duration_ms,
                "outcome": "SERVER_ERROR",
                "error_code": type(exc).__name__,
            }
            self.logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {exc}",
                extra=extra,
            )
            raise
        finally:
            current_request_id.reset(token)

