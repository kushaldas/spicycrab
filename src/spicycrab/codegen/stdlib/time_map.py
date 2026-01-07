"""Mappings for Python time and datetime modules to Rust chrono."""

from __future__ import annotations

from spicycrab.codegen.stdlib.types import StdlibMapping

# time module mappings (Python's time module -> std::time)
TIME_MAPPINGS: dict[str, StdlibMapping] = {
    "time.time": StdlibMapping(
        python_module="time",
        python_func="time",
        rust_code="std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs_f64()",
        rust_imports=[],
    ),
    "time.sleep": StdlibMapping(
        python_module="time",
        python_func="sleep",
        rust_code="std::thread::sleep(std::time::Duration::from_secs_f64({args}))",
        rust_imports=[],
    ),
    "time.monotonic": StdlibMapping(
        python_module="time",
        python_func="monotonic",
        rust_code="std::time::Instant::now().elapsed().as_secs_f64()",
        rust_imports=[],
    ),
}

# =============================================================================
# timedelta class mappings
# =============================================================================

TIMEDELTA_MAPPINGS: dict[str, StdlibMapping] = {
    # Constructor: timedelta(days=0, seconds=0, microseconds=0, ...)
    # We handle this specially in the emitter for keyword args
    "datetime.timedelta": StdlibMapping(
        python_module="datetime",
        python_func="timedelta",
        rust_code=(
            "chrono::Duration::days({days}) + chrono::Duration::seconds({seconds}) "
            "+ chrono::Duration::microseconds({microseconds})"
        ),
        rust_imports=[],
    ),
}

TIMEDELTA_METHOD_MAPPINGS: dict[str, StdlibMapping] = {
    "timedelta.days": StdlibMapping(
        python_module="datetime",
        python_func="days",
        rust_code="{self}.num_days() as i64",
        rust_imports=[],
    ),
    "timedelta.seconds": StdlibMapping(
        python_module="datetime",
        python_func="seconds",
        rust_code="({self}.num_seconds() % 86400) as i64",
        rust_imports=[],
    ),
    "timedelta.microseconds": StdlibMapping(
        python_module="datetime",
        python_func="microseconds",
        rust_code="({self}.num_microseconds().unwrap_or(0) % 1_000_000) as i64",
        rust_imports=[],
    ),
    "timedelta.total_seconds": StdlibMapping(
        python_module="datetime",
        python_func="total_seconds",
        rust_code="{self}.num_seconds() as f64 + ({self}.num_milliseconds() % 1000) as f64 / 1000.0",
        rust_imports=[],
    ),
}

# =============================================================================
# date class mappings
# =============================================================================

DATE_MAPPINGS: dict[str, StdlibMapping] = {
    # Constructor: date(year, month, day)
    "datetime.date": StdlibMapping(
        python_module="datetime",
        python_func="date",
        rust_code="chrono::NaiveDate::from_ymd_opt({args}).unwrap()",
        rust_imports=["chrono::Datelike"],
    ),
    "datetime.date.today": StdlibMapping(
        python_module="datetime",
        python_func="today",
        rust_code="chrono::Local::now().date_naive()",
        rust_imports=["chrono::Datelike"],
    ),
    "datetime.date.fromtimestamp": StdlibMapping(
        python_module="datetime",
        python_func="fromtimestamp",
        rust_code="chrono::DateTime::from_timestamp({args} as i64, 0).unwrap().date_naive()",
        rust_imports=["chrono::Datelike"],
    ),
    "datetime.date.fromordinal": StdlibMapping(
        python_module="datetime",
        python_func="fromordinal",
        rust_code="chrono::NaiveDate::from_num_days_from_ce_opt({args}).unwrap()",
        rust_imports=["chrono::Datelike"],
    ),
    "datetime.date.fromisoformat": StdlibMapping(
        python_module="datetime",
        python_func="fromisoformat",
        rust_code='chrono::NaiveDate::parse_from_str(&{args}, "%Y-%m-%d").unwrap()',
        rust_imports=["chrono::Datelike"],
    ),
    "datetime.date.fromisocalendar": StdlibMapping(
        python_module="datetime",
        python_func="fromisocalendar",
        rust_code="chrono::NaiveDate::from_isoywd_opt({args}).unwrap()",
        rust_imports=["chrono::Datelike"],
    ),
}

