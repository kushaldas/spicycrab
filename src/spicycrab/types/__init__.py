"""Rust-like types for spicycrab transpilation.

These types are designed for transpilation to Rust, not for runtime use.
They provide full Rust Option/Result API signatures for type checking
and pattern matching support.

Usage:
    from spicycrab.types import Option, Some, Result, Ok, Err, Error

    def find_user(id: int) -> Option[User]:
        if id in users:
            return Some(users[id])
        return None

    def parse_int(s: str) -> Result[int, Error]:
        try:
            return Ok(int(s))
        except ValueError as e:
            return Err(Error(str(e)))
"""

from spicycrab.types.error import Error
from spicycrab.types.option import Option, Some
from spicycrab.types.result import Err, Ok, Result

__all__ = [
    "Error",
    "Option",
    "Some",
    "Result",
    "Ok",
    "Err",
]
