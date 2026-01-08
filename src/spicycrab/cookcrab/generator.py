"""Stub generator: Convert parsed Rust crates to Python stub packages.

This module takes the output of the Rust parser and generates:
- pyproject.toml
- spicycrab_<crate>/__init__.py (Python stubs)
- spicycrab_<crate>/_spicycrab.toml (transpilation mappings)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spicycrab.cookcrab._parser import (
        RustCrate,
        RustMethod,
        RustTypeAlias,
    )


# Python reserved keywords - methods with these names must be skipped
PYTHON_RESERVED_KEYWORDS: set[str] = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
}


def is_valid_python_identifier(name: str) -> bool:
    """Check if a name is a valid Python identifier (not a reserved keyword)."""
    return name not in PYTHON_RESERVED_KEYWORDS and name.isidentifier()


def python_safe_name(name: str) -> str:
    """Convert a name to a Python-safe identifier.

    If the name is a Python reserved keyword, append an underscore.
    This follows Python's convention (e.g., class_ for class).
    """
    if name in PYTHON_RESERVED_KEYWORDS:
        return f"{name}_"
    return name


# Rust to Python type mapping
RUST_TO_PYTHON_TYPES: dict[str, str] = {
    "i8": "int",
    "i16": "int",
    "i32": "int",
    "i64": "int",
    "i128": "int",
    "isize": "int",
    "u8": "int",
    "u16": "int",
    "u32": "int",
    "u64": "int",
    "u128": "int",
    "usize": "int",
    "f32": "float",
    "f64": "float",
    "bool": "bool",
    "char": "str",
    "String": "str",
    "&str": "str",
    "&'staticstr": "str",
    "()": "None",
}

# Mapping of methods that require trait imports
# Format: crate_name -> {method_name -> trait_import}
TRAIT_METHOD_IMPORTS: dict[str, dict[str, str]] = {
    "chrono": {
        # Datelike trait methods
        "year": "chrono::Datelike",
        "month": "chrono::Datelike",
        "month0": "chrono::Datelike",
        "day": "chrono::Datelike",
        "day0": "chrono::Datelike",
        "ordinal": "chrono::Datelike",
        "ordinal0": "chrono::Datelike",
        "weekday": "chrono::Datelike",
        "iso_week": "chrono::Datelike",
        "with_year": "chrono::Datelike",
        "with_month": "chrono::Datelike",
        "with_month0": "chrono::Datelike",
        "with_day": "chrono::Datelike",
        "with_day0": "chrono::Datelike",
        "with_ordinal": "chrono::Datelike",
        "with_ordinal0": "chrono::Datelike",
        # Timelike trait methods
        "hour": "chrono::Timelike",
        "minute": "chrono::Timelike",
        "second": "chrono::Timelike",
        "nanosecond": "chrono::Timelike",
        "with_hour": "chrono::Timelike",
        "with_minute": "chrono::Timelike",
        "with_second": "chrono::Timelike",
        "with_nanosecond": "chrono::Timelike",
        "num_seconds_from_midnight": "chrono::Timelike",
    },
}


@dataclass
class FunctionMapping:
    """A function/constructor mapping."""

    python: str
    rust_code: str
    rust_imports: list[str] = field(default_factory=list)
    needs_result: bool = False
    param_types: list[str] = field(default_factory=list)  # Rust types for each param


@dataclass
class MethodMapping:
    """A method mapping."""

    python: str
    rust_code: str
    rust_imports: list[str] = field(default_factory=list)
    needs_result: bool = False
    returns_self: bool = False
    param_types: list[str] = field(default_factory=list)  # Rust types for each param


@dataclass
class TypeMapping:
    """A type mapping."""

    python: str
    rust: str


@dataclass
class GeneratedStub:
    """Generated stub package data."""

    crate_name: str
    version: str
    python_module: str
    init_py: str
    spicycrab_toml: str
    pyproject_toml: str


def sanitize_rust_type(rust_type: str) -> str:
    """Sanitize Rust-specific syntax that doesn't translate to Python.

    Removes lifetimes, dyn keywords, trait bounds, macros, etc.
    Returns a valid Python type or 'object' for unsupported types.
    """
    import re

    # Handle macro invocations (e.g., impl_backtrace!()) -> object
    if "!" in rust_type:
        return "object"

    # Handle parenthesized dyn types like (dyn StdError + ...) -> object
    if rust_type.startswith("(") and "dyn" in rust_type:
        return "object"

    # Handle Rust tuples like (usize, Option<usize>) -> object
    # These need special handling that's beyond simple sanitization
    if rust_type.startswith("(") and "," in rust_type:
        return "object"

    # Handle types with references inside generics (e.g., Bound<&usize>)
    # These can't be represented in Python type hints
    if "<&" in rust_type or "< &" in rust_type:
        return "object"

    # Handle types with Self inside generics (e.g., Error<Self>)
    # Self is a Rust-specific type that can't be represented in Python
    if "<Self>" in rust_type or "< Self>" in rust_type or "<Self," in rust_type:
        return "object"

    # Handle Rust array types [T; N]
    if rust_type.startswith("[") and ";" in rust_type:
        return "object"

    # Handle Rust unit type () and Result<()>
    if rust_type == "()" or rust_type == "Result<()>" or rust_type == "Result< ()>":
        return "None"
    if "<()>" in rust_type or "< ()>" in rust_type:
        return "object"

    # Remove std::ops:: and other common path prefixes
    rust_type = rust_type.replace("std::ops::", "")
    rust_type = rust_type.replace("std::fmt::", "")
    rust_type = rust_type.replace("std::marker::", "")
    rust_type = rust_type.replace("core::ops::", "")
    rust_type = rust_type.replace("core::fmt::", "")

    # Handle Rust-specific std::ops types and other Rust-only types
    rust_only_types = [
        "Bound<",
        "RangeFull",
        "Range<",
        "RangeInclusive<",
        "RangeTo<",
        "RangeFrom<",
        "RangeToInclusive<",
        "Formatter<",
        "Arguments<",
        "PhantomData<",
    ]
    for rust_only in rust_only_types:
        if rust_type.startswith(rust_only):
            return "object"

    # Remove all lifetime annotations ('static, 'a, '_,  etc.)
    rust_type = re.sub(r"'\w*\s*", "", rust_type)

    # Remove dyn keyword
    rust_type = rust_type.replace("dyn ", "")

    # Remove trait bounds (+ Send + Sync, etc.) - keep only the first type/trait
    if "+" in rust_type and not rust_type.startswith("Option") and not rust_type.startswith("Result"):
        rust_type = rust_type.split("+")[0].strip()

    # Remove mut keyword (handle both "mut " and "mut" prefix)
    rust_type = re.sub(r"\bmut\s+", "", rust_type)
    rust_type = re.sub(r"\bmut([A-Z])", r"\1", rust_type)  # mutE -> E
    rust_type = re.sub(r"\bmut\(", "(", rust_type)  # mut(...) -> (...)

    # Handle impl Trait types (can't be expressed in Python)
    if "impl" in rust_type.lower():
        return "object"

    # Remove * const and * mut (raw pointers) -> object
    if rust_type.startswith("*"):
        return "object"

    # Handle empty generics like Request<> -> Request
    rust_type = re.sub(r"<\s*>", "", rust_type)

    # Handle malformed generics with leading comma like Mut<,T> -> object
    if re.search(r"<\s*,", rust_type):
        return "object"

    # Handle incomplete generics that just have > without matching <
    if ">" in rust_type and "<" not in rust_type:
        return "object"

    # Clean up any remaining whitespace issues
    rust_type = " ".join(rust_type.split())

    # If result is empty or just punctuation, return object
    if not rust_type or rust_type in ("()", "(,)", ""):
        return "object"

    return rust_type.strip()


def rust_type_to_python(rust_type: str) -> str:
    """Convert a Rust type to Python type hint."""
    # Remove leading/trailing whitespace
    rust_type = rust_type.strip()

    # First, sanitize Rust-specific syntax
    rust_type = sanitize_rust_type(rust_type)

    # If sanitization returned "object", use it directly
    if rust_type == "object":
        return "object"

    # Direct mapping
    if rust_type in RUST_TO_PYTHON_TYPES:
        return RUST_TO_PYTHON_TYPES[rust_type]

    # Handle reference types
    if rust_type.startswith("&"):
        inner = rust_type[1:].strip()
        return rust_type_to_python(inner)

    # Handle Option<T>
    if rust_type.startswith("Option<") and rust_type.endswith(">"):
        inner = rust_type[7:-1]
        return f"{rust_type_to_python(inner)} | None"

    # Handle Result<T, E>
    if rust_type.startswith("Result<") and rust_type.endswith(">"):
        # Just use the Ok type for simplicity
        inner = rust_type[7:-1]
        # Find the first comma at depth 0
        depth = 0
        for i, c in enumerate(inner):
            if c == "<":
                depth += 1
            elif c == ">":
                depth -= 1
            elif c == "," and depth == 0:
                inner = inner[:i]
                break
        return rust_type_to_python(inner)

    # Handle Vec<T>
    if rust_type.startswith("Vec<") and rust_type.endswith(">"):
        inner = rust_type[4:-1]
        return f"list[{rust_type_to_python(inner)}]"

    # Handle HashMap<K, V>
    if rust_type.startswith("HashMap<") and rust_type.endswith(">"):
        inner = rust_type[8:-1]
        # Find comma at depth 0
        depth = 0
        for i, c in enumerate(inner):
            if c == "<":
                depth += 1
            elif c == ">":
                depth -= 1
            elif c == "," and depth == 0:
                key = inner[:i].strip()
                value = inner[i + 1 :].strip()
                return f"dict[{rust_type_to_python(key)}, {rust_type_to_python(value)}]"
        return "dict"

    # Handle Box<T>
    if rust_type.startswith("Box<") and rust_type.endswith(">"):
        inner = rust_type[4:-1]
        return rust_type_to_python(inner)

    # Handle Box<dyn ...> (dynamic trait object - use object)
    if rust_type.startswith("Box<") and "dyn" in rust_type:
        return "object"

    # Handle Self
    if rust_type == "Self":
        return "Self"

    # Handle path types like crate::module::Type
    # Only apply if :: is outside of angle brackets (not inside generics)
    if "::" in rust_type:
        # Check if :: is inside angle brackets
        depth = 0
        outside_brackets = True
        for i, c in enumerate(rust_type):
            if c == "<":
                depth += 1
            elif c == ">":
                depth -= 1
            elif rust_type[i : i + 2] == "::" and depth == 0:
                # Found :: outside brackets, safe to split
                outside_brackets = True
                break
            elif rust_type[i : i + 2] == "::" and depth > 0:
                # Found :: inside brackets, not safe to split
                outside_brackets = False
                break

        if outside_brackets and depth == 0:
            # Split on the last :: that's outside brackets
            last_sep = -1
            depth = 0
            for i, c in enumerate(rust_type):
                if c == "<":
                    depth += 1
                elif c == ">":
                    depth -= 1
                elif rust_type[i : i + 2] == "::" and depth == 0:
                    last_sep = i
            if last_sep >= 0:
                # Recursively process the remaining type after stripping namespace
                return rust_type_to_python(rust_type[last_sep + 2 :])
        else:
            # :: is inside angle brackets (associated type like U::Target)
            # This is too complex to represent in Python, use object
            return "object"

    # Handle standard library error types
    if rust_type in ("StdError", "Error", "std::error::Error"):
        return "Exception"

    # Handle impl Trait (just use object for now)
    if rust_type.startswith("impl "):
        return "object"

    # Final validation - catch any remaining invalid Python type syntax
    # Check for unbalanced angle brackets
    if rust_type.count("<") != rust_type.count(">"):
        return "object"

    # Check for > without < (partial generic remnants)
    if ">" in rust_type and "<" not in rust_type:
        return "object"

    # Check for unknown generics with angle brackets (e.g., Ref<T>, Own<T>)
    # These are Rust generics that we don't have mappings for
    if "<" in rust_type and ">" in rust_type:
        # We've handled all known generics above (Option, Result, Vec, HashMap, Box)
        # Any remaining generics are unknown Rust types
        return "object"

    # Default: return the type name as-is (likely a custom type)
    return rust_type


def generate_method_signature(method: RustMethod, type_name: str) -> str:
    """Generate Python method signature from Rust method."""
    params = []

    if method.self_type:
        params.append("self")

    for param in method.params:
        py_type = rust_type_to_python(param.rust_type)
        # Use safe name for parameters too
        safe_param_name = python_safe_name(param.name)
        params.append(f"{safe_param_name}: {py_type}")

    params_str = ", ".join(params)

    # Determine return type
    if method.return_type:
        ret_type = rust_type_to_python(method.return_type)
        # Handle Self return type
        if ret_type == "Self":
            ret_type = "Self"
    else:
        ret_type = "None"

    # Use safe name for method name
    safe_method_name = python_safe_name(method.name)
    return f"def {safe_method_name}({params_str}) -> {ret_type}: ..."


def generate_static_method_signature(method: RustMethod, type_name: str) -> str:
    """Generate Python static method signature from Rust static method."""
    params = []

    for param in method.params:
        py_type = rust_type_to_python(param.rust_type)
        # Use safe name for parameters too
        safe_param_name = python_safe_name(param.name)
        params.append(f"{safe_param_name}: {py_type}")

    params_str = ", ".join(params)

    # Determine return type
    if method.return_type:
        ret_type = rust_type_to_python(method.return_type)
        if ret_type == "Self" or ret_type == type_name:
            ret_type = f'"{type_name}"'
    else:
        ret_type = "None"

    # Use safe name for method name
    safe_method_name = python_safe_name(method.name)
    return f"def {safe_method_name}({params_str}) -> {ret_type}: ..."


def is_result_type_alias(alias: RustTypeAlias) -> bool:
    """Check if this type alias is a Result type (wraps core::result::Result)."""
    target = alias.target_type.lower()
    return "result" in target and ("core::result" in target or "std::result" in target)


def generate_result_class(alias: RustTypeAlias, crate_name: str) -> list[str]:
    """Generate a Result class for a Result type alias."""
    lines = [
        "",
        "T = TypeVar('T')",
        "E = TypeVar('E')",
        "",
        "",
        f"class {alias.name}(Generic[T, E]):",
        f'    """A Result type alias for {crate_name}.',
        "",
        f"    Maps to {crate_name}::{alias.name} which is an alias for {alias.target_type}.",
        '    """',
        "",
        "    @staticmethod",
        f'    def Ok(value: T) -> "{alias.name}[T, E]":',
        '        """Create a successful result."""',
        "        ...",
        "",
        "    @staticmethod",
        f'    def Err(error: E) -> "{alias.name}[T, E]":',
        '        """Create an error result."""',
        "        ...",
    ]
    return lines


