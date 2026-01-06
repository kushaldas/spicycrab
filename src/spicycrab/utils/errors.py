"""Custom exceptions for spicycrab."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class CrabpyError(Exception):
    """Base exception for all crabpy errors."""

    def __init__(self, message: str, filename: str | None = None, line: int | None = None) -> None:
        self.message = message
        self.filename = filename
        self.line = line
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        parts = []
        if self.filename:
            parts.append(self.filename)
        if self.line is not None:
            parts.append(f"line {self.line}")
        location = ":".join(parts)
        if location:
            return f"{location}: {self.message}"
        return self.message


class ParseError(CrabpyError):
    """Error during Python source parsing."""

    pass


class TypeAnnotationError(CrabpyError):
    """Error related to type annotations - missing or invalid."""

    def __init__(
        self,
        message: str,
        name: str | None = None,
        filename: str | None = None,
        line: int | None = None,
    ) -> None:
        self.name = name
        if name and "missing" not in message.lower():
            message = f"'{name}': {message}"
        super().__init__(message, filename, line)


class UnsupportedFeatureError(CrabpyError):
    """Error when encountering a Python feature not supported by spicycrab."""

    def __init__(
        self,
        feature: str,
        filename: str | None = None,
        line: int | None = None,
        suggestion: str | None = None,
    ) -> None:
        self.feature = feature
        self.suggestion = suggestion
        message = f"Unsupported Python feature: {feature}"
        if suggestion:
            message += f". {suggestion}"
        super().__init__(message, filename, line)


class CodegenError(CrabpyError):
    """Error during Rust code generation."""

    pass


@dataclass
class ErrorLocation:
    """Location information for error reporting."""

    filename: str | None = None
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    def __str__(self) -> str:
        parts = []
        if self.filename:
            parts.append(self.filename)
        if self.line is not None:
            loc = str(self.line)
            if self.column is not None:
                loc += f":{self.column}"
            parts.append(loc)
        return ":".join(parts) if parts else "<unknown>"
