"""Discover and load mappings from installed stub packages.

This module enables self-describing stub packages for Rust crates.
Stub packages include a `_spicycrab.toml` file that describes how to
transpile Python code using that crate's API to Rust.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from importlib.metadata import distributions, entry_points
from importlib.resources import files
from typing import Any

from spicycrab.codegen.stdlib.types import StdlibMapping
from spicycrab.debug_log import increment, log_decision


@dataclass
class StubPackage:
    """Represents a discovered stub package."""

    name: str
    rust_crate: str
    rust_version: str
    python_module: str
    cargo_deps: dict[str, Any] = field(default_factory=dict)
    function_mappings: dict[str, StdlibMapping] = field(default_factory=dict)
    method_mappings: dict[str, StdlibMapping] = field(default_factory=dict)
    type_mappings: dict[str, str] = field(default_factory=dict)
    # Enum variant mappings (e.g., "Protocol.Tlsv12" -> "native_tls::Protocol::Tlsv12")
    enum_variant_mappings: dict[str, str] = field(default_factory=dict)
    # Features available in this crate
    available_features: list[str] = field(default_factory=list)
    # Default features (enabled by default)
    default_features: list[str] = field(default_factory=list)


def discover_stub_packages() -> dict[str, StubPackage]:
    """Discover all installed spicycrab stub packages.

    Discovery happens via two methods:
    1. Entry points (preferred) - packages register via [project.entry-points."spicycrab.stubs"]
    2. Package name scanning - packages named spicycrab-* are scanned for _spicycrab.toml

    Returns:
        Dict mapping crate name to StubPackage
    """
    packages: dict[str, StubPackage] = {}

    # Method 1: Entry points (preferred)
    try:
        eps = entry_points(group="spicycrab.stubs")
        for ep in eps:
            try:
                module = ep.load()
                pkg = _load_stub_package(ep.name, module.__name__)
                if pkg:
                    packages[pkg.name] = pkg
            except Exception:
                pass  # Skip invalid packages
    except Exception:
        pass  # entry_points may fail on older Python

    # Method 2: Scan installed packages for _spicycrab.toml
    try:
        for dist in distributions():
            dist_name = dist.name or ""
            if dist_name.startswith("spicycrab-"):
                crate_name = dist_name.replace("spicycrab-", "")
                if crate_name not in packages:
                    module_name = dist_name.replace("-", "_")
                    pkg = _load_stub_package(crate_name, module_name)
                    if pkg:
                        packages[pkg.name] = pkg
    except Exception:
        pass

    return packages


def _load_stub_package(crate_name: str, module_name: str) -> StubPackage | None:
    """Load a stub package from its _spicycrab.toml.

    Args:
        crate_name: Name of the Rust crate
        module_name: Python module name (e.g., spicycrab_clap)

    Returns:
        StubPackage if successfully loaded, None otherwise
    """
    try:
        pkg_files = files(module_name)
        toml_file = pkg_files.joinpath("_spicycrab.toml")
        content = toml_file.read_text()
        config = tomllib.loads(content)
        return _parse_config(config)
    except Exception:
        return None


def _parse_config(config: dict[str, Any]) -> StubPackage:
    """Parse _spicycrab.toml into StubPackage.

    Args:
        config: Parsed TOML configuration

    Returns:
        Populated StubPackage instance
    """
    pkg = config["package"]

    function_mappings: dict[str, StdlibMapping] = {}
    method_mappings: dict[str, StdlibMapping] = {}
    type_mappings: dict[str, str] = {}

    mappings = config.get("mappings", {})

    # Parse function mappings
    for func in mappings.get("functions", []):
        mapping = StdlibMapping(
            python_module=pkg["python_module"],
            python_func=func["python"].split(".")[-1],
            rust_code=func["rust_code"],
            rust_imports=func.get("rust_imports", []),
            needs_result=func.get("needs_result", False),
            param_types=func.get("param_types"),
        )
        function_mappings[func["python"]] = mapping

    # Parse method mappings (for instance methods with {self})
    for method in mappings.get("methods", []):
        mapping = StdlibMapping(
            python_module=pkg["python_module"],
            python_func=method["python"],
            rust_code=method["rust_code"],
            rust_imports=method.get("rust_imports", []),
            needs_result=method.get("needs_result", False),
            param_types=method.get("param_types"),
            returns=method.get("returns"),
        )
        method_mappings[method["python"]] = mapping

    # Parse type mappings (Python type -> Rust type)
    for typ in mappings.get("types", []):
        type_mappings[typ["python"]] = typ["rust"]

    # Parse enum variant mappings (e.g., "Protocol.Tlsv12" -> "native_tls::Protocol::Tlsv12")
    enum_variant_mappings: dict[str, str] = {}
    for variant in mappings.get("enum_variants", []):
        enum_variant_mappings[variant["python"]] = variant["rust"]

    # Parse feature information
    cargo_config = config.get("cargo", {})
    features_config = cargo_config.get("features", {})

    return StubPackage(
        name=pkg["name"],
        rust_crate=pkg["rust_crate"],
        rust_version=pkg["rust_version"],
        python_module=pkg["python_module"],
        cargo_deps=cargo_config.get("dependencies", {}),
        function_mappings=function_mappings,
        method_mappings=method_mappings,
        type_mappings=type_mappings,
        enum_variant_mappings=enum_variant_mappings,
        available_features=features_config.get("available", []),
        default_features=features_config.get("default", []),
    )


# Cache discovered packages (lazy initialization)
_stub_cache: dict[str, StubPackage] | None = None


def _get_cache() -> dict[str, StubPackage]:
    """Get or initialize the stub package cache."""
    global _stub_cache
    if _stub_cache is None:
        _stub_cache = discover_stub_packages()
    return _stub_cache


def clear_stub_cache() -> None:
    """Clear the stub package cache (useful for testing)."""
    global _stub_cache
    _stub_cache = None


def get_stub_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a function from any installed stub package.

    Args:
        func_name: Fully qualified function name (e.g., "clap.Command.new")

    Returns:
        StdlibMapping if found, None otherwise
    """
    cache = _get_cache()
    for pkg in cache.values():
        if func_name in pkg.function_mappings:
            mapping = pkg.function_mappings[func_name]
            log_decision(
                "stub_function_lookup",
                key=func_name,
                found=True,
                crate=pkg.name,
                rust_code=mapping.rust_code,
            )
            increment("stub_function_hits")
            return mapping
    log_decision("stub_function_lookup", key=func_name, found=False)
    increment("stub_function_misses")
    return None