def generate_init_py(crate: RustCrate, crate_name: str) -> str:
    """Generate __init__.py content for the stub package."""
    # Check if we need Generic/TypeVar for Result type aliases
    has_result_alias = any(is_result_type_alias(a) for a in crate.type_aliases)

    typing_imports = ["Self"]
    if has_result_alias:
        typing_imports.extend(["TypeVar", "Generic"])

    lines = [
        f'"""Python stubs for the {crate_name} Rust crate.',
        "",
        f"Install with: cookcrab install {crate_name}",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        f"from typing import {', '.join(typing_imports)}",
    ]

    # Generate Result class for Result type aliases
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            lines.extend(generate_result_class(alias, crate_name))

    # Collect all types and their methods
    type_methods: dict[str, list[RustMethod]] = {}
    for impl in crate.impls:
        if impl.type_name not in type_methods:
            type_methods[impl.type_name] = []
        type_methods[impl.type_name].extend(impl.methods)

    # Generate classes for structs
    all_types = []
    for struct in crate.structs:
        all_types.append(struct.name)
        lines.append("")
        if struct.doc:
            lines.append(f"class {struct.name}:")
            lines.append(f'    """{struct.doc}"""')
        else:
            lines.append(f"class {struct.name}:")

        methods = type_methods.get(struct.name, [])
        if not methods:
            lines.append("    pass")
        else:
            for method in methods:
                lines.append("")
                if method.is_static:
                    lines.append("    @staticmethod")
                    sig = generate_static_method_signature(method, struct.name)
                else:
                    sig = generate_method_signature(method, struct.name)
                lines.append(f"    {sig}")

    # Generate classes for enums
    for enum in crate.enums:
        all_types.append(enum.name)
        lines.append("")
        if enum.doc:
            lines.append(f"class {enum.name}:")
            lines.append(f'    """{enum.doc}"""')
        else:
            lines.append(f"class {enum.name}:")

        # Add variants as class attributes
        for variant in enum.variants:
            safe_name = python_safe_name(variant.name)
            lines.append(f'    {safe_name}: "{enum.name}"')

        methods = type_methods.get(enum.name, [])
        if methods:
            for method in methods:
                lines.append("")
                if method.is_static:
                    lines.append("    @staticmethod")
                    sig = generate_static_method_signature(method, enum.name)
                else:
                    sig = generate_method_signature(method, enum.name)
                lines.append(f"    {sig}")

    # Add Result type aliases to all_types
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            all_types.insert(0, alias.name)  # Put Result first

    # Add __all__
    lines.append("")
    all_str = ", ".join(f'"{t}"' for t in all_types)
    lines.append(f"__all__: list[str] = [{all_str}]")
    lines.append("")

    return "\n".join(lines)


