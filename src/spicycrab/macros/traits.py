"""Derive trait markers for Rust #[derive(...)] attribute.

These are marker classes that represent Rust derive traits.
They don't do anything at runtime but are used by the transpiler
to generate the appropriate #[derive(...)] attributes.

Usage:
    @rust(derive=[Debug, Clone, PartialEq])
    class Point:
        x: int
        y: int

    # Transpiles to:
    # #[derive(Debug, Clone, PartialEq)]
    # struct Point { x: i64, y: i64 }
"""

from __future__ import annotations


class DeriveTrait:
    """Base class for all derive trait markers."""

    # The Rust trait name (e.g., "Debug", "Clone")
    rust_name: str = ""

    # Optional crate path (e.g., "serde::Serialize")
    crate_path: str | None = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Default rust_name to class name if not set
        if not cls.rust_name:
            cls.rust_name = cls.__name__

    def __repr__(self) -> str:
        if self.crate_path:
            return f"{self.crate_path}::{self.rust_name}"
        return self.rust_name


# =============================================================================
# Standard Library Derive Traits
# =============================================================================


class Debug(DeriveTrait):
    """#[derive(Debug)] - Enable {:?} formatting."""

    rust_name = "Debug"


class Clone(DeriveTrait):
    """#[derive(Clone)] - Enable .clone() method."""

    rust_name = "Clone"


class Copy(DeriveTrait):
    """#[derive(Copy)] - Enable implicit copying (requires Clone)."""

    rust_name = "Copy"


class Default(DeriveTrait):
    """#[derive(Default)] - Enable Default::default()."""

    rust_name = "Default"


class PartialEq(DeriveTrait):
    """#[derive(PartialEq)] - Enable == and != operators."""

    rust_name = "PartialEq"


class Eq(DeriveTrait):
    """#[derive(Eq)] - Mark as having full equivalence (requires PartialEq)."""

    rust_name = "Eq"


class PartialOrd(DeriveTrait):
    """#[derive(PartialOrd)] - Enable <, >, <=, >= operators."""

    rust_name = "PartialOrd"


class Ord(DeriveTrait):
    """#[derive(Ord)] - Enable total ordering (requires PartialOrd + Eq)."""

    rust_name = "Ord"


class Hash(DeriveTrait):
    """#[derive(Hash)] - Enable hashing for use in HashMap/HashSet keys."""

    rust_name = "Hash"


# =============================================================================
# Serde Derive Traits
# =============================================================================


class Serialize(DeriveTrait):
    """#[derive(Serialize)] - Enable serialization via serde."""

    rust_name = "Serialize"
    crate_path = "serde"


class Deserialize(DeriveTrait):
    """#[derive(Deserialize)] - Enable deserialization via serde."""

    rust_name = "Deserialize"
    crate_path = "serde"


# =============================================================================
# Convenience groupings
# =============================================================================

# Common trait combinations
STANDARD_DERIVES: list[type[DeriveTrait]] = [Debug, Clone, PartialEq]
VALUE_TYPE_DERIVES: list[type[DeriveTrait]] = [Debug, Clone, Copy, PartialEq, Eq, Hash]
SERDE_DERIVES: list[type[DeriveTrait]] = [Serialize, Deserialize]