DATE_METHOD_MAPPINGS: dict[str, StdlibMapping] = {
    "date.year": StdlibMapping(
        python_module="datetime",
        python_func="year",
        rust_code="{self}.year() as i64",
        rust_imports=[],
    ),
    "date.month": StdlibMapping(
        python_module="datetime",
        python_func="month",
        rust_code="{self}.month() as i64",
        rust_imports=[],
    ),
    "date.day": StdlibMapping(
        python_module="datetime",
        python_func="day",
        rust_code="{self}.day() as i64",
        rust_imports=[],
    ),
    "date.weekday": StdlibMapping(
        python_module="datetime",
        python_func="weekday",
        rust_code="{self}.weekday().num_days_from_monday() as i64",
        rust_imports=[],
    ),
    "date.isoweekday": StdlibMapping(
        python_module="datetime",
        python_func="isoweekday",
        rust_code="{self}.weekday().number_from_monday() as i64",
        rust_imports=[],
    ),
    "date.isocalendar": StdlibMapping(
        python_module="datetime",
        python_func="isocalendar",
        rust_code="({self}.iso_week_date().0, {self}.iso_week_date().1, {self}.iso_week_date().2.number_from_monday())",
        rust_imports=[],
    ),
    "date.isoformat": StdlibMapping(
        python_module="datetime",
        python_func="isoformat",
        rust_code='{self}.format("%Y-%m-%d").to_string()',
        rust_imports=[],
    ),
    "date.ctime": StdlibMapping(
        python_module="datetime",
        python_func="ctime",
        rust_code='{self}.format("%a %b %e 00:00:00 %Y").to_string()',
        rust_imports=[],
    ),
    "date.strftime": StdlibMapping(
        python_module="datetime",
        python_func="strftime",
        rust_code="{self}.format({args}).to_string()",
        rust_imports=[],
    ),
    "date.toordinal": StdlibMapping(
        python_module="datetime",
        python_func="toordinal",
        rust_code="{self}.num_days_from_ce()",
        rust_imports=[],
    ),
    "date.replace": StdlibMapping(
        python_module="datetime",
        python_func="replace",
        # This needs special handling in emitter for keyword args
        rust_code="{self}.with_year({year}).unwrap().with_month({month}).unwrap().with_day({day}).unwrap()",
        rust_imports=[],
    ),
}

# =============================================================================
# datetime.time class mappings (not the time module!)
# =============================================================================

TIME_CLASS_MAPPINGS: dict[str, StdlibMapping] = {
    # Constructor: time(hour=0, minute=0, second=0, microsecond=0)
    "datetime.time": StdlibMapping(
        python_module="datetime",
        python_func="time",
        rust_code="chrono::NaiveTime::from_hms_micro_opt({args}).unwrap()",
        rust_imports=[],
    ),
    "datetime.time.fromisoformat": StdlibMapping(
        python_module="datetime",
        python_func="fromisoformat",
        rust_code='chrono::NaiveTime::parse_from_str({args}, "%H:%M:%S").unwrap()',
        rust_imports=[],
    ),
}

TIME_CLASS_METHOD_MAPPINGS: dict[str, StdlibMapping] = {
    "time.hour": StdlibMapping(
        python_module="datetime",
        python_func="hour",
        rust_code="{self}.hour()",
        rust_imports=[],
    ),
    "time.minute": StdlibMapping(
        python_module="datetime",
        python_func="minute",
        rust_code="{self}.minute()",
        rust_imports=[],
    ),
    "time.second": StdlibMapping(
        python_module="datetime",
        python_func="second",
        rust_code="{self}.second()",
        rust_imports=[],
    ),
    "time.microsecond": StdlibMapping(
        python_module="datetime",
        python_func="microsecond",
        rust_code="{self}.nanosecond() / 1000",
        rust_imports=[],
    ),
    "time.isoformat": StdlibMapping(
        python_module="datetime",
        python_func="isoformat",
        rust_code='{self}.format("%H:%M:%S").to_string()',
        rust_imports=[],
    ),
    "time.strftime": StdlibMapping(
        python_module="datetime",
        python_func="strftime",
        rust_code="{self}.format({args}).to_string()",
        rust_imports=[],
    ),
    "time.replace": StdlibMapping(
        python_module="datetime",
        python_func="replace",
        rust_code="chrono::NaiveTime::from_hms_micro_opt({hour}, {minute}, {second}, {microsecond}).unwrap()",
        rust_imports=[],
    ),
}

