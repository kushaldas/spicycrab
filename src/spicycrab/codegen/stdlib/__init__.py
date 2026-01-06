"""Standard library mappings from Python to Rust."""

from spicycrab.codegen.stdlib.collections_map import (
    COLLECTIONS_MAPPINGS,
    DEQUE_METHOD_MAPPINGS,
    get_collections_mapping,
    get_deque_method,
)
from spicycrab.codegen.stdlib.json_map import (
    JSON_MAPPINGS,
    get_json_mapping,
)
from spicycrab.codegen.stdlib.os_map import (
    OS_MAPPINGS,
    PATHLIB_MAPPINGS,
    SYS_MAPPINGS,
    StdlibMapping,
    get_os_mapping,
    get_pathlib_mapping,
    get_sys_mapping,
)
from spicycrab.codegen.stdlib.time_map import (
    TIME_MAPPINGS,
    DATETIME_MAPPINGS,
    DATE_MAPPINGS,
    TIME_CLASS_MAPPINGS,
    TIMEDELTA_MAPPINGS,
    TIMEZONE_MAPPINGS,
    DATETIME_METHOD_MAPPINGS,
    DATE_METHOD_MAPPINGS,
    TIME_CLASS_METHOD_MAPPINGS,
    TIMEDELTA_METHOD_MAPPINGS,
    ALL_DATETIME_MAPPINGS,
    get_time_mapping,
    get_datetime_mapping,
    get_datetime_method_mapping,
)

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
]


def get_stdlib_mapping(module: str, func: str) -> StdlibMapping | None:
    """Get stdlib mapping for a module.function call."""
    key = f"{module}.{func}"

    # Check each mapping dict
    if key in OS_MAPPINGS:
        return OS_MAPPINGS[key]
    if key in SYS_MAPPINGS:
        return SYS_MAPPINGS[key]
    if key in JSON_MAPPINGS:
        return JSON_MAPPINGS[key]
    if key in COLLECTIONS_MAPPINGS:
        return COLLECTIONS_MAPPINGS[key]
    if key in TIME_MAPPINGS:
        return TIME_MAPPINGS[key]
    if key in ALL_DATETIME_MAPPINGS:
        return ALL_DATETIME_MAPPINGS[key]

    return None
