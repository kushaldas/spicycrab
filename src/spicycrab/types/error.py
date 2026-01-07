"""Base Error type for Rust-like error handling.

This is a type stub for transpilation - provides the interface
that maps to Rust's std::error::Error trait.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Error:
    """Base error type that maps to Rust's std::error::Error trait.

    In Rust, this becomes a type implementing the Error trait.
    Users should subclass this for custom error types.

    Example:
        class ParseError(Error):
            def __init__(self, message: str, line: int) -> None:
                super().__init__(message)
                self.line = line

        # Transpiles to:
        # #[derive(Debug)]
        # struct ParseError {
        #     message: String,
        #     line: i64,
        # }
        # impl std::error::Error for ParseError {}
    """

    __match_args__ = ("message",)

    def __init__(self, message: str = "") -> None:
        """Create a new error with the given message."""
        self._message = message

    @property
    def message(self) -> str:
        """Get the error message."""
        return self._message

    def source(self) -> Error | None:
        """Return the lower-level source of this error, if any.

        Maps to Rust's Error::source() method.
        """
        return None

    def description(self) -> str:
        """Return a short description of the error.

        Deprecated in Rust, but included for compatibility.
        Maps to Error::description().
        """
        return self._message

    def __str__(self) -> str:
        """Display the error message."""
        return self._message

    def __repr__(self) -> str:
        """Debug representation."""
        return f"{self.__class__.__name__}({self._message!r})"