def get_stub_method_mapping(type_name: str, method_name: str) -> StdlibMapping | None:
    """Get mapping for a method from any installed stub package.

    Args:
        type_name: Type name (e.g., "Command")
        method_name: Method name (e.g., "arg")

    Returns:
        StdlibMapping if found, None otherwise
    """
    cache = _get_cache()
    key = f"{type_name}.{method_name}"
    for pkg in cache.values():
        if key in pkg.method_mappings:
            mapping = pkg.method_mappings[key]
            log_decision(
                "stub_method_lookup",
                key=key,
                found=True,
                crate=pkg.name,
                rust_code=mapping.rust_code,
            )
            increment("stub_method_hits")
            return mapping
    log_decision("stub_method_lookup", key=key, found=False)
    increment("stub_method_misses")
    return None


def get_stub_type_mapping(python_type: str, crate_name: str | None = None) -> str | None:
    """Get Rust type for a Python type from installed stub packages.

    Args:
        python_type: Python type name (e.g., "Command")
        crate_name: Optional crate name to restrict lookup to (e.g., "tokio").
                    If provided, only looks in that crate's mappings.
                    If None, searches all crates (legacy behavior, not recommended).

    Returns:
        Rust type path if found, None otherwise

    Note:
        When multiple crates export the same type name (e.g., Sender in fern and tokio),
        you MUST provide crate_name to get the correct mapping. Without it, the first
        match is returned which may be from the wrong crate.
    """
    cache = _get_cache()

    # If crate_name is specified, only look in that crate's package
    if crate_name is not None:
        pkg = cache.get(crate_name)
        if pkg and python_type in pkg.type_mappings:
            rust_type = pkg.type_mappings[python_type]
            log_decision(
                "stub_type_lookup",
                python_type=python_type,
                crate=crate_name,
                found=True,
                rust_type=rust_type,
            )
            increment("stub_type_hits")
            return rust_type
        log_decision(
            "stub_type_lookup",
            python_type=python_type,
            crate=crate_name,
            found=False,
        )
        increment("stub_type_misses")
        return None

    # Legacy behavior: search all packages (not recommended for conflicting names)
    for pkg in cache.values():
        if python_type in pkg.type_mappings:
            rust_type = pkg.type_mappings[python_type]
            log_decision(
                "stub_type_lookup",
                python_type=python_type,
                crate=pkg.name,
                found=True,
                rust_type=rust_type,
                legacy_search=True,
            )
            increment("stub_type_hits")
            return rust_type
    log_decision(
        "stub_type_lookup",
        python_type=python_type,
        crate=None,
        found=False,
        legacy_search=True,
    )
    increment("stub_type_misses")
    return None


