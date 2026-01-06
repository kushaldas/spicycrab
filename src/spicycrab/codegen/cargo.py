"""Cargo.toml generator for spicycrab.

Generates a Cargo.toml file for the transpiled Rust project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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
    # Note: Python's time module maps to std::time (no external dependency)
    # Note: subprocess module maps to std::process (no external dependency)
}

# Dependencies for serde_json::Value (used with Any type)
SERDE_JSON_DEPS: list[CargoDependency] = [
    CargoDependency("serde", "1.0", features=["derive"]),
    CargoDependency("serde_json", "1.0"),
]


def generate_cargo_toml(
    name: str,
    version: str = "0.1.0",
    edition: str = "2021",
    modules: list[IRModule] | None = None,
    extra_deps: list[CargoDependency] | None = None,
    is_library: bool = False,
    uses_serde_json: bool = False,
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

    # Add extra dependencies
    if extra_deps:
        for dep in extra_deps:
            deps[dep.name] = dep

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
