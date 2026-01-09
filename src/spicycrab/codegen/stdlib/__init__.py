"""Standard library mappings from Python to Rust."""

from spicycrab.codegen.stdlib.collections_map import (
    COLLECTIONS_MAPPINGS,
    DEQUE_METHOD_MAPPINGS,
    get_collections_mapping,
    get_deque_method,
)
from spicycrab.codegen.stdlib.glob_map import (
    GLOB_MAPPINGS,
    get_glob_mapping,
)
from spicycrab.codegen.stdlib.json_map import (
    JSON_MAPPINGS,
    get_json_mapping,
)
from spicycrab.codegen.stdlib.logging_map import (
    LOGGING_MAPPINGS,
    get_logging_mapping,
)
from spicycrab.codegen.stdlib.os_map import (
    OS_MAPPINGS,
    PATHLIB_MAPPINGS,
    SYS_MAPPINGS,
    get_os_mapping,
    get_pathlib_mapping,
    get_sys_mapping,
)
from spicycrab.codegen.stdlib.random_map import (
    RANDOM_MAPPINGS,
    get_random_mapping,
)
from spicycrab.codegen.stdlib.rust_std_map import (
    FS_MAPPINGS,
    FS_METHOD_MAPPINGS,
    IO_MAPPINGS,
    IO_METHOD_MAPPINGS,
    PATH_MAPPINGS,
    PATH_METHOD_MAPPINGS,
    RUST_STD_TYPE_MAPPINGS,
    RUST_TIME_MAPPINGS,
    RUST_TIME_METHOD_MAPPINGS,
    SYNC_MAPPINGS,
    SYNC_METHOD_MAPPINGS,
    THREAD_MAPPINGS,
    THREAD_METHOD_MAPPINGS,
    get_fs_mapping,
    get_fs_method_mapping,
    get_io_mapping,
    get_io_method_mapping,
    get_path_mapping,
    get_path_method_mapping,
    get_rust_std_type,
    get_rust_time_mapping,
    get_rust_time_method_mapping,
    get_sync_mapping,
    get_sync_method_mapping,
    get_thread_mapping,
    get_thread_method_mapping,
    is_rust_std_type,
)
from spicycrab.codegen.stdlib.shutil_map import (
    SHUTIL_MAPPINGS,
    get_shutil_mapping,
)
from spicycrab.codegen.stdlib.subprocess_map import (
    SUBPROCESS_MAPPINGS,
    get_subprocess_mapping,
)
from spicycrab.codegen.stdlib.tempfile_map import (
    TEMPFILE_MAPPINGS,
    get_tempfile_mapping,
)
from spicycrab.codegen.stdlib.time_map import (
    ALL_DATETIME_MAPPINGS,
    DATE_MAPPINGS,
    DATE_METHOD_MAPPINGS,
    DATETIME_MAPPINGS,
    DATETIME_METHOD_MAPPINGS,
    TIME_CLASS_MAPPINGS,
    TIME_CLASS_METHOD_MAPPINGS,
    TIME_MAPPINGS,
    TIMEDELTA_MAPPINGS,
    TIMEDELTA_METHOD_MAPPINGS,
    TIMEZONE_MAPPINGS,
    get_datetime_mapping,
    get_datetime_method_mapping,
    get_time_mapping,
)
from spicycrab.codegen.stdlib.types import StdlibMapping

# Lazy imports for stub_discovery to avoid circular imports
# Import these directly from spicycrab.codegen.stub_discovery when needed


def _get_stub_discovery():
    """Lazy import of stub_discovery module."""
    from spicycrab.codegen import stub_discovery

    return stub_discovery


def get_stub_mapping(key: str):
    """Get stub mapping for a key."""
    return _get_stub_discovery().get_stub_mapping(key)


def get_stub_method_mapping(type_name: str, method_name: str):
    """Get stub method mapping for a type and method."""
    return _get_stub_discovery().get_stub_method_mapping(type_name, method_name)


def get_stub_type_mapping(key: str):
    """Get stub type mapping for a key."""
    return _get_stub_discovery().get_stub_type_mapping(key)


def get_stub_cargo_deps():
    """Get stub cargo dependencies."""
    return _get_stub_discovery().get_stub_cargo_deps()


def get_all_stub_packages():
    """Get all stub packages."""
    return _get_stub_discovery().get_all_stub_packages()


def get_crate_for_python_module(module: str):
    """Get crate for python module."""
    return _get_stub_discovery().get_crate_for_python_module(module)


def get_stub_package_by_module(module: str):
    """Get stub package by module."""
    return _get_stub_discovery().get_stub_package_by_module(module)


def clear_stub_cache():
    """Clear stub cache."""
    return _get_stub_discovery().clear_stub_cache()