def generate_spicycrab_toml(crate: RustCrate, crate_name: str, version: str, python_module: str) -> str:
    """Generate _spicycrab.toml content."""
    lines = [
        "[package]",
        f'name = "{crate_name}"',
        f'rust_crate = "{crate_name}"',
        f'rust_version = "{version}"',
        f'python_module = "{python_module}"',
        "",
        "[cargo.dependencies]",
        f'{crate_name} = "{version}"',
        "",
    ]

    # Generate mappings for Result type aliases (Result.Ok, Result.Err)
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            # Result.Ok -> Ok({arg0})
            lines.append("# Result type alias - Ok constructor")
            lines.append("[[mappings.functions]]")
            lines.append(f'python = "{crate_name}.{alias.name}.Ok"')
            lines.append('rust_code = "Ok({arg0})"')
            lines.append("rust_imports = []")
            lines.append("needs_result = false")
            lines.append("")
            # Result.Err -> Err({arg0})
            lines.append("# Result type alias - Err constructor")
            lines.append("[[mappings.functions]]")
            lines.append(f'python = "{crate_name}.{alias.name}.Err"')
            lines.append('rust_code = "Err({arg0})"')
            lines.append("rust_imports = []")
            lines.append("needs_result = false")
            lines.append("")

    # Collect all types and their methods
    type_methods: dict[str, list[RustMethod]] = {}
    for impl in crate.impls:
        if impl.type_name not in type_methods:
            type_methods[impl.type_name] = []
        type_methods[impl.type_name].extend(impl.methods)

    # Generate function mappings (static methods / constructors)
    for struct in crate.structs:
        methods = type_methods.get(struct.name, [])
        for method in methods:
            if method.is_static:
                # Generate argument placeholders
                args = ", ".join(f"{{arg{i}}}" for i in range(len(method.params)))
                # Use safe name for Python, original for Rust
                py_method_name = python_safe_name(method.name)
                # Collect param types for type-aware argument transformation
                param_types = [p.rust_type for p in method.params]
                param_types_str = ", ".join(f'"{t}"' for t in param_types)

                # Special case: Error.msg in anyhow should use anyhow! macro
                if struct.name == "Error" and method.name == "msg" and crate_name == "anyhow":
                    lines.append("# Error.msg - use anyhow! macro for string messages")
                    lines.append("[[mappings.functions]]")
                    lines.append(f'python = "{crate_name}.{struct.name}.{py_method_name}"')
                    lines.append(f'rust_code = "{crate_name}::anyhow!({args})"')
                    lines.append("rust_imports = []")
                    lines.append("needs_result = false")
                    if param_types:
                        lines.append(f"param_types = [{param_types_str}]")
                    lines.append("")
                else:
                    lines.append("[[mappings.functions]]")
                    lines.append(f'python = "{crate_name}.{struct.name}.{py_method_name}"')
                    lines.append(f'rust_code = "{crate_name}::{struct.name}::{method.name}({args})"')
                    lines.append(f'rust_imports = ["{crate_name}::{struct.name}"]')
                    lines.append("needs_result = false")
                    if param_types:
                        lines.append(f"param_types = [{param_types_str}]")
                    lines.append("")

    # Generate method mappings (instance methods)
    # Get trait method imports for this crate
    crate_trait_methods = TRAIT_METHOD_IMPORTS.get(crate_name, {})

    for struct in crate.structs:
        methods = type_methods.get(struct.name, [])
        for method in methods:
            if not method.is_static:
                # Generate argument placeholders
                args = ", ".join(f"{{arg{i}}}" for i in range(len(method.params)))
                # Use safe name for Python, original for Rust
                py_method_name = python_safe_name(method.name)
                # Collect param types for type-aware argument transformation
                param_types = [p.rust_type for p in method.params]
                param_types_str = ", ".join(f'"{t}"' for t in param_types)
                returns_self = method.return_type and (
                    "Self" in method.return_type or struct.name in method.return_type
                )

                # Check if this method requires a trait import
                trait_import = crate_trait_methods.get(method.name, "")
                rust_imports = [trait_import] if trait_import else []

                # Check if return type needs conversion to i64 (Python int)
                # Small integer types (i32, u32, i16, u16, etc.) need explicit cast
                # Use "as i64" instead of ".into()" to avoid ambiguity in format contexts
                needs_cast = method.return_type in {"i8", "i16", "i32", "u8", "u16", "u32"}
                into_suffix = " as i64" if needs_cast else ""

                lines.append("[[mappings.methods]]")
                lines.append(f'python = "{struct.name}.{py_method_name}"')
                if args:
                    lines.append(f'rust_code = "{{self}}.{method.name}({args}){into_suffix}"')
                else:
                    lines.append(f'rust_code = "{{self}}.{method.name}(){into_suffix}"')
                if rust_imports:
                    imports_str = ", ".join(f'"{i}"' for i in rust_imports)
                    lines.append(f"rust_imports = [{imports_str}]")
                else:
                    lines.append("rust_imports = []")
                lines.append("needs_result = false")
                if returns_self:
                    lines.append("returns_self = true")
                if param_types:
                    lines.append(f"param_types = [{param_types_str}]")
                lines.append("")

    # Generate type mappings for Result type aliases
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            lines.append("# Result type alias")
            lines.append("[[mappings.types]]")
            lines.append(f'python = "{alias.name}"')
            lines.append(f'rust = "{crate_name}::{alias.name}"')
            lines.append("")

    # Generate type mappings for structs
    for struct in crate.structs:
        lines.append("[[mappings.types]]")
        lines.append(f'python = "{struct.name}"')
        lines.append(f'rust = "{crate_name}::{struct.name}"')
        lines.append("")

    for enum in crate.enums:
        lines.append("[[mappings.types]]")
        lines.append(f'python = "{enum.name}"')
        lines.append(f'rust = "{crate_name}::{enum.name}"')
        lines.append("")

    return "\n".join(lines)


