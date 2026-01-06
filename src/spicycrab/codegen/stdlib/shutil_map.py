"""Mappings for Python shutil module to Rust std::fs."""

from __future__ import annotations

from spicycrab.codegen.stdlib.os_map import StdlibMapping


# shutil module mappings
SHUTIL_MAPPINGS: dict[str, StdlibMapping] = {
    # shutil.copy(src, dst) -> copy file to destination
    "shutil.copy": StdlibMapping(
        python_module="shutil",
        python_func="copy",
        rust_code="std::fs::copy(&{arg0}, &{arg1}).unwrap()",
        rust_imports=[],
        needs_result=False,
    ),
    # shutil.copy2(src, dst) -> copy file with metadata (simplified: same as copy)
    "shutil.copy2": StdlibMapping(
        python_module="shutil",
        python_func="copy2",
        rust_code="std::fs::copy(&{arg0}, &{arg1}).unwrap()",
        rust_imports=[],
        needs_result=False,
    ),
    # shutil.copyfile(src, dst) -> copy file contents only
    "shutil.copyfile": StdlibMapping(
        python_module="shutil",
        python_func="copyfile",
        rust_code="std::fs::copy(&{arg0}, &{arg1}).unwrap()",
        rust_imports=[],
        needs_result=False,
    ),
    # shutil.rmtree(path) -> remove directory tree
    "shutil.rmtree": StdlibMapping(
        python_module="shutil",
        python_func="rmtree",
        rust_code="std::fs::remove_dir_all(&{args}).unwrap()",
        rust_imports=[],
        needs_result=False,
    ),
    # shutil.move(src, dst) -> move file or directory
    "shutil.move": StdlibMapping(
        python_module="shutil",
        python_func="move",
        rust_code="std::fs::rename(&{arg0}, &{arg1}).unwrap()",
        rust_imports=[],
        needs_result=False,
    ),
    # shutil.which(cmd) -> find executable in PATH (returns empty string if not found)
    "shutil.which": StdlibMapping(
        python_module="shutil",
        python_func="which",
        rust_code="which::which({args}).ok().map(|p| p.to_string_lossy().to_string()).unwrap_or_default()",
        rust_imports=[],
        needs_result=False,
    ),
    # shutil.disk_usage(path) -> get disk usage statistics
    # Returns (total, used, free) - simplified to just return total for now
    "shutil.disk_usage": StdlibMapping(
        python_module="shutil",
        python_func="disk_usage",
        rust_code='{{ let m = std::fs::metadata(&{args}).unwrap(); (m.len(), 0u64, 0u64) }}',
        rust_imports=[],
        needs_result=False,
    ),
}


def get_shutil_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a shutil module function."""
    return SHUTIL_MAPPINGS.get(func_name)
