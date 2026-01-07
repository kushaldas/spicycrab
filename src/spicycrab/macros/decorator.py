"""The @rust() decorator for applying Rust attributes.

This decorator collects Rust attributes and stores them on the decorated
class or function for later use by the transpiler.

Usage:
    @rust(
        derive=[Debug, Clone, PartialEq],
        repr="C",
        serde={"rename_all": "camelCase"},
        allow=["dead_code"],
    )
    class Point:
        x: int
        y: int

    @rust(inline=True, must_use="check the result")
    def calculate(x: int) -> int:
        return x * 2

    # Custom attributes
    @rust(attrs=[attr("tokio::main")])
    async def main() -> None:
        pass
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from spicycrab.macros.attributes import RustAttribute
    from spicycrab.macros.traits import DeriveTrait

T = TypeVar("T", bound=type | Callable[..., Any])


@dataclass
class RustAttrs:
    """Container for Rust attributes attached to a Python class or function.

    This is stored on the decorated object as __rust_attrs__.
    The transpiler reads this to generate appropriate Rust attributes.
    """

    # #[derive(...)]
    derive: list[type[DeriveTrait] | str] = field(default_factory=list)

    # #[repr(...)]
    repr: str | None = None

    # #[serde(...)]
    serde: dict[str, Any] | None = None

    # Lint attributes: #[allow(...)], #[deny(...)], #[warn(...)]
    allow: list[str] = field(default_factory=list)
    deny: list[str] = field(default_factory=list)
    warn: list[str] = field(default_factory=list)

    # #[cfg(...)]
    cfg: str | None = None

    # #[cfg_attr(...)]
    cfg_attr: tuple[str, str] | None = None

    # Function attributes
    inline: bool | str | None = None  # True, "always", "never"
    cold: bool = False
    must_use: bool | str | None = None  # True or message string

    # #[deprecated(...)]
    deprecated: bool | dict[str, str] | None = None

    # #[doc = "..."] - usually from docstring
    doc: str | None = None

    # Custom attributes: list of RustAttribute or attr() results
    attrs: list[RustAttribute] = field(default_factory=list)

    def to_rust_attributes(self) -> list[str]:
        """Generate list of Rust attribute strings."""
        from spicycrab.macros.traits import DeriveTrait

        result: list[str] = []

        # Custom attributes first (for things like #[tokio::main] that must come first)
        for a in self.attrs:
            result.append(a.to_rust())

        # #[cfg(...)]
        if self.cfg:
            result.append(f"#[cfg({self.cfg})]")

        # #[cfg_attr(...)]
        if self.cfg_attr:
            cond, attrs = self.cfg_attr
            result.append(f"#[cfg_attr({cond}, {attrs})]")

        # #[derive(...)]
        if self.derive:
            derives = []
            for d in self.derive:
                if isinstance(d, str):
                    derives.append(d)
                elif isinstance(d, type) and issubclass(d, DeriveTrait):
                    derives.append(d.rust_name)
                elif hasattr(d, "rust_name"):
                    derives.append(d.rust_name)
                else:
                    derives.append(str(d))
            result.append(f"#[derive({', '.join(derives)})]")

        # #[repr(...)]
        if self.repr:
            result.append(f"#[repr({self.repr})]")

        # #[serde(...)]
        if self.serde:
            parts = []
            for k, v in self.serde.items():
                if v is True:
                    parts.append(k)
                elif isinstance(v, str):
                    parts.append(f'{k} = "{v}"')
                else:
                    parts.append(f"{k} = {v}")
            result.append(f"#[serde({', '.join(parts)})]")

        # Lint attributes
        if self.allow:
            result.append(f"#[allow({', '.join(self.allow)})]")
        if self.deny:
            result.append(f"#[deny({', '.join(self.deny)})]")
        if self.warn:
            result.append(f"#[warn({', '.join(self.warn)})]")

        # Function attributes
        if self.inline is not None:
            if self.inline is True:
                result.append("#[inline]")
            elif isinstance(self.inline, str):
                result.append(f"#[inline({self.inline})]")

        if self.cold:
            result.append("#[cold]")

        if self.must_use is not None:
            if self.must_use is True:
                result.append("#[must_use]")
            elif isinstance(self.must_use, str):
                result.append(f'#[must_use = "{self.must_use}"]')

        # #[deprecated(...)]
        if self.deprecated:
            if self.deprecated is True:
                result.append("#[deprecated]")
            elif isinstance(self.deprecated, dict):
                parts = []
                if "since" in self.deprecated:
                    parts.append(f'since = "{self.deprecated["since"]}"')
                if "note" in self.deprecated:
                    parts.append(f'note = "{self.deprecated["note"]}"')
                result.append(f"#[deprecated({', '.join(parts)})]")

        # #[doc = "..."]
        if self.doc:
            # Multi-line docs become multiple #[doc] attributes
            for line in self.doc.split("\n"):
                escaped = line.replace("\\", "\\\\").replace('"', '\\"')
                result.append(f'#[doc = "{escaped}"]')

        return result


def rust(
    *,
    derive: list[type[DeriveTrait] | str] | None = None,
    repr: str | None = None,
    serde: dict[str, Any] | None = None,
    allow: list[str] | None = None,
    deny: list[str] | None = None,
    warn: list[str] | None = None,
    cfg: str | None = None,
    cfg_attr: tuple[str, str] | None = None,
    inline: bool | str | None = None,
    cold: bool = False,
    must_use: bool | str | None = None,
    deprecated: bool | dict[str, str] | None = None,
    doc: str | None = None,
    attrs: list[RustAttribute] | None = None,
) -> Callable[[T], T]:
    """Decorator to attach Rust attributes to a Python class or function.

    All arguments are keyword-only for clarity.

    Args:
        derive: List of derive traits (e.g., [Debug, Clone, PartialEq])
        repr: Memory representation (e.g., "C", "packed", "transparent")
        serde: Serde container attributes (e.g., {"rename_all": "camelCase"})
        allow: Lints to allow (e.g., ["dead_code", "unused"])
        deny: Lints to deny (e.g., ["unsafe_code"])
        warn: Lints to warn (e.g., ["missing_docs"])
        cfg: Conditional compilation (e.g., "feature = \\"async\\"")
        cfg_attr: Conditional attribute (condition, attributes)
        inline: Inline hint (True, "always", "never")
        cold: Mark function as cold (unlikely to be called)
        must_use: Warn if return value unused (True or message)
        deprecated: Mark as deprecated (True or {since, note})
        doc: Documentation (usually from docstring automatically)
        attrs: List of custom RustAttribute objects

    Returns:
        Decorator function that attaches RustAttrs to the target

    Example:
        @rust(derive=[Debug, Clone], repr="C")
        class Point:
            x: int
            y: int

        @rust(inline="always", must_use="important result")
        def calculate(x: int) -> int:
            return x * 2

        @rust(attrs=[attr("tokio::main")])
        async def main() -> None:
            pass
    """
    rust_attrs = RustAttrs(
        derive=derive or [],
        repr=repr,
        serde=serde,
        allow=allow or [],
        deny=deny or [],
        warn=warn or [],
        cfg=cfg,
        cfg_attr=cfg_attr,
        inline=inline,
        cold=cold,
        must_use=must_use,
        deprecated=deprecated,
        doc=doc,
        attrs=attrs or [],
    )

    def decorator(target: T) -> T:
        # Store the attributes on the target
        target.__rust_attrs__ = rust_attrs  # type: ignore

        # If it's a class with a docstring and no explicit doc, use the docstring
        if hasattr(target, "__doc__") and target.__doc__ and not rust_attrs.doc:
            rust_attrs.doc = target.__doc__

        return target

    return decorator


# Convenience function for simple derive-only usage
def derive(*traits: type[DeriveTrait] | str) -> Callable[[T], T]:
    """Shorthand decorator for just #[derive(...)].

    Usage:
        @derive(Debug, Clone, PartialEq)
        class Point:
            x: int
            y: int

    Equivalent to:
        @rust(derive=[Debug, Clone, PartialEq])
        class Point:
            x: int
            y: int
    """
    return rust(derive=list(traits))
