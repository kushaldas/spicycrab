"""Rust-compatible types for spicycrab.

This module provides type stubs for Rust types that can be used in Python
type annotations. When transpiled, these types map directly to their Rust
equivalents.

Usage:
    from spicycrab.types import u8, u32, i64, Result, Ok, Err

    def add(a: u8, b: u8) -> u8:
        return a + b

    def divide(a: i64, b: i64) -> Result[i64, str]:
        if b == 0:
            return Err("division by zero")
        return Ok(a // b)
"""

from typing import Generic, TypeVar

# Type variables for generic types
T = TypeVar("T")
E = TypeVar("E")


# =============================================================================
# Rust Integer Types
# =============================================================================


class u8(int):
    """Rust u8: unsigned 8-bit integer (0 to 255)."""

    pass


class u16(int):
    """Rust u16: unsigned 16-bit integer (0 to 65,535)."""

    pass


class u32(int):
    """Rust u32: unsigned 32-bit integer (0 to 4,294,967,295)."""

    pass


class u64(int):
    """Rust u64: unsigned 64-bit integer (0 to 18,446,744,073,709,551,615)."""

    pass


class u128(int):
    """Rust u128: unsigned 128-bit integer."""

    pass


class usize(int):
    """Rust usize: pointer-sized unsigned integer."""

    pass


class i8(int):
    """Rust i8: signed 8-bit integer (-128 to 127)."""

    pass


class i16(int):
    """Rust i16: signed 16-bit integer (-32,768 to 32,767)."""

    pass


class i32(int):
    """Rust i32: signed 32-bit integer (-2,147,483,648 to 2,147,483,647)."""

    pass


class i64(int):
    """Rust i64: signed 64-bit integer (default for Python int)."""

    pass


class i128(int):
    """Rust i128: signed 128-bit integer."""

    pass


class isize(int):
    """Rust isize: pointer-sized signed integer."""

    pass


# =============================================================================
# Rust Float Types
# =============================================================================


class f32(float):
    """Rust f32: 32-bit floating point."""

    pass


class f64(float):
    """Rust f64: 64-bit floating point (default for Python float)."""

    pass


# =============================================================================
# Result Type
# =============================================================================


class Result(Generic[T, E]):
    """Rust Result<T, E> type for error handling.

    Use Ok() and Err() to construct Result values.

    Example:
        def divide(a: int, b: int) -> Result[int, str]:
            if b == 0:
                return Err("division by zero")
            return Ok(a // b)
    """

    @staticmethod
    def unwrap(result: "Result[T, E]") -> T:
        """Unwrap the Result, panicking on Err. Transpiles to: result.unwrap()"""
        ...

    @staticmethod
    def expect(result: "Result[T, E]", msg: str) -> T:
        """Unwrap with custom panic message. Transpiles to: result.expect(msg)"""
        ...

    @staticmethod
    def unwrap_or(result: "Result[T, E]", default: T) -> T:
        """Unwrap or return default. Transpiles to: result.unwrap_or(default)"""
        ...

    @staticmethod
    def unwrap_err(result: "Result[T, E]") -> E:
        """Unwrap the Err variant. Transpiles to: result.unwrap_err()"""
        ...

    @staticmethod
    def is_ok(result: "Result[T, E]") -> bool:
        """Check if Result is Ok. Transpiles to: result.is_ok()"""
        ...

    @staticmethod
    def is_err(result: "Result[T, E]") -> bool:
        """Check if Result is Err. Transpiles to: result.is_err()"""
        ...


class Ok(Generic[T]):
    """Ok variant of Result. Transpiles to: Ok(value)"""

    def __init__(self, value: T) -> None:
        self.value = value


class Err(Generic[E]):
    """Err variant of Result. Transpiles to: Err(error)"""

    def __init__(self, error: E) -> None:
        self.error = error


# =============================================================================
# Option Type
# =============================================================================


class Option(Generic[T]):
    """Rust Option<T> type for optional values.

    In Python, use `T | None` or `Optional[T]` which transpiles to `Option<T>`.
    This class provides explicit methods for Option manipulation.

    Example:
        value: str | None = get_value()
        if Option.is_some(value):
            print(Option.unwrap(value))
    """

    @staticmethod
    def unwrap(option: "Option[T] | T | None") -> T:
        """Unwrap the Option, panicking on None. Transpiles to: option.unwrap()"""
        ...

    @staticmethod
    def expect(option: "Option[T] | T | None", msg: str) -> T:
        """Unwrap with custom panic message. Transpiles to: option.expect(msg)"""
        ...

    @staticmethod
    def unwrap_or(option: "Option[T] | T | None", default: T) -> T:
        """Unwrap or return default. Transpiles to: option.unwrap_or(default)"""
        ...

    @staticmethod
    def is_some(option: "Option[T] | T | None") -> bool:
        """Check if Option has a value. Transpiles to: option.is_some()"""
        ...

    @staticmethod
    def is_none(option: "Option[T] | T | None") -> bool:
        """Check if Option is None. Transpiles to: option.is_none()"""
        ...


class Some(Generic[T]):
    """Some variant of Option. Transpiles to: Some(value)"""

    def __init__(self, value: T) -> None:
        self.value = value


# For None, use Python's built-in None which transpiles to Rust's None


# =============================================================================
# All exported types
# =============================================================================

__all__ = [
    # Integer types
    "u8",
    "u16",
    "u32",
    "u64",
    "u128",
    "usize",
    "i8",
    "i16",
    "i32",
    "i64",
    "i128",
    "isize",
    # Float types
    "f32",
    "f64",
    # Result type
    "Result",
    "Ok",
    "Err",
    # Option type
    "Option",
    "Some",
]