def generate_pyproject_toml(crate_name: str, version: str, python_module: str) -> str:
    """Generate pyproject.toml content."""
    return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "spicycrab-{crate_name}"
version = "{version}"
description = "spicycrab type stubs for the {crate_name} Rust crate"
requires-python = ">=3.11"
dependencies = []

[project.entry-points."spicycrab.stubs"]
{crate_name} = "{python_module}"

[tool.hatch.build.targets.wheel]
packages = ["{python_module}"]
'''


def generate_reexport_init_py(crate_name: str, source_crates: list[str]) -> str:
    """Generate __init__.py that re-exports from source crate stubs."""
    lines = [
        f'"""Python stubs for the {crate_name} Rust crate.',
        "",
        f"This crate re-exports from: {', '.join(source_crates)}",
        '"""',
        "",
        "from __future__ import annotations",
        "",
    ]

    # Import and re-export from each source crate
    for source in source_crates:
        source_module = f"spicycrab_{source.replace('-', '_')}"
        lines.append(f"from {source_module} import *  # noqa: F401, F403")

    lines.append("")
    return "\n".join(lines)


def generate_reexport_toml(
    crate_name: str,
    source_crates: list[str],
    version: str,
    python_module: str,
    output_dir: Path,
) -> str:
    """Generate _spicycrab.toml that copies and rewrites mappings from source crate stubs.

    Reads the generated source crate toml files and rewrites:
    - clap_builder -> clap (or whatever the re-export crate is)
    - python paths: clap_builder.X -> clap.X
    - rust_code: clap_builder::X -> clap::X (since clap re-exports clap_builder)
    - rust_imports: same
    """
    lines = [
        "[package]",
        f'name = "{crate_name}"',
        f'rust_crate = "{crate_name}"',
        f'rust_version = "{version}"',
        f'python_module = "{python_module}"',
        "",
        "# This crate re-exports from other crates",
        f"# Source crates: {', '.join(source_crates)}",
        "",
        "[cargo.dependencies]",
        f'{crate_name} = "{version}"',
        "",
    ]

    # Read and rewrite mappings from each source crate
    for source_crate in source_crates:
        source_module = f"spicycrab_{source_crate.replace('-', '_')}"
        source_toml_path = output_dir / source_crate / source_module / "_spicycrab.toml"

        if not source_toml_path.exists():
            continue

        source_content = source_toml_path.read_text()

        # Find and copy all [[mappings.functions]] and [[mappings.methods]] blocks
        in_mapping_block = False
        current_block: list[str] = []

        for line in source_content.split("\n"):
            if line.startswith("[[mappings."):
                if current_block and in_mapping_block:
                    # Process and add the previous block
                    rewritten_block = _rewrite_mapping_block(current_block, source_crate, crate_name)
                    lines.extend(rewritten_block)
                    lines.append("")
                current_block = [line]
                in_mapping_block = True
            elif in_mapping_block:
                if line.startswith("[") and not line.startswith("[["):
                    # End of mappings section
                    if current_block:
                        rewritten_block = _rewrite_mapping_block(current_block, source_crate, crate_name)
                        lines.extend(rewritten_block)
                        lines.append("")
                    in_mapping_block = False
                    current_block = []
                else:
                    current_block.append(line)

        # Process last block if any
        if current_block and in_mapping_block:
            rewritten_block = _rewrite_mapping_block(current_block, source_crate, crate_name)
            lines.extend(rewritten_block)
            lines.append("")

    return "\n".join(lines)


def _rewrite_mapping_block(block: list[str], source_crate: str, target_crate: str) -> list[str]:
    """Rewrite a mapping block, replacing source crate references with target crate."""
    result = []
    for line in block:
        # Rewrite python paths: clap_builder.X -> clap.X
        if line.startswith("python = "):
            line = line.replace(f'"{source_crate}.', f'"{target_crate}.')
        # Rewrite rust_code: clap_builder:: -> clap::
        elif line.startswith("rust_code = "):
            line = line.replace(f"{source_crate}::", f"{target_crate}::")
        # Rewrite rust_imports: ["clap_builder::X"] -> ["clap::X"]
        elif line.startswith("rust_imports = "):
            line = line.replace(f'"{source_crate}::', f'"{target_crate}::')
        result.append(line)
    return result


def generate_reexport_pyproject(crate_name: str, source_crates: list[str], version: str, python_module: str) -> str:
    """Generate pyproject.toml with dependencies on source crate stubs."""
    deps = ", ".join(f'"spicycrab-{s}"' for s in source_crates)
    return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "spicycrab-{crate_name}"
version = "{version}"
description = "spicycrab type stubs for the {crate_name} Rust crate (re-exports from {", ".join(source_crates)})"
requires-python = ">=3.11"
dependencies = [{deps}]

[project.entry-points."spicycrab.stubs"]
{crate_name} = "{python_module}"

[tool.hatch.build.targets.wheel]
packages = ["{python_module}"]
'''


