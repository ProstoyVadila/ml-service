# mypy: ignore-errors
# ruff: noqa: C901
import asyncio
import functools
import logging
import random
import sys
import time
from typing import (
    Any,
    Callable,
    Coroutine,
    ParamSpec,
    TypeVar,
    overload,
)

P = ParamSpec("P")
T = TypeVar("T")
AnyFunc = Callable[..., Any]


class Retry:
    """
    A decorator class for retrying function calls on specified exceptions, with optional backoff and logging.
    This class can be used to decorate both synchronous and asynchronous functions.
    """

    __slots__ = ("verbose", "n_times", "sleep_duration", "increasing")

    def __init__(self, verbose: bool = False) -> None:
        self.verbose: bool = verbose

    @overload
    def __call__(
        self,
        n_times: int = ...,
        sleep_duration: float = ...,
        increasing: bool = ...,
        verbose: bool = ...,
        allowed_exceptions: tuple[type[BaseException], ...] = ...,
    ) -> Callable[[Callable[P, T]], Callable[P, T]]: ...

    @overload
    def __call__(
        self,
        n_times: int = ...,
        sleep_duration: float = ...,
        increasing: bool = ...,
        verbose: bool = ...,
        allowed_exceptions: tuple[type[BaseException], ...] = ...,
    ) -> Callable[
        [Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]
    ]: ...

    def __call__(
        self,
        n_times: int = 5,
        sleep_duration: float = 1.2,
        increasing: bool = False,
        verbose: bool = False,
        allowed_exceptions: tuple[type[BaseException], ...] = (Exception,),
    ) -> Callable[[AnyFunc], AnyFunc]:
        self.n_times = n_times
        self.sleep_duration = sleep_duration
        self.increasing = increasing
        self.verbose = verbose

        def decorator(func: AnyFunc) -> AnyFunc:
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                exc_info = (None, None, None)
                for i in range(self.n_times):
                    try:
                        return await func(*args, **kwargs)
                    except allowed_exceptions as exc:
                        sleep = (
                            self.sleep_duration
                            if not self.increasing
                            else self._get_increasing_duration(i + 1)
                        )
                        sleep = round(sleep, 2)
                        logging.warning(
                            f"Retry {i + 1}/{self.n_times} (sleep: {sleep}s) of {func.__name__} failed: {exc}"
                        )
                        exc_info = sys.exc_info()
                        if self.verbose:
                            logging.warning(
                                f"exc_info for {func.__name__}", exc_info=exc_info
                            )
                        await asyncio.sleep(sleep)
                if exc_info[0] is not None:
                    raise exc_info[1].with_traceback(exc_info[2])  # type: ignore
                raise RuntimeError(
                    f"{func.__name__} failed after {self.n_times} retries"
                )

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                exc_info = (None, None, None)
                for i in range(self.n_times):
                    try:
                        return func(*args, **kwargs)
                    except allowed_exceptions as exc:
                        sleep = (
                            self.sleep_duration
                            if not self.increasing
                            else self._get_increasing_duration(i + 1)
                        )
                        sleep = round(sleep, 2)
                        logging.warning(
                            f"Retry {i + 1}/{self.n_times} (sleep: {sleep}s) of {func.__name__} failed: {exc}"
                        )
                        exc_info = sys.exc_info()
                        if self.verbose:
                            logging.warning(
                                f"exc_info for {func.__name__}", exc_info=exc_info
                            )
                        time.sleep(sleep)
                if exc_info[0] is not None:
                    raise exc_info[1].with_traceback(exc_info[2])
                raise RuntimeError(
                    f"{func.__name__} failed after {self.n_times} retries"
                )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def _get_increasing_duration(self, step: int) -> float:
        base = self.sleep_duration * (2 ** (step - 1))
        max_duration = self.sleep_duration * self.n_times
        duration = min(base, max_duration)
        jitter = random.uniform(0.8, 1.2)
        return duration * jitter
