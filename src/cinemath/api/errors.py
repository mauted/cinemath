"""Typed errors and retry classification."""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID_INPUT = "invalid_input"
    UNSUPPORTED_PROBLEM = "unsupported_problem"
    PLANNING_FAILED = "planning_failed"
    VERIFICATION_FAILED = "verification_failed"
    RENDER_FAILED = "render_failed"
    RENDER_TIMEOUT = "render_timeout"
    CANCELLED = "cancelled"
    INTERNAL = "internal"


RETRYABLE_ERROR_CODES = frozenset(
    {
        ErrorCode.PLANNING_FAILED,
        ErrorCode.RENDER_FAILED,
        ErrorCode.RENDER_TIMEOUT,
        ErrorCode.INTERNAL,
    }
)


class CinemathError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        retryable: bool = False,
        cause: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.cause = cause

    @classmethod
    def permanent(
        cls,
        code: ErrorCode,
        message: str,
        *,
        cause: str | None = None,
    ) -> CinemathError:
        return cls(code=code, message=message, retryable=False, cause=cause)

    @classmethod
    def retryable(
        cls,
        code: ErrorCode,
        message: str,
        *,
        cause: str | None = None,
    ) -> CinemathError:
        return cls(code=code, message=message, retryable=True, cause=cause)

    @classmethod
    def from_code(
        cls,
        code: ErrorCode,
        message: str,
        *,
        cause: str | None = None,
    ) -> CinemathError:
        return cls(
            code=code,
            message=message,
            retryable=code in RETRYABLE_ERROR_CODES,
            cause=cause,
        )