def generate_reexport_stub_package(
    crate_name: str,
    source_crates: list[str],
    version: str,
    output_dir: Path,
) -> None:
    """Generate a stub package that re-exports from source crate stubs.

    Args:
        crate_name: Name of the wrapper crate (e.g., "clap")
        source_crates: Names of source crates (e.g., ["clap_builder"])
        version: Crate version
        output_dir: Directory to write the stub package to
    """
    python_module = f"spicycrab_{crate_name.replace('-', '_')}"

    # Generate content
    init_py = generate_reexport_init_py(crate_name, source_crates)
    spicycrab_toml = generate_reexport_toml(crate_name, source_crates, version, python_module, output_dir)
    pyproject_toml = generate_reexport_pyproject(crate_name, source_crates, version, python_module)

    # Create output directory structure
    pkg_dir = output_dir / crate_name / python_module
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Write files
    (output_dir / crate_name / "pyproject.toml").write_text(pyproject_toml)
    (pkg_dir / "__init__.py").write_text(init_py)
    (pkg_dir / "_spicycrab.toml").write_text(spicycrab_toml)

    # Create README
    readme = f"""# spicycrab-{crate_name}

Python type stubs for the [{crate_name}](https://crates.io/crates/{crate_name}) Rust crate.

This crate re-exports from: {", ".join(source_crates)}

**Install with cookcrab, NOT pip:**

```bash
cookcrab install {crate_name}
```

## Usage

```python
from {python_module} import Command, Arg, ...
```

## Dependencies

This package depends on:
{chr(10).join(f"- spicycrab-{s}" for s in source_crates)}
"""
    (output_dir / crate_name / "README.md").write_text(readme)


