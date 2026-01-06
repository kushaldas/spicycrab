"""Result type for Rust-like error handling.

This is a type stub for transpilation - provides the full Rust Result<T, E> API.
Result[T, E] can be Ok(value) or Err(error).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable
    from spicycrab.types.option import Option, Some

from spicycrab.types.error import Error

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E", bound=Error)
F = TypeVar("F", bound=Error)


class Ok(Generic[T]):
    """Wrapper for the Ok variant of Result.

    Used for pattern matching:
        match result:
            case Ok(value):
                print(value)
            case Err(e):
                print(f"error: {e}")
    """

    __match_args__ = ("value",)

    def __init__(self, value: T) -> None:
        self._value = value

    @property
    def value(self) -> T:
        """Get the wrapped value."""
        return self._value

    def __repr__(self) -> str:
        return f"Ok({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Ok):
            return self._value == other._value
        return False

    def __hash__(self) -> int:
        return hash(("Ok", self._value))


class Err(Generic[E]):
    """Wrapper for the Err variant of Result.

    Used for pattern matching:
        match result:
            case Ok(value):
                print(value)
            case Err(e):
                print(f"error: {e}")
    """

    __match_args__ = ("error",)

    def __init__(self, error: E) -> None:
        self._error = error

    @property
    def error(self) -> E:
        """Get the wrapped error."""
        return self._error

    def __repr__(self) -> str:
        return f"Err({self._error!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Err):
            return self._error == other._error
        return False

    def __hash__(self) -> int:
        return hash(("Err", self._error))


class Result(Generic[T, E]):
    """Rust-like Result type for error handling.

    Result[T, E] can be:
    - Ok(T): Contains a success value
    - Err(E): Contains an error value

    This is a type stub for transpilation. In actual Python usage,
    you would use Ok(value) or Err(error) directly.

    Example:
        def parse_int(s: str) -> Result[int, Error]:
            try:
                return Ok(int(s))
            except ValueError as e:
                return Err(Error(str(e)))

        # Pattern matching
        match parse_int("42"):
            case Ok(n):
                print(f"parsed: {n}")
            case Err(e):
                print(f"error: {e}")
    """

    # Note: Result itself is not instantiated directly.
    # Use Ok(value) or Err(error).

    # =========================================================================
    # Querying the contained value
    # =========================================================================

    @staticmethod
    def is_ok(res: Result[T, E] | Ok[T] | Err[E]) -> bool:
        """Return True if the result is Ok."""
        return isinstance(res, Ok)

    @staticmethod
    def is_ok_and(res: Result[T, E] | Ok[T] | Err[E], f: Callable[[T], bool]) -> bool:
        """Return True if Ok and the predicate returns True."""
        if isinstance(res, Ok):
            return f(res.value)
        return False

    @staticmethod
    def is_err(res: Result[T, E] | Ok[T] | Err[E]) -> bool:
        """Return True if the result is Err."""
        return isinstance(res, Err)

    @staticmethod
    def is_err_and(res: Result[T, E] | Ok[T] | Err[E], f: Callable[[E], bool]) -> bool:
        """Return True if Err and the predicate returns True."""
        if isinstance(res, Err):
            return f(res.error)
        return False

    # =========================================================================
    # Extracting contained values
    # =========================================================================

    @staticmethod
    def ok(res: Result[T, E] | Ok[T] | Err[E]) -> Option[T] | Some[T] | None:
        """Convert to Option, discarding error."""
        from spicycrab.types.option import Some
        if isinstance(res, Ok):
            return Some(res.value)
        return None

    @staticmethod
    def err(res: Result[T, E] | Ok[T] | Err[E]) -> Option[E] | Some[E] | None:
        """Convert to Option of error, discarding success."""
        from spicycrab.types.option import Some
        if isinstance(res, Err):
            return Some(res.error)
        return None

    @staticmethod
    def expect(res: Result[T, E] | Ok[T] | Err[E], msg: str) -> T:
        """Return the contained Ok value or panic with message."""
        if isinstance(res, Ok):
            return res.value
        raise RuntimeError(f"{msg}: {res}")

    @staticmethod
    def expect_err(res: Result[T, E] | Ok[T] | Err[E], msg: str) -> E:
        """Return the contained Err value or panic with message."""
        if isinstance(res, Err):
            return res.error
        raise RuntimeError(f"{msg}: {res}")

    @staticmethod
    def unwrap(res: Result[T, E] | Ok[T] | Err[E]) -> T:
        """Return the contained Ok value or panic."""
        if isinstance(res, Ok):
            return res.value
        raise RuntimeError(f"called unwrap on Err: {res}")

    @staticmethod
    def unwrap_err(res: Result[T, E] | Ok[T] | Err[E]) -> E:
        """Return the contained Err value or panic."""
        if isinstance(res, Err):
            return res.error
        raise RuntimeError(f"called unwrap_err on Ok: {res}")

    @staticmethod
    def unwrap_or(res: Result[T, E] | Ok[T] | Err[E], default: T) -> T:
        """Return the contained Ok value or a default."""
        if isinstance(res, Ok):
            return res.value
        return default

    @staticmethod
    def unwrap_or_else(res: Result[T, E] | Ok[T] | Err[E], f: Callable[[E], T]) -> T:
        """Return the contained Ok value or compute from error."""
        if isinstance(res, Ok):
            return res.value
        if isinstance(res, Err):
            return f(res.error)
        raise RuntimeError("invalid Result state")

    @staticmethod
    def unwrap_or_default(res: Result[T, E] | Ok[T] | Err[E]) -> T:
        """Return the contained Ok value or default for type.

        Note: In Python, we can't get the default for a generic type.
        In Rust, this requires T: Default.
        """
        if isinstance(res, Ok):
            return res.value
        raise RuntimeError("called unwrap_or_default on Err (no Default impl)")

    # =========================================================================
    # Transforming contained values
    # =========================================================================

    @staticmethod
    def map(res: Result[T, E] | Ok[T] | Err[E], f: Callable[[T], U]) -> Result[U, E] | Ok[U] | Err[E]:
        """Map Result<T, E> to Result<U, E> by applying f to Ok value."""
        if isinstance(res, Ok):
            return Ok(f(res.value))
        return res  # type: ignore

    @staticmethod
    def map_or(res: Result[T, E] | Ok[T] | Err[E], default: U, f: Callable[[T], U]) -> U:
        """Apply f to Ok value, or return default."""
        if isinstance(res, Ok):
            return f(res.value)
        return default

    @staticmethod
    def map_or_else(
        res: Result[T, E] | Ok[T] | Err[E],
        default: Callable[[E], U],
        f: Callable[[T], U],
    ) -> U:
        """Apply f to Ok value, or compute default from error."""
        if isinstance(res, Ok):
            return f(res.value)
        if isinstance(res, Err):
            return default(res.error)
        raise RuntimeError("invalid Result state")

    @staticmethod
    def map_err(res: Result[T, E] | Ok[T] | Err[E], f: Callable[[E], F]) -> Result[T, F] | Ok[T] | Err[F]:
        """Map Result<T, E> to Result<T, F> by applying f to Err value."""
        if isinstance(res, Err):
            return Err(f(res.error))
        return res  # type: ignore

    @staticmethod
    def inspect(res: Result[T, E] | Ok[T] | Err[E], f: Callable[[T], None]) -> Result[T, E] | Ok[T] | Err[E]:
        """Call f on Ok value (if Ok), return original Result."""
        if isinstance(res, Ok):
            f(res.value)
        return res

    @staticmethod
    def inspect_err(res: Result[T, E] | Ok[T] | Err[E], f: Callable[[E], None]) -> Result[T, E] | Ok[T] | Err[E]:
        """Call f on Err value (if Err), return original Result."""
        if isinstance(res, Err):
            f(res.error)
        return res

    # =========================================================================
    # Boolean operations
    # =========================================================================

    @staticmethod
    def and_(res: Result[T, E] | Ok[T] | Err[E], resb: Result[U, E] | Ok[U] | Err[E]) -> Result[U, E] | Ok[U] | Err[E]:
        """Return resb if res is Ok, otherwise return the Err of res."""
        if isinstance(res, Ok):
            return resb
        return res  # type: ignore

    @staticmethod
    def and_then(
        res: Result[T, E] | Ok[T] | Err[E],
        f: Callable[[T], Result[U, E] | Ok[U] | Err[E]],
    ) -> Result[U, E] | Ok[U] | Err[E]:
        """Return Err if Err, otherwise call f with Ok value (flatMap)."""
        if isinstance(res, Ok):
            return f(res.value)
        return res  # type: ignore

    @staticmethod
    def or_(res: Result[T, E] | Ok[T] | Err[E], resb: Result[T, F] | Ok[T] | Err[F]) -> Result[T, F] | Ok[T] | Err[F]:
        """Return res if Ok, otherwise return resb."""
        if isinstance(res, Ok):
            return res  # type: ignore
        return resb

    @staticmethod
    def or_else(
        res: Result[T, E] | Ok[T] | Err[E],
        f: Callable[[E], Result[T, F] | Ok[T] | Err[F]],
    ) -> Result[T, F] | Ok[T] | Err[F]:
        """Return res if Ok, otherwise call f with error."""
        if isinstance(res, Ok):
            return res  # type: ignore
        if isinstance(res, Err):
            return f(res.error)
        raise RuntimeError("invalid Result state")

    # =========================================================================
    # Conversion to Option
    # =========================================================================

    @staticmethod
    def transpose(
        res: Result[Option[T] | Some[T] | None, E] | Ok[Option[T] | Some[T] | None] | Err[E],
    ) -> Option[Result[T, E]] | Some[Result[T, E]] | None:
        """Transpose Result of Option to Option of Result."""
        from spicycrab.types.option import Some
        if isinstance(res, Ok):
            inner = res.value
            if inner is None:
                return None
            if isinstance(inner, Some):
                return Some(Ok(inner.value))
            return None
        if isinstance(res, Err):
            return Some(res)
        return None

    # =========================================================================
    # Misc operations
    # =========================================================================

    @staticmethod
    def flatten(
        res: Result[Result[T, E] | Ok[T] | Err[E], E] | Ok[Result[T, E] | Ok[T] | Err[E]] | Err[E],
    ) -> Result[T, E] | Ok[T] | Err[E]:
        """Flatten nested Result."""
        if isinstance(res, Ok):
            return res.value
        return res  # type: ignore

    @staticmethod
    def iter(res: Result[T, E] | Ok[T] | Err[E]) -> list[T]:
        """Return iterator over the Ok value (0 or 1 element)."""
        if isinstance(res, Ok):
            return [res.value]
        return []

    @staticmethod
    def iter_err(res: Result[T, E] | Ok[T] | Err[E]) -> list[E]:
        """Return iterator over the Err value (0 or 1 element)."""
        if isinstance(res, Err):
            return [res.error]
        return []

    # =========================================================================
    # Copying/Cloning (stubs for transpilation)
    # =========================================================================

    @staticmethod
    def copied(res: Result[T, E] | Ok[T] | Err[E]) -> Result[T, E] | Ok[T] | Err[E]:
        """Copy the value (stub - in Rust, requires T: Copy)."""
        return res

    @staticmethod
    def cloned(res: Result[T, E] | Ok[T] | Err[E]) -> Result[T, E] | Ok[T] | Err[E]:
        """Clone the value (stub - in Rust, requires T: Clone)."""
        return res
