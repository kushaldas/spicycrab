"""Mappings for Python glob module to Rust glob crate."""

from __future__ import annotations

from spicycrab.codegen.stdlib.os_map import StdlibMapping


# glob module mappings
GLOB_MAPPINGS: dict[str, StdlibMapping] = {
    # glob.glob(pattern) -> list of paths as strings (matching Python behavior)
    # Rust glob returns PathBuf, so we convert to String for Python compatibility
    # Note: glob::glob expects &str, so we use &{args} to borrow the String
    "glob.glob": StdlibMapping(
        python_module="glob",
        python_func="glob",
        rust_code="glob::glob(&{args}).unwrap().filter_map(|p| p.ok()).map(|p| p.to_string_lossy().to_string()).collect::<Vec<_>>()",
        rust_imports=[],
        needs_result=False,
    ),
    # glob.iglob(pattern) -> iterator of paths (collected to Vec for simplicity)
    # Same as glob.glob for now since Rust iterators need to be collected
    "glob.iglob": StdlibMapping(
        python_module="glob",
        python_func="iglob",
        rust_code="glob::glob(&{args}).unwrap().filter_map(|p| p.ok()).map(|p| p.to_string_lossy().to_string()).collect::<Vec<_>>()",
        rust_imports=[],
        needs_result=False,
    ),
    # glob.escape(pathname) -> escaped string
    # Escapes special glob characters: * ? [ ]
    "glob.escape": StdlibMapping(
        python_module="glob",
        python_func="escape",
        rust_code='{args}.replace("[", "[[]").replace("]", "[]]").replace("*", "[*]").replace("?", "[?]")',
        rust_imports=[],
        needs_result=False,
    ),
}


def get_glob_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a glob module function."""
    return GLOB_MAPPINGS.get(func_name)