def get_stub_enum_variant_mapping(enum_type: str, variant: str, crate_name: str | None = None) -> str | None:
    """Get Rust path for an enum variant from installed stub packages.

    Args:
        enum_type: Enum type name (e.g., "Protocol")
        variant: Variant name (e.g., "Tlsv12")
        crate_name: Optional crate name to restrict lookup to

    Returns:
        Rust enum variant path if found (e.g., "native_tls::Protocol::Tlsv12"), None otherwise
    """
    cache = _get_cache()
    key = f"{enum_type}.{variant}"

    # If crate_name is specified, only look in that crate's package
    if crate_name is not None:
        pkg = cache.get(crate_name)
        if pkg and key in pkg.enum_variant_mappings:
            rust_path = pkg.enum_variant_mappings[key]
            log_decision(
                "stub_enum_variant_lookup",
                key=key,
                crate=crate_name,
                found=True,
                rust_path=rust_path,
            )
            increment("stub_enum_variant_hits")
            return rust_path
        log_decision("stub_enum_variant_lookup", key=key, crate=crate_name, found=False)
        increment("stub_enum_variant_misses")
        return None

    # Search all packages
    for pkg in cache.values():
        if key in pkg.enum_variant_mappings:
            rust_path = pkg.enum_variant_mappings[key]
            log_decision(
                "stub_enum_variant_lookup",
                key=key,
                crate=pkg.name,
                found=True,
                rust_path=rust_path,
            )
            increment("stub_enum_variant_hits")
            return rust_path
    log_decision("stub_enum_variant_lookup", key=key, found=False)
    increment("stub_enum_variant_misses")
    return None


def get_stub_cargo_deps() -> dict[str, Any]:
    """Get all cargo dependencies from installed stub packages.

    Returns:
        Dict of dependency name to dependency spec (version or table)
    """
    cache = _get_cache()
    deps: dict[str, Any] = {}
    for pkg in cache.values():
        deps.update(pkg.cargo_deps)
    return deps


def get_all_stub_packages() -> dict[str, StubPackage]:
    """Get all discovered stub packages.

    Returns:
        Dict mapping crate name to StubPackage
    """
    return _get_cache().copy()


def get_crate_for_python_module(python_module: str) -> str | None:
    """Get the Rust crate name for a Python stub module.

    Args:
        python_module: Python module name (e.g., "spicycrab_anyhow")

    Returns:
        Crate name if found (e.g., "anyhow"), None otherwise
    """
    cache = _get_cache()
    for pkg in cache.values():
        if pkg.python_module == python_module:
            return pkg.name
    return None


