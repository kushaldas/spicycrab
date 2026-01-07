"""Option type for Rust-like optional values.

This is a type stub for transpilation - provides the full Rust Option<T> API.
Option[T] can be Some(value) or None.

In Python, Option[T] is essentially T | None, but with explicit Some() wrapper
for pattern matching support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from spicycrab.types.result import Result

# TypeVars for static method signatures (class params only work for instance methods)
T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


class Some[T]:
    """Wrapper for the Some variant of Option.

    Used for pattern matching:
        match opt:
            case Some(x):
                print(x)
            case None:
                print("nothing")
    """

    __match_args__ = ("value",)

    def __init__(self, value: T) -> None:
        self._value = value

    @property
    def value(self) -> T:
        """Get the wrapped value."""
        return self._value

    def __repr__(self) -> str:
        return f"Some({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Some):
            return self._value == other._value
        return False

    def __hash__(self) -> int:
        return hash(("Some", self._value))


class Option[T]:
    """Rust-like Option type representing an optional value.

    Option[T] can be:
    - Some(T): Contains a value
    - None: Contains nothing

    This is a type stub for transpilation. In actual Python usage,
    you would use Some(value) or None directly.

    Example:
        def find_user(id: int) -> Option[User]:
            if id in users:
                return Some(users[id])
            return None

        # Pattern matching
        match find_user(42):
            case Some(user):
                print(user.name)
            case None:
                print("not found")
    """

    # Note: Option itself is not instantiated directly.
    # Use Some(value) or None.

    # =========================================================================
    # Querying the contained value
    # =========================================================================

    @staticmethod
    def is_some(opt: Option[T] | Some[T] | None) -> bool:
        """Return True if the option is Some."""
        return opt is not None and opt is not None

    @staticmethod
    def is_some_and(opt: Option[T] | Some[T] | None, f: Callable[[T], bool]) -> bool:
        """Return True if Some and the predicate returns True."""
        if isinstance(opt, Some):
            return f(opt.value)
        return False

    @staticmethod
    def is_none(opt: Option[T] | Some[T] | None) -> bool:
        """Return True if the option is None."""
        return opt is None

    # =========================================================================
    # Extracting the contained value
    # =========================================================================

    @staticmethod
    def expect(opt: Option[T] | Some[T] | None, msg: str) -> T:
        """Return the contained value or panic with message."""
        if isinstance(opt, Some):
            return opt.value
        raise RuntimeError(msg)

    @staticmethod
    def unwrap(opt: Option[T] | Some[T] | None) -> T:
        """Return the contained value or panic."""
        if isinstance(opt, Some):
            return opt.value
        raise RuntimeError("called unwrap on None")

    @staticmethod
    def unwrap_or(opt: Option[T] | Some[T] | None, default: T) -> T:
        """Return the contained value or a default."""
        if isinstance(opt, Some):
            return opt.value
        return default

    @staticmethod
    def unwrap_or_else(opt: Option[T] | Some[T] | None, f: Callable[[], T]) -> T:
        """Return the contained value or compute from closure."""
        if isinstance(opt, Some):
            return opt.value
        return f()

    @staticmethod
    def unwrap_or_default(opt: Option[T] | Some[T] | None) -> T:
        """Return the contained value or default for type.

        Note: In Python, we can't get the default for a generic type,
        so this raises if None. In Rust, this requires T: Default.
        """
        if isinstance(opt, Some):
            return opt.value
        raise RuntimeError("called unwrap_or_default on None (no Default impl)")

    # =========================================================================
    # Transforming contained values
    # =========================================================================

    @staticmethod
    def map(opt: Option[T] | Some[T] | None, f: Callable[[T], U]) -> Option[U] | Some[U] | None:
        """Map Option<T> to Option<U> by applying f to contained value."""
        if isinstance(opt, Some):
            return Some(f(opt.value))
        return None

    @staticmethod
    def inspect(opt: Option[T] | Some[T] | None, f: Callable[[T], None]) -> Option[T] | Some[T] | None:
        """Call f on contained value (if Some), return original Option."""
        if isinstance(opt, Some):
            f(opt.value)
        return opt

    @staticmethod
    def map_or(opt: Option[T] | Some[T] | None, default: U, f: Callable[[T], U]) -> U:
        """Apply f to contained value, or return default."""
        if isinstance(opt, Some):
            return f(opt.value)
        return default

    @staticmethod
    def map_or_else(
        opt: Option[T] | Some[T] | None,
        default: Callable[[], U],
        f: Callable[[T], U],
    ) -> U:
        """Apply f to contained value, or compute default."""
        if isinstance(opt, Some):
            return f(opt.value)
        return default()

    # =========================================================================
    # Boolean operations
    # =========================================================================

    @staticmethod
    def and_(opt: Option[T] | Some[T] | None, optb: Option[U] | Some[U] | None) -> Option[U] | Some[U] | None:
        """Return None if opt is None, otherwise return optb."""
        if isinstance(opt, Some):
            return optb
        return None

    @staticmethod
    def and_then(
        opt: Option[T] | Some[T] | None,
        f: Callable[[T], Option[U] | Some[U] | None],
    ) -> Option[U] | Some[U] | None:
        """Return None if None, otherwise call f with value (flatMap)."""
        if isinstance(opt, Some):
            return f(opt.value)
        return None

    @staticmethod
    def filter(
        opt: Option[T] | Some[T] | None,
        predicate: Callable[[T], bool],
    ) -> Option[T] | Some[T] | None:
        """Return None if None, or if predicate returns False."""
        if isinstance(opt, Some) and predicate(opt.value):
            return opt
        return None

    @staticmethod
    def or_(opt: Option[T] | Some[T] | None, optb: Option[T] | Some[T] | None) -> Option[T] | Some[T] | None:
        """Return opt if Some, otherwise return optb."""
        if isinstance(opt, Some):
            return opt
        return optb

    @staticmethod
    def or_else(
        opt: Option[T] | Some[T] | None,
        f: Callable[[], Option[T] | Some[T] | None],
    ) -> Option[T] | Some[T] | None:
        """Return opt if Some, otherwise call f."""
        if isinstance(opt, Some):
            return opt
        return f()

    @staticmethod
    def xor(
        opt: Option[T] | Some[T] | None,
        optb: Option[T] | Some[T] | None,
    ) -> Option[T] | Some[T] | None:
        """Return Some if exactly one is Some, otherwise None."""
        a_some = isinstance(opt, Some)
        b_some = isinstance(optb, Some)
        if a_some and not b_some:
            return opt
        if b_some and not a_some:
            return optb
        return None

    # =========================================================================
    # Entry-like operations
    # =========================================================================

    @staticmethod
    def insert(opt: list, value: T) -> T:
        """Insert value, returning mutable reference.

        Note: Python doesn't have mutable references, so this is a stub.
        In Rust: fn insert(&mut self, value: T) -> &mut T
        """
        opt.clear()
        opt.append(Some(value))
        return value

    @staticmethod
    def get_or_insert(opt: list, value: T) -> T:
        """Insert value if None, return contained value.

        Note: Uses list as mutable container for Python compatibility.
        """
        if opt and isinstance(opt[0], Some):
            return opt[0].value
        opt.clear()
        opt.append(Some(value))
        return value

    @staticmethod
    def get_or_insert_with(opt: list, f: Callable[[], T]) -> T:
        """Insert computed value if None, return contained value."""
        if opt and isinstance(opt[0], Some):
            return opt[0].value
        value = f()
        opt.clear()
        opt.append(Some(value))
        return value

    # =========================================================================
    # Misc operations
    # =========================================================================

    @staticmethod
    def take(opt: list) -> Option[T] | Some[T] | None:
        """Take the value out, leaving None.

        Note: Uses list as mutable container for Python compatibility.
        """
        if opt and isinstance(opt[0], Some):
            value = opt[0]
            opt[0] = None
            return value
        return None

    @staticmethod
    def replace(opt: list, value: T) -> Option[T] | Some[T] | None:
        """Replace the value, returning the old value."""
        old = opt[0] if opt else None
        if opt:
            opt[0] = Some(value)
        else:
            opt.append(Some(value))
        return old

    @staticmethod
    def zip(
        opt: Option[T] | Some[T] | None,
        other: Option[U] | Some[U] | None,
    ) -> Option[tuple[T, U]] | Some[tuple[T, U]] | None:
        """Zip two Options into Option of tuple."""
        if isinstance(opt, Some) and isinstance(other, Some):
            return Some((opt.value, other.value))
        return None

    @staticmethod
    def zip_with(
        opt: Option[T] | Some[T] | None,
        other: Option[U] | Some[U] | None,
        f: Callable[[T, U], object],
    ) -> Option[object] | Some[object] | None:
        """Zip two Options with a function."""
        if isinstance(opt, Some) and isinstance(other, Some):
            return Some(f(opt.value, other.value))
        return None

    @staticmethod
    def unzip(
        opt: Option[tuple[T, U]] | Some[tuple[T, U]] | None,
    ) -> tuple[Option[T] | Some[T] | None, Option[U] | Some[U] | None]:
        """Unzip Option of tuple into tuple of Options."""
        if isinstance(opt, Some):
            a, b = opt.value
            return (Some(a), Some(b))
        return (None, None)

    # =========================================================================
    # Conversion to Result
    # =========================================================================

    @staticmethod
    def ok_or(opt: Option[T] | Some[T] | None, err: E) -> Result[T, E]:
        """Transform Option to Result, mapping Some(v) to Ok(v) and None to Err(err)."""
        from spicycrab.types.result import Err, Ok

        if isinstance(opt, Some):
            return Ok(opt.value)
        return Err(err)

    @staticmethod
    def ok_or_else(opt: Option[T] | Some[T] | None, err: Callable[[], E]) -> Result[T, E]:
        """Transform Option to Result, computing error lazily."""
        from spicycrab.types.result import Err, Ok

        if isinstance(opt, Some):
            return Ok(opt.value)
        return Err(err())

    @staticmethod
    def transpose(
        opt: Option[Result[T, E]] | Some[Result[T, E]] | None,
    ) -> Result[Option[T] | Some[T] | None, E]:
        """Transpose Option of Result to Result of Option."""
        from spicycrab.types.result import Err, Ok

        if opt is None:
            return Ok(None)
        if isinstance(opt, Some):
            inner = opt.value
            if isinstance(inner, Ok):
                return Ok(Some(inner.value))
            if isinstance(inner, Err):
                return inner
        return Ok(None)

    # =========================================================================
    # Iterator operations
    # =========================================================================

    @staticmethod
    def iter(opt: Option[T] | Some[T] | None) -> list[T]:
        """Return iterator over the contained value (0 or 1 element)."""
        if isinstance(opt, Some):
            return [opt.value]
        return []

    @staticmethod
    def flatten(
        opt: Option[Option[T]] | Some[Option[T] | Some[T] | None] | None,
    ) -> Option[T] | Some[T] | None:
        """Flatten nested Option."""
        if isinstance(opt, Some):
            return opt.value
        return None