def generate_stub_package(
    crate: RustCrate,
    crate_name: str,
    version: str,
    output_dir: Path,
    source_crates: list[str] | None = None,
) -> GeneratedStub:
    """Generate a complete stub package from a parsed Rust crate.

    Args:
        crate: Parsed Rust crate from the parser
        crate_name: Name of the crate
        version: Crate version
        output_dir: Directory to write the stub package to

    Returns:
        GeneratedStub with the generated content
    """
    # Normalize crate name for Python module
    python_module = f"spicycrab_{crate_name.replace('-', '_')}"

    # Generate content
    init_py = generate_init_py(crate, crate_name)
    spicycrab_toml = generate_spicycrab_toml(crate, crate_name, version, python_module)
    pyproject_toml = generate_pyproject_toml(crate_name, version, python_module)

    # Create output directory structure
    pkg_dir = output_dir / crate_name / python_module
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Write files
    (output_dir / crate_name / "pyproject.toml").write_text(pyproject_toml)
    (pkg_dir / "__init__.py").write_text(init_py)
    (pkg_dir / "_spicycrab.toml").write_text(spicycrab_toml)

    # Create README
    readme = f"""# spicycrab-{crate_name}

Python type stubs for the [{crate_name}](https://crates.io/crates/{crate_name}) Rust crate.

**Install with cookcrab, NOT pip:**

```bash
cookcrab install {crate_name}
```

## Usage

```python
from {python_module} import ...
```
"""
    (output_dir / crate_name / "README.md").write_text(readme)

    return GeneratedStub(
        crate_name=crate_name,
        version=version,
        python_module=python_module,
        init_py=init_py,
        spicycrab_toml=spicycrab_toml,
        pyproject_toml=pyproject_toml,
    )
