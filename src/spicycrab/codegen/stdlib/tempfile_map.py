"""Mappings for Python tempfile module to Rust tempfile crate."""

from __future__ import annotations

from spicycrab.codegen.stdlib.types import StdlibMapping

# tempfile module mappings
TEMPFILE_MAPPINGS: dict[str, StdlibMapping] = {
    # tempfile.gettempdir() -> get system temp directory
    "tempfile.gettempdir": StdlibMapping(
        python_module="tempfile",
        python_func="gettempdir",
        rust_code="std::env::temp_dir().to_string_lossy().to_string()",
        rust_imports=[],
        needs_result=False,
    ),
    # tempfile.mkdtemp() -> create a temporary directory
    # Returns the path as a string, uses keep() to persist the directory
    "tempfile.mkdtemp": StdlibMapping(
        python_module="tempfile",
        python_func="mkdtemp",
        rust_code=(
            "{ let d = tempfile::tempdir().unwrap(); "
            "let p = d.path().to_string_lossy().to_string(); let _ = d.keep(); p }"
        ),
        rust_imports=[],
        needs_result=False,
    ),
    # tempfile.mkstemp() -> create a temporary file
    # Returns (fd, path) tuple - we return just the path for simplicity
    "tempfile.mkstemp": StdlibMapping(
        python_module="tempfile",
        python_func="mkstemp",
        rust_code=(
            "{ let f = tempfile::NamedTempFile::new().unwrap(); "
            "let p = f.path().to_string_lossy().to_string(); std::mem::forget(f); p }"
        ),
        rust_imports=[],
        needs_result=False,
    ),
    # tempfile.NamedTemporaryFile() -> create a named temporary file
    # Returns a file-like object, we return the NamedTempFile
    "tempfile.NamedTemporaryFile": StdlibMapping(
        python_module="tempfile",
        python_func="NamedTemporaryFile",
        rust_code="tempfile::NamedTempFile::new().unwrap()",
        rust_imports=[],
        needs_result=False,
    ),
    # tempfile.TemporaryDirectory() -> create a temporary directory
    # Returns a context manager, we return TempDir
    "tempfile.TemporaryDirectory": StdlibMapping(
        python_module="tempfile",
        python_func="TemporaryDirectory",
        rust_code="tempfile::tempdir().unwrap()",
        rust_imports=[],
        needs_result=False,
    ),
    # tempfile.tempdir() -> create a temporary directory (alias)
    "tempfile.tempdir": StdlibMapping(
        python_module="tempfile",
        python_func="tempdir",
        rust_code="tempfile::tempdir().unwrap()",
        rust_imports=[],
        needs_result=False,
    ),
}


def get_tempfile_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a tempfile module function."""
    return TEMPFILE_MAPPINGS.get(func_name)