__all__ = [
    # Types
    "StdlibMapping",
    # OS mappings
    "OS_MAPPINGS",
    "PATHLIB_MAPPINGS",
    "SYS_MAPPINGS",
    "get_os_mapping",
    "get_pathlib_mapping",
    "get_sys_mapping",
    # JSON mappings
    "JSON_MAPPINGS",
    "get_json_mapping",
    # Glob mappings
    "GLOB_MAPPINGS",
    "get_glob_mapping",
    # Tempfile mappings
    "TEMPFILE_MAPPINGS",
    "get_tempfile_mapping",
    # Subprocess mappings
    "SUBPROCESS_MAPPINGS",
    "get_subprocess_mapping",
    # Shutil mappings
    "SHUTIL_MAPPINGS",
    "get_shutil_mapping",
    # Random mappings
    "RANDOM_MAPPINGS",
    "get_random_mapping",
    # Logging mappings
    "LOGGING_MAPPINGS",
    "get_logging_mapping",
    # Collections mappings
    "COLLECTIONS_MAPPINGS",
    "DEQUE_METHOD_MAPPINGS",
    "get_collections_mapping",
    "get_deque_method",
    # Time module mappings
    "TIME_MAPPINGS",
    "get_time_mapping",
    # Datetime module mappings
    "DATETIME_MAPPINGS",
    "DATE_MAPPINGS",
    "TIME_CLASS_MAPPINGS",
    "TIMEDELTA_MAPPINGS",
    "TIMEZONE_MAPPINGS",
    "ALL_DATETIME_MAPPINGS",
    "DATETIME_METHOD_MAPPINGS",
    "DATE_METHOD_MAPPINGS",
    "TIME_CLASS_METHOD_MAPPINGS",
    "TIMEDELTA_METHOD_MAPPINGS",
    "get_datetime_mapping",
    "get_datetime_method_mapping",
    # Rust std module mappings
    "FS_MAPPINGS",
    "FS_METHOD_MAPPINGS",
    "IO_MAPPINGS",
    "IO_METHOD_MAPPINGS",
    "PATH_MAPPINGS",
    "PATH_METHOD_MAPPINGS",
    "SYNC_MAPPINGS",
    "SYNC_METHOD_MAPPINGS",
    "THREAD_MAPPINGS",
    "THREAD_METHOD_MAPPINGS",
    "RUST_TIME_MAPPINGS",
    "RUST_TIME_METHOD_MAPPINGS",
    "RUST_STD_TYPE_MAPPINGS",
    "get_fs_mapping",
    "get_fs_method_mapping",
    "get_io_mapping",
    "get_io_method_mapping",
    "get_path_mapping",
    "get_path_method_mapping",
    "get_sync_mapping",
    "get_sync_method_mapping",
    "get_thread_mapping",
    "get_thread_method_mapping",
    "get_rust_time_mapping",
    "get_rust_time_method_mapping",
    "get_rust_std_type",
    "is_rust_std_type",
    # Stub discovery (external crate packages)
    "get_stub_mapping",
    "get_stub_method_mapping",
    "get_stub_type_mapping",
    "get_stub_cargo_deps",
    "get_all_stub_packages",
    "get_crate_for_python_module",
    "get_stub_package_by_module",
    "clear_stub_cache",
]


def get_stdlib_mapping(module: str, func: str) -> StdlibMapping | None:
    """Get stdlib mapping for a module.function call.

    First checks built-in stdlib mappings, then falls back to
    any installed stub packages (e.g., spicycrab-clap).
    """
    key = f"{module}.{func}"

    # Check each built-in mapping dict
    if key in OS_MAPPINGS:
        return OS_MAPPINGS[key]
    if key in SYS_MAPPINGS:
        return SYS_MAPPINGS[key]
    if key in JSON_MAPPINGS:
        return JSON_MAPPINGS[key]
    if key in GLOB_MAPPINGS:
        return GLOB_MAPPINGS[key]
    if key in TEMPFILE_MAPPINGS:
        return TEMPFILE_MAPPINGS[key]
    if key in SUBPROCESS_MAPPINGS:
        return SUBPROCESS_MAPPINGS[key]
    if key in SHUTIL_MAPPINGS:
        return SHUTIL_MAPPINGS[key]
    if key in RANDOM_MAPPINGS:
        return RANDOM_MAPPINGS[key]
    if key in COLLECTIONS_MAPPINGS:
        return COLLECTIONS_MAPPINGS[key]
    if key in LOGGING_MAPPINGS:
        return LOGGING_MAPPINGS[key]
    if key in TIME_MAPPINGS:
        return TIME_MAPPINGS[key]
    if key in ALL_DATETIME_MAPPINGS:
        return ALL_DATETIME_MAPPINGS[key]
    # Rust std module mappings
    if key in FS_MAPPINGS:
        return FS_MAPPINGS[key]
    if key in IO_MAPPINGS:
        return IO_MAPPINGS[key]
    if key in PATH_MAPPINGS:
        return PATH_MAPPINGS[key]
    if key in SYNC_MAPPINGS:
        return SYNC_MAPPINGS[key]
    if key in THREAD_MAPPINGS:
        return THREAD_MAPPINGS[key]
    if key in RUST_TIME_MAPPINGS:
        return RUST_TIME_MAPPINGS[key]

    # Fallback to installed stub packages
    return get_stub_mapping(key)
