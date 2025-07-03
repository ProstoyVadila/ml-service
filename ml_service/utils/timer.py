import time
import asyncio
from typing import TypeVar, ParamSpec
from functools import wraps
from collections.abc import Callable

from ml_service.settings.logger import logger

P = ParamSpec("P")
T = TypeVar("T")


def timer(func: Callable[P, T]) -> Callable[P, T | asyncio.Future]:
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            t0 = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                dt = time.perf_counter() - t0
                name = func.__name__
                if args:
                    cls = getattr(args[0], "__class__", None)
                    if cls is not None:
                        name = f"{cls.__name__}.{name}"
                logger.info(f"[Timer] {name}: {dt:0.3f} seconds")

        return async_wrapper  # type: ignore[return-value]

    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        t0 = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            dt = time.perf_counter() - t0
            name = func.__name__
            if args:
                cls = getattr(args[0], "__class__", None)
                if cls is not None:
                    name = f"{cls.__name__}.{name}"
            logger.info(f"[Timer] {name}: {dt:0.3f} seconds")

    return sync_wrapper
