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

from spicycrab.macros.decorator import rust, derive
from spicycrab.macros.traits import (
    # Standard derive traits
    Debug,
    Clone,
    Copy,
    Default,
    PartialEq,
    Eq,
    PartialOrd,
    Ord,
    Hash,
    # Serde derives
    Serialize,
    Deserialize,
)
from spicycrab.macros.attributes import (
    # Representation
    Repr,
    # Common attributes
    Allow,
    Deny,
    Warn,
    Cfg,
    CfgAttr,
    # Function attributes
    Inline,
    Cold,
    MustUse,
    # Custom attribute builder
    attr,
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