def get_stub_package_by_module(python_module: str) -> StubPackage | None:
    """Get a stub package by its Python module name.

    Args:
        python_module: Python module name (e.g., "spicycrab_anyhow")

    Returns:
        StubPackage if found, None otherwise
    """
    cache = _get_cache()
    for pkg in cache.values():
        if pkg.python_module == python_module:
            return pkg
    return None


def load_user_feature_config(project_dir: str | None = None) -> dict[str, list[str]]:
    """Load user feature configuration from pyproject.toml or spicycrab.toml.

    Searches for configuration in the following order:
    1. pyproject.toml with [tool.spicycrab.features] section
    2. spicycrab.toml with [features] section

    Example pyproject.toml:
        [tool.spicycrab.features]
        reqwest = ["blocking", "json"]
        tokio = ["full"]

    Example spicycrab.toml:
        [features]
        reqwest = ["blocking", "json"]
        tokio = ["full"]

    Args:
        project_dir: Directory to search for config files. Defaults to current directory.

    Returns:
        Dict mapping crate name to list of features to enable
    """
    from pathlib import Path

    if project_dir is None:
        project_dir = "."
    project_path = Path(project_dir)

    # Try pyproject.toml first
    pyproject = project_path / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            config = tomllib.loads(content)
            tool_config = config.get("tool", {}).get("spicycrab", {})
            features = tool_config.get("features", {})
            if features:
                return features
        except Exception:
            pass  # Fall through to spicycrab.toml

    # Try spicycrab.toml
    spicycrab_toml = project_path / "spicycrab.toml"
    if spicycrab_toml.exists():
        try:
            content = spicycrab_toml.read_text()
            config = tomllib.loads(content)
            return config.get("features", {})
        except Exception:
            pass

    return {}


def get_stub_cargo_deps_with_features(
    project_dir: str | None = None,
    user_features: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Get cargo dependencies with user-specified features merged in.

    Args:
        project_dir: Directory to search for user config. Defaults to current directory.
        user_features: Optional dict of features to use instead of loading from config.

    Returns:
        Dict of dependency name to dependency spec with features applied
    """
    cache = _get_cache()

    # Load user features from config if not provided
    if user_features is None:
        user_features = load_user_feature_config(project_dir)

    deps: dict[str, Any] = {}
    for pkg in cache.values():
        # Use pkg.name for Cargo.toml (e.g., "native-tls" with hyphen)
        # pkg.rust_crate is for Rust code (e.g., "native_tls" with underscore)
        cargo_dep_name = pkg.name
        version = pkg.rust_version

        # Start with default features or empty list
        features: list[str] = []

        # Check if user specified features for this crate (using either name format)
        if cargo_dep_name in user_features:
            features = user_features[cargo_dep_name]
        elif pkg.rust_crate in user_features:
            features = user_features[pkg.rust_crate]
        elif pkg.default_features:
            # Use default features if user didn't specify
            features = list(pkg.default_features)

        # Create dependency spec
        if features:
            deps[cargo_dep_name] = {
                "version": version,
                "features": features,
            }
        else:
            deps[cargo_dep_name] = version

    return deps


def get_crate_available_features(crate_name: str) -> list[str]:
    """Get available features for a crate.

    Args:
        crate_name: Name of the Rust crate

    Returns:
        List of available feature names, empty if crate not found
    """
    cache = _get_cache()
    pkg = cache.get(crate_name)
    if pkg:
        return list(pkg.available_features)
    return []


def get_crate_default_features(crate_name: str) -> list[str]:
    """Get default features for a crate.

    Args:
        crate_name: Name of the Rust crate

    Returns:
        List of default feature names, empty if crate not found
    """
    cache = _get_cache()
    pkg = cache.get(crate_name)
    if pkg:
        return list(pkg.default_features)
    return []
