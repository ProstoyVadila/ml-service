"""Throttling middleware for the FastAPI application."""

import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from ml_service.settings.config import config


class ThrottlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to throttle requests based on IP address.

    This middleware limits the number of requests an IP address can make
    within a specified time window (defaults to 60 seconds).
    """

    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)
        self.rate_limit = config.throttling.rate_limit_per_minute
        self.time_window = 60  # in seconds

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Dispatch method to process incoming requests and apply throttling.

        Args:
            request: The incoming request.
            call_next: The next middleware or endpoint to call.

        Returns:
            The response from the next middleware or endpoint, or a
            JSONResponse with a 429 status code if the rate limit is exceeded.
        """
        client_ip = request.client.host if request.client else "unknown"
        request_time = time.time()

        # Remove timestamps outside the current time window
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if t > request_time - self.time_window
        ]

        if len(self.requests[client_ip]) >= self.rate_limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
            )

        self.requests[client_ip].append(request_time)
        return await call_next(request)
