"""Rust attribute markers for spicycrab transpilation.

This module provides markers for Rust attributes like #[repr(...)],
#[allow(...)], #[inline], #[must_use], and custom attributes.

Usage:
    @rust(repr="C", allow=["dead_code"])
    class FFIStruct:
        data: int

    @rust(inline=True, must_use="check the result")
    def important_calc(x: int) -> int:
        return x * 2

    # Custom attributes
    @rust(custom=[attr("tokio::main"), attr("test")])
    async def my_test() -> None:
        pass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# Base Attribute Classes
# =============================================================================


@dataclass
class RustAttribute:
    """Base class for Rust attributes.

    Represents a Rust attribute like #[name] or #[name(args)].
    """

    name: str
    args: list[str] | dict[str, Any] | str | None = None

    def to_rust(self) -> str:
        """Convert to Rust attribute syntax."""
        if self.args is None:
            return f"#[{self.name}]"

        if isinstance(self.args, str):
            return f'#[{self.name}({self.args})]'

        if isinstance(self.args, list):
            args_str = ", ".join(str(a) for a in self.args)
            return f"#[{self.name}({args_str})]"

        if isinstance(self.args, dict):
            args_str = ", ".join(f'{k} = "{v}"' if isinstance(v, str) else f"{k} = {v}"
                                  for k, v in self.args.items())
            return f"#[{self.name}({args_str})]"

        return f"#[{self.name}]"


def attr(name: str, *args: Any, **kwargs: Any) -> RustAttribute:
    """Create a custom Rust attribute.

    Usage:
        attr("tokio::main")           -> #[tokio::main]
        attr("test")                  -> #[test]
        attr("cfg", "feature = \"foo\"") -> #[cfg(feature = "foo")]
        attr("serde", rename="ID")    -> #[serde(rename = "ID")]
    """
    if kwargs:
        return RustAttribute(name=name, args=kwargs)
    if args:
        if len(args) == 1 and isinstance(args[0], str):
            return RustAttribute(name=name, args=args[0])
        return RustAttribute(name=name, args=list(args))
    return RustAttribute(name=name, args=None)


# =============================================================================
# Representation Attributes
# =============================================================================


@dataclass
class Repr(RustAttribute):
    """#[repr(...)] attribute for memory layout control.

    Usage:
        @rust(repr="C")        -> #[repr(C)]
        @rust(repr="packed")   -> #[repr(packed)]
        @rust(repr="u8")       -> #[repr(u8)]  (for enums)
    """

    name: str = field(default="repr", init=False)
    repr_type: str = "Rust"

    def __post_init__(self) -> None:
        self.args = self.repr_type


# Common repr values
REPR_C = Repr(repr_type="C")
REPR_PACKED = Repr(repr_type="packed")
REPR_TRANSPARENT = Repr(repr_type="transparent")


# =============================================================================
# Lint Attributes
# =============================================================================


@dataclass
class LintAttribute(RustAttribute):
    """Base for lint control attributes (#[allow], #[deny], #[warn])."""

    lints: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.args = self.lints


@dataclass
class Allow(LintAttribute):
    """#[allow(...)] - Suppress warnings for specified lints.

    Usage:
        @rust(allow=["dead_code", "unused_variables"])
    """

    name: str = field(default="allow", init=False)


@dataclass
class Deny(LintAttribute):
    """#[deny(...)] - Treat specified lints as errors.

    Usage:
        @rust(deny=["unsafe_code"])
    """

    name: str = field(default="deny", init=False)


@dataclass
class Warn(LintAttribute):
    """#[warn(...)] - Emit warnings for specified lints.

    Usage:
        @rust(warn=["missing_docs"])
    """

    name: str = field(default="warn", init=False)


# =============================================================================
# Conditional Compilation
# =============================================================================


@dataclass
class Cfg(RustAttribute):
    """#[cfg(...)] - Conditional compilation.

    Usage:
        @rust(cfg="feature = \"async\"")
        @rust(cfg="target_os = \"linux\"")
    """

    name: str = field(default="cfg", init=False)
    condition: str = ""

    def __post_init__(self) -> None:
        self.args = self.condition


@dataclass
class CfgAttr(RustAttribute):
    """#[cfg_attr(...)] - Conditional attribute application.

    Usage:
        @rust(cfg_attr=("feature = \"serde\"", "derive(Serialize, Deserialize)"))
    """

    name: str = field(default="cfg_attr", init=False)
    condition: str = ""
    attributes: str = ""

    def __post_init__(self) -> None:
        self.args = f'{self.condition}, {self.attributes}'


# =============================================================================
# Function Attributes
# =============================================================================


@dataclass
class Inline(RustAttribute):
    """#[inline] or #[inline(always)] - Hint to inline function.

    Usage:
        @rust(inline=True)           -> #[inline]
        @rust(inline="always")       -> #[inline(always)]
        @rust(inline="never")        -> #[inline(never)]
    """

    name: str = field(default="inline", init=False)
    mode: str | bool = True

    def __post_init__(self) -> None:
        if self.mode is True:
            self.args = None
        elif isinstance(self.mode, str):
            self.args = self.mode


@dataclass
class Cold(RustAttribute):
    """#[cold] - Mark function as unlikely to be called.

    Usage:
        @rust(cold=True)
    """

    name: str = field(default="cold", init=False)

    def __post_init__(self) -> None:
        self.args = None


@dataclass
class MustUse(RustAttribute):
    """#[must_use] - Warn if return value is unused.

    Usage:
        @rust(must_use=True)                    -> #[must_use]
        @rust(must_use="check the result")      -> #[must_use = "check the result"]
    """

    name: str = field(default="must_use", init=False)
    message: str | bool = True

    def __post_init__(self) -> None:
        if self.message is True:
            self.args = None
        elif isinstance(self.message, str):
            self.args = f'"{self.message}"'


# =============================================================================
# Other Common Attributes
# =============================================================================


@dataclass
class Doc(RustAttribute):
    """#[doc = "..."] - Documentation attribute.

    Usually generated from docstrings automatically.
    """

    name: str = field(default="doc", init=False)
    content: str = ""

    def __post_init__(self) -> None:
        self.args = f'"{self.content}"'


@dataclass
class Deprecated(RustAttribute):
    """#[deprecated] - Mark as deprecated.

    Usage:
        @rust(deprecated=True)
        @rust(deprecated={"since": "1.0", "note": "use new_func instead"})
    """

    name: str = field(default="deprecated", init=False)
    since: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if self.since or self.note:
            parts = []
            if self.since:
                parts.append(f'since = "{self.since}"')
            if self.note:
                parts.append(f'note = "{self.note}"')
            self.args = ", ".join(parts)
        else:
            self.args = None


# =============================================================================
# Serde Attributes (for field/variant level)
# =============================================================================


@dataclass
class SerdeAttr(RustAttribute):
    """#[serde(...)] - Serde field/struct attributes.

    Usage:
        @rust(serde={"rename_all": "camelCase"})
        @rust(serde={"default": True, "skip_serializing_if": "Option::is_none"})

    For field-level:
        x: int = field(metadata={"serde": {"rename": "X", "default": True}})
    """

    name: str = field(default="serde", init=False)
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.options:
            parts = []
            for k, v in self.options.items():
                if v is True:
                    parts.append(k)
                elif isinstance(v, str):
                    parts.append(f'{k} = "{v}"')
                else:
                    parts.append(f"{k} = {v}")
            self.args = ", ".join(parts)
        else:
            self.args = None
