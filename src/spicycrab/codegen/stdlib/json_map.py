"""Mappings for Python json module to Rust serde_json."""

from __future__ import annotations

from spicycrab.codegen.stdlib.types import StdlibMapping

# json module mappings
JSON_MAPPINGS: dict[str, StdlibMapping] = {
    "json.loads": StdlibMapping(
        python_module="json",
        python_func="loads",
        rust_code="serde_json::from_str({args}).unwrap()",
        rust_imports=["serde_json"],
        cargo_deps=['serde_json = "1.0"'],
        needs_result=True,
    ),
    "json.dumps": StdlibMapping(
        python_module="json",
        python_func="dumps",
        rust_code="serde_json::to_string({args}).unwrap()",
        rust_imports=["serde_json"],
        cargo_deps=['serde_json = "1.0"'],
        needs_result=True,
    ),
    "json.load": StdlibMapping(
        python_module="json",
        python_func="load",
        rust_code="serde_json::from_reader({args}).unwrap()",
        rust_imports=["serde_json"],
        cargo_deps=['serde_json = "1.0"'],
        needs_result=True,
    ),
    "json.dump": StdlibMapping(
        python_module="json",
        python_func="dump",
        rust_code="serde_json::to_writer({arg1}, {arg0}).unwrap()",
        rust_imports=["serde_json"],
        cargo_deps=['serde_json = "1.0"'],
        needs_result=True,
    ),
}

# Pretty printing variants
JSON_MAPPINGS["json.dumps_indent"] = StdlibMapping(
    python_module="json",
    python_func="dumps",
    rust_code="serde_json::to_string_pretty({args}).unwrap()",
    rust_imports=["serde_json"],
    cargo_deps=['serde_json = "1.0"'],
    needs_result=True,
)


def get_json_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a json module function."""
    return JSON_MAPPINGS.get(func_name)
