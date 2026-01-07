"""Rust attribute macros for spicycrab transpilation.

This module provides Python decorators that map to Rust attributes like
#[derive(...)], #[repr(...)], #[serde(...)], etc.

Usage:
    from spicycrab.macros import rust, derive, Debug, Clone, Serialize

    @rust(
        derive=[Debug, Clone, PartialEq],
        repr="C",
        serde={"rename_all": "camelCase"},
        allow=["dead_code"],
    )
    class Point:
        x: int
        y: int

    @rust(inline=True, must_use="returns important value")
    def calculate(x: int) -> int:
        return x * 2
"""

from spicycrab.macros.attributes import (
    # Common attributes
    Allow,
    Cfg,
    CfgAttr,
    Cold,
    Deny,
    # Function attributes
    Inline,
    MustUse,
    # Representation
    Repr,
    Warn,
    # Custom attribute builder
    attr,
)
from spicycrab.macros.decorator import derive, rust
from spicycrab.macros.traits import (
    Clone,
    Copy,
    # Standard derive traits
    Debug,
    Default,
    Deserialize,
    Eq,
    Hash,
    Ord,
    PartialEq,
    PartialOrd,
    # Serde derives
    Serialize,
)

__all__ = [
    # Main decorators
    "rust",
    "derive",
    # Derive traits
    "Debug",
    "Clone",
    "Copy",
    "Default",
    "PartialEq",
    "Eq",
    "PartialOrd",
    "Ord",
    "Hash",
    "Serialize",
    "Deserialize",
    # Attributes
    "Repr",
    "Allow",
    "Deny",
    "Warn",
    "Cfg",
    "CfgAttr",
    "Inline",
    "Cold",
    "MustUse",
    # Custom
    "attr",
]
