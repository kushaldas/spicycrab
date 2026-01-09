"""Cargo.toml generator for spicycrab.

Generates a Cargo.toml file for the transpiled Rust project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from spicycrab.codegen.stub_discovery import get_stub_cargo_deps

if TYPE_CHECKING:
    from spicycrab.ir.nodes import IRModule


@dataclass
class CargoDependency:
    """A Cargo dependency."""

    name: str
    version: str
    features: list[str] = field(default_factory=list)
    optional: bool = False

    def to_toml(self) -> str:
        """Convert to TOML format."""
        if self.features or self.optional:
            parts = [f'version = "{self.version}"']
            if self.features:
                features_str = ", ".join(f'"{f}"' for f in self.features)
                parts.append(f"features = [{features_str}]")
            if self.optional:
                parts.append("optional = true")
            return f"{self.name} = {{ {', '.join(parts)} }}"
        return f'{self.name} = "{self.version}"'


# Default dependencies for common patterns
DEFAULT_DEPS: list[CargoDependency] = [
    CargoDependency("thiserror", "1.0"),
    CargoDependency("anyhow", "1.0"),
]

# Dependencies triggered by specific imports
IMPORT_DEPS: dict[str, list[CargoDependency]] = {
    "json": [
        CargoDependency("serde", "1.0", features=["derive"]),
        CargoDependency("serde_json", "1.0"),
    ],
    "collections": [
        CargoDependency("indexmap", "2.0"),
    ],
    "datetime": [
        CargoDependency("chrono", "0.4"),
    ],
    "glob": [
        CargoDependency("glob", "0.3"),
    ],
    "tempfile": [
        CargoDependency("tempfile", "3"),
    ],
    "shutil": [
        CargoDependency("which", "6"),
    ],
    "random": [
        CargoDependency("rand", "0.8"),
        CargoDependency("rand_distr", "0.4"),  # For distributions like gauss
    ],
    # Note: Python's time module maps to std::time (no external dependency)
    # Note: subprocess module maps to std::process (no external dependency)
}

# Dependencies for serde_json::Value (used with Any type)
SERDE_JSON_DEPS: list[CargoDependency] = [
    CargoDependency("serde", "1.0", features=["derive"]),
    CargoDependency("serde_json", "1.0"),
]

# Dependencies for async code (tokio runtime)
ASYNC_DEPS: list[CargoDependency] = [
    CargoDependency("tokio", "1", features=["full"]),
]


def generate_cargo_toml(
    name: str,
    version: str = "0.1.0",
    edition: str = "2021",
    modules: list[IRModule] | None = None,
    extra_deps: list[CargoDependency] | None = None,
    is_library: bool = False,
    uses_serde_json: bool = False,
    has_async: bool | None = None,
) -> str:
    """Generate a Cargo.toml file.

    Args:
        name: Project name
        version: Project version
        edition: Rust edition (2018, 2021)
        modules: List of IR modules to analyze for dependencies
        extra_deps: Additional dependencies to include
        is_library: If True, generate a library crate
        uses_serde_json: If True, include serde_json dependency (for Any type)
        has_async: If True, include tokio dependency. If None, auto-detect from modules.

    Returns:
        Cargo.toml content as string
    """
    lines: list[str] = []

    # Package section
    lines.append("[package]")
    lines.append(f'name = "{name}"')
    lines.append(f'version = "{version}"')
    lines.append(f'edition = "{edition}"')
    lines.append("")

    # Collect dependencies
    deps: dict[str, CargoDependency] = {}

    # Add default dependencies
    for dep in DEFAULT_DEPS:
        deps[dep.name] = dep

    # Analyze modules for import-based dependencies
    if modules:
        for module in modules:
            for imp in module.imports:
                mod_name = imp.module.split(".")[0]
                if mod_name in IMPORT_DEPS:
                    for dep in IMPORT_DEPS[mod_name]:
                        deps[dep.name] = dep

    # Add serde_json if Any type is used
    if uses_serde_json:
        for dep in SERDE_JSON_DEPS:
            deps[dep.name] = dep

    # Detect or use async flag for tokio dependency
    uses_async = has_async
    if uses_async is None and modules:
        # Auto-detect async functions
        for module in modules:
            for func in module.functions:
                if func.is_async:
                    uses_async = True
                    break
            if uses_async:
                break

    if uses_async:
        for dep in ASYNC_DEPS:
            deps[dep.name] = dep

    # Add extra dependencies
    if extra_deps:
        for dep in extra_deps:
            deps[dep.name] = dep

    # Add dependencies from installed stub packages
    stub_deps = get_stub_cargo_deps()
    for dep_name, dep_spec in stub_deps.items():
        if dep_name not in deps:
            # Handle both string version and table spec
            if isinstance(dep_spec, str):
                deps[dep_name] = CargoDependency(dep_name, dep_spec)
            elif isinstance(dep_spec, dict):
                version = dep_spec.get("version", "")
                features = dep_spec.get("features", [])
                optional = dep_spec.get("optional", False)
                deps[dep_name] = CargoDependency(dep_name, version, features=features, optional=optional)

    # Dependencies section
    if deps:
        lines.append("[dependencies]")
        for dep in sorted(deps.values(), key=lambda d: d.name):
            lines.append(dep.to_toml())
        lines.append("")

    # Binary target (if not library)
    if not is_library:
        lines.append("[[bin]]")
        lines.append(f'name = "{name}"')
        lines.append('path = "src/main.rs"')
        lines.append("")

    # Rust lint configuration
    # - unused_must_use: async channel operations return Results that may be intentionally ignored
    lines.append("[lints.rust]")
    lines.append('unused_must_use = "allow"')
    lines.append("")

    # Clippy lint configuration
    # - unnecessary_cast: conservative casts ensure type safety for Python int -> Rust u64
    # - vec_init_then_push: optimizing vec![] + push() requires complex analysis
    # - unnecessary_to_owned: string literal to String conversion then borrow is safe
    # - format_in_format_args: f-string transpilation creates format! inside println!
    lines.append("[lints.clippy]")
    lines.append('unnecessary_cast = "allow"')
    lines.append('vec_init_then_push = "allow"')
    lines.append('unnecessary_to_owned = "allow"')
    lines.append('format_in_format_args = "allow"')
    lines.append("")

    return "\n".join(lines)


def generate_lib_rs(module_names: list[str]) -> str:
    """Generate a lib.rs that re-exports modules.

    Args:
        module_names: List of module names to include

    Returns:
        lib.rs content
    """
    lines: list[str] = []

    for name in sorted(module_names):
        lines.append(f"pub mod {name};")

    return "\n".join(lines)


def generate_main_rs(entry_module: str | None = None) -> str:
    """Generate a main.rs file.

    Args:
        entry_module: Optional module containing main function

    Returns:
        main.rs content
    """
    lines: list[str] = []

    if entry_module:
        lines.append(f"mod {entry_module};")
        lines.append("")
        lines.append("fn main() {")
        lines.append(f"    {entry_module}::main();")
        lines.append("}")
    else:
        lines.append("fn main() {")
        lines.append('    println!("Hello from spicycrab!");')
        lines.append("}")

    return "\n".join(lines)
