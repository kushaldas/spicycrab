"""Type definitions for stdlib mappings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StdlibMapping:
    """A mapping from Python stdlib to Rust."""

    python_module: str
    python_func: str
    rust_code: str  # Template with {args} placeholder
    rust_imports: list[str]
    needs_result: bool = False  # Whether it returns Result
    param_types: list[str] | None = None  # Rust types for params (for char/&str handling)
    cargo_deps: list[str] | None = None  # Required cargo dependencies
    returns: str | None = None  # Return type for method chaining (e.g., "RequestBuilder")
