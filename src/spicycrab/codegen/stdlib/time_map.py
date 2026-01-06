"""Mappings for Python time and datetime modules to Rust chrono."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class StdlibMapping:
    """A mapping from Python stdlib to Rust."""

    python_module: str
    python_func: str
    rust_code: str  # Template with {args} placeholder
    rust_imports: list[str]
    needs_result: bool = False  # Whether it returns Result


# time module mappings
TIME_MAPPINGS: dict[str, StdlibMapping] = {
    "time.time": StdlibMapping(
        python_module="time",
        python_func="time",
        rust_code="std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs_f64()",
        rust_imports=[],  # Using full paths
    ),
    "time.sleep": StdlibMapping(
        python_module="time",
        python_func="sleep",
        rust_code="std::thread::sleep(std::time::Duration::from_secs_f64({args}))",
        rust_imports=[],  # Using full paths
    ),
    "time.monotonic": StdlibMapping(
        python_module="time",
        python_func="monotonic",
        rust_code="std::time::Instant::now().elapsed().as_secs_f64()",
        rust_imports=[],
    ),
}

# datetime module mappings using chrono (full paths, no imports needed)
DATETIME_MAPPINGS: dict[str, StdlibMapping] = {
    "datetime.datetime.now": StdlibMapping(
        python_module="datetime",
        python_func="now",
        rust_code="chrono::Local::now()",
        rust_imports=[],  # Using full path
    ),
    "datetime.datetime.utcnow": StdlibMapping(
        python_module="datetime",
        python_func="utcnow",
        rust_code="chrono::Utc::now()",
        rust_imports=[],  # Using full path
    ),
    "datetime.date.today": StdlibMapping(
        python_module="datetime",
        python_func="today",
        rust_code="chrono::Local::now().date_naive()",
        rust_imports=[],  # Using full path
    ),
}

# datetime class method mappings (called on datetime objects)
# These are methods on chrono types, no imports needed (full paths used)
DATETIME_METHOD_MAPPINGS: dict[str, StdlibMapping] = {
    "datetime.strftime": StdlibMapping(
        python_module="datetime",
        python_func="strftime",
        rust_code="{self}.format({args}).to_string()",
        rust_imports=[],
    ),
    "datetime.timestamp": StdlibMapping(
        python_module="datetime",
        python_func="timestamp",
        rust_code="{self}.timestamp() as f64",
        rust_imports=[],
    ),
    "datetime.date": StdlibMapping(
        python_module="datetime",
        python_func="date",
        rust_code="{self}.date_naive()",
        rust_imports=[],
    ),
    "datetime.time": StdlibMapping(
        python_module="datetime",
        python_func="time",
        rust_code="{self}.time()",
        rust_imports=[],
    ),
    "datetime.year": StdlibMapping(
        python_module="datetime",
        python_func="year",
        rust_code="{self}.year()",
        rust_imports=[],
    ),
    "datetime.month": StdlibMapping(
        python_module="datetime",
        python_func="month",
        rust_code="{self}.month()",
        rust_imports=[],
    ),
    "datetime.day": StdlibMapping(
        python_module="datetime",
        python_func="day",
        rust_code="{self}.day()",
        rust_imports=[],
    ),
    "datetime.hour": StdlibMapping(
        python_module="datetime",
        python_func="hour",
        rust_code="{self}.hour()",
        rust_imports=[],
    ),
    "datetime.minute": StdlibMapping(
        python_module="datetime",
        python_func="minute",
        rust_code="{self}.minute()",
        rust_imports=[],
    ),
    "datetime.second": StdlibMapping(
        python_module="datetime",
        python_func="second",
        rust_code="{self}.second()",
        rust_imports=[],
    ),
    "datetime.weekday": StdlibMapping(
        python_module="datetime",
        python_func="weekday",
        rust_code="{self}.weekday().num_days_from_monday()",
        rust_imports=[],
    ),
    "datetime.isoformat": StdlibMapping(
        python_module="datetime",
        python_func="isoformat",
        rust_code="{self}.to_rfc3339()",
        rust_imports=[],
    ),
}


def get_time_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a time module function."""
    return TIME_MAPPINGS.get(func_name)


def get_datetime_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a datetime module function."""
    return DATETIME_MAPPINGS.get(func_name)


def get_datetime_method_mapping(method_name: str) -> StdlibMapping | None:
    """Get mapping for a datetime method."""
    return DATETIME_METHOD_MAPPINGS.get(method_name)