# =============================================================================
# datetime.datetime class mappings
# =============================================================================

DATETIME_MAPPINGS: dict[str, StdlibMapping] = {
    # Constructor: datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0)
    "datetime.datetime": StdlibMapping(
        python_module="datetime",
        python_func="datetime",
        rust_code=(
            "chrono::NaiveDate::from_ymd_opt({year}, {month}, {day}).unwrap()"
            ".and_hms_micro_opt({hour}, {minute}, {second}, {microsecond}).unwrap()"
        ),
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
    "datetime.datetime.now": StdlibMapping(
        python_module="datetime",
        python_func="now",
        rust_code="chrono::Local::now()",
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
    "datetime.datetime.utcnow": StdlibMapping(
        python_module="datetime",
        python_func="utcnow",
        rust_code="chrono::Utc::now()",
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
    "datetime.datetime.today": StdlibMapping(
        python_module="datetime",
        python_func="today",
        rust_code="chrono::Local::now().naive_local()",
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
    "datetime.datetime.fromtimestamp": StdlibMapping(
        python_module="datetime",
        python_func="fromtimestamp",
        rust_code="chrono::DateTime::from_timestamp({args} as i64, 0).unwrap().naive_local()",
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
    "datetime.datetime.utcfromtimestamp": StdlibMapping(
        python_module="datetime",
        python_func="utcfromtimestamp",
        rust_code="chrono::DateTime::from_timestamp({args} as i64, 0).unwrap().naive_utc()",
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
    "datetime.datetime.fromordinal": StdlibMapping(
        python_module="datetime",
        python_func="fromordinal",
        rust_code="chrono::NaiveDate::from_num_days_from_ce_opt({args}).unwrap().and_hms_opt(0, 0, 0).unwrap()",
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
    "datetime.datetime.fromisoformat": StdlibMapping(
        python_module="datetime",
        python_func="fromisoformat",
        rust_code=(
            'chrono::NaiveDateTime::parse_from_str(&{args}, "%Y-%m-%dT%H:%M:%S")'
            '.or_else(|_| chrono::NaiveDateTime::parse_from_str(&{args}, "%Y-%m-%d %H:%M:%S"))'
            ".or_else(|_| chrono::NaiveDateTime::parse_from_str("
            '&format!("{{}}T00:00:00", {args}), "%Y-%m-%dT%H:%M:%S")).unwrap()'
        ),
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
    "datetime.datetime.combine": StdlibMapping(
        python_module="datetime",
        python_func="combine",
        rust_code="chrono::NaiveDateTime::new({date}, {time})",
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
    "datetime.datetime.strptime": StdlibMapping(
        python_module="datetime",
        python_func="strptime",
        rust_code="chrono::NaiveDateTime::parse_from_str(&{args}).unwrap()",
        rust_imports=["chrono::Datelike", "chrono::Timelike"],
    ),
}

# datetime instance method mappings (called on datetime objects)
DATETIME_METHOD_MAPPINGS: dict[str, StdlibMapping] = {
    "datetime.year": StdlibMapping(
        python_module="datetime",
        python_func="year",
        rust_code="{self}.year() as i64",
        rust_imports=[],
    ),
    "datetime.month": StdlibMapping(
        python_module="datetime",
        python_func="month",
        rust_code="{self}.month() as i64",
        rust_imports=[],
    ),
    "datetime.day": StdlibMapping(
        python_module="datetime",
        python_func="day",
        rust_code="{self}.day() as i64",
        rust_imports=[],
    ),
    "datetime.hour": StdlibMapping(
        python_module="datetime",
        python_func="hour",
        rust_code="{self}.hour() as i64",
        rust_imports=[],
    ),
    "datetime.minute": StdlibMapping(
        python_module="datetime",
        python_func="minute",
        rust_code="{self}.minute() as i64",
        rust_imports=[],
    ),
    "datetime.second": StdlibMapping(
        python_module="datetime",
        python_func="second",
        rust_code="{self}.second() as i64",
        rust_imports=[],
    ),
    "datetime.microsecond": StdlibMapping(
        python_module="datetime",
        python_func="microsecond",
        rust_code="({self}.nanosecond() / 1000) as i64",
        rust_imports=[],
    ),
    "datetime.weekday": StdlibMapping(
        python_module="datetime",
        python_func="weekday",
        rust_code="{self}.weekday().num_days_from_monday() as i64",
        rust_imports=[],
    ),
    "datetime.isoweekday": StdlibMapping(
        python_module="datetime",
        python_func="isoweekday",
        rust_code="{self}.weekday().number_from_monday() as i64",
        rust_imports=[],
    ),
    "datetime.isocalendar": StdlibMapping(
        python_module="datetime",
        python_func="isocalendar",
        rust_code="({self}.iso_week_date().0, {self}.iso_week_date().1, {self}.iso_week_date().2.number_from_monday())",
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
    "datetime.timestamp": StdlibMapping(
        python_module="datetime",
        python_func="timestamp",
        rust_code="{self}.and_utc().timestamp() as f64",
        rust_imports=[],
    ),
    "datetime.isoformat": StdlibMapping(
        python_module="datetime",
        python_func="isoformat",
        rust_code='{self}.format("%Y-%m-%dT%H:%M:%S").to_string()',
        rust_imports=[],
    ),
    "datetime.ctime": StdlibMapping(
        python_module="datetime",
        python_func="ctime",
        rust_code='{self}.format("%a %b %e %H:%M:%S %Y").to_string()',
        rust_imports=[],
    ),
    "datetime.strftime": StdlibMapping(
        python_module="datetime",
        python_func="strftime",
        rust_code="{self}.format({args}).to_string()",
        rust_imports=[],
    ),
    "datetime.toordinal": StdlibMapping(
        python_module="datetime",
        python_func="toordinal",
        rust_code="{self}.date().num_days_from_ce()",
        rust_imports=[],
    ),
    "datetime.replace": StdlibMapping(
        python_module="datetime",
        python_func="replace",
        # Needs special handling for keyword args
        rust_code=(
            "chrono::NaiveDate::from_ymd_opt({year}, {month}, {day}).unwrap()"
            ".and_hms_micro_opt({hour}, {minute}, {second}, {microsecond}).unwrap()"
        ),
        rust_imports=[],
    ),
}

# =============================================================================
# timezone class mappings
# =============================================================================

TIMEZONE_MAPPINGS: dict[str, StdlibMapping] = {
    "datetime.timezone": StdlibMapping(
        python_module="datetime",
        python_func="timezone",
        rust_code="chrono::FixedOffset::east_opt(({args}).num_seconds() as i32).unwrap()",
        rust_imports=[],
    ),
    "datetime.timezone.utc": StdlibMapping(
        python_module="datetime",
        python_func="utc",
        rust_code="chrono::Utc",
        rust_imports=[],
    ),
}


# =============================================================================
# Lookup functions
# =============================================================================


def get_time_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a time module function."""
    return TIME_MAPPINGS.get(func_name)


def get_datetime_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a datetime module class/function."""
    # Check all datetime-related mappings
    if func_name in DATETIME_MAPPINGS:
        return DATETIME_MAPPINGS[func_name]
    if func_name in DATE_MAPPINGS:
        return DATE_MAPPINGS[func_name]
    if func_name in TIME_CLASS_MAPPINGS:
        return TIME_CLASS_MAPPINGS[func_name]
    if func_name in TIMEDELTA_MAPPINGS:
        return TIMEDELTA_MAPPINGS[func_name]
    if func_name in TIMEZONE_MAPPINGS:
        return TIMEZONE_MAPPINGS[func_name]
    return None


def get_datetime_method_mapping(method_name: str) -> StdlibMapping | None:
    """Get mapping for a datetime/date/time/timedelta method."""
    if method_name in DATETIME_METHOD_MAPPINGS:
        return DATETIME_METHOD_MAPPINGS[method_name]
    if method_name in DATE_METHOD_MAPPINGS:
        return DATE_METHOD_MAPPINGS[method_name]
    if method_name in TIME_CLASS_METHOD_MAPPINGS:
        return TIME_CLASS_METHOD_MAPPINGS[method_name]
    if method_name in TIMEDELTA_METHOD_MAPPINGS:
        return TIMEDELTA_METHOD_MAPPINGS[method_name]
    return None


# Combined mappings for get_stdlib_mapping
ALL_DATETIME_MAPPINGS: dict[str, StdlibMapping] = {
    **DATETIME_MAPPINGS,
    **DATE_MAPPINGS,
    **TIME_CLASS_MAPPINGS,
    **TIMEDELTA_MAPPINGS,
    **TIMEZONE_MAPPINGS,
}
