"""Mappings for Python logging module to Rust log crate."""

from __future__ import annotations

from spicycrab.codegen.stdlib.types import StdlibMapping

# logging module mappings
# Maps Python logging to Rust's log crate with env_logger for initialization
LOGGING_MAPPINGS: dict[str, StdlibMapping] = {
    # Basic logging functions
    "logging.debug": StdlibMapping(
        python_module="logging",
        python_func="debug",
        rust_code='log::debug!("{}", {args})',
        rust_imports=[],
        cargo_deps=["log", "env_logger"],
    ),
    "logging.info": StdlibMapping(
        python_module="logging",
        python_func="info",
        rust_code='log::info!("{}", {args})',
        rust_imports=[],
        cargo_deps=["log", "env_logger"],
    ),
    "logging.warning": StdlibMapping(
        python_module="logging",
        python_func="warning",
        rust_code='log::warn!("{}", {args})',
        rust_imports=[],
        cargo_deps=["log", "env_logger"],
    ),
    "logging.warn": StdlibMapping(
        python_module="logging",
        python_func="warn",
        rust_code='log::warn!("{}", {args})',
        rust_imports=[],
        cargo_deps=["log", "env_logger"],
    ),
    "logging.error": StdlibMapping(
        python_module="logging",
        python_func="error",
        rust_code='log::error!("{}", {args})',
        rust_imports=[],
        cargo_deps=["log", "env_logger"],
    ),
    "logging.critical": StdlibMapping(
        python_module="logging",
        python_func="critical",
        rust_code='log::error!("{}", {args})',  # Rust log doesn't have critical, use error
        rust_imports=[],
        cargo_deps=["log", "env_logger"],
    ),
    "logging.exception": StdlibMapping(
        python_module="logging",
        python_func="exception",
        rust_code='log::error!("{}", {args})',  # Maps to error level
        rust_imports=[],
        cargo_deps=["log", "env_logger"],
    ),
    # Configuration
    "logging.basicConfig": StdlibMapping(
        python_module="logging",
        python_func="basicConfig",
        rust_code="env_logger::init()",
        rust_imports=[],
        cargo_deps=["log", "env_logger"],
    ),
    # Level constants (for use in setLevel, etc.)
    "logging.DEBUG": StdlibMapping(
        python_module="logging",
        python_func="DEBUG",
        rust_code="log::LevelFilter::Debug",
        rust_imports=[],
        cargo_deps=["log"],
    ),
    "logging.INFO": StdlibMapping(
        python_module="logging",
        python_func="INFO",
        rust_code="log::LevelFilter::Info",
        rust_imports=[],
        cargo_deps=["log"],
    ),
    "logging.WARNING": StdlibMapping(
        python_module="logging",
        python_func="WARNING",
        rust_code="log::LevelFilter::Warn",
        rust_imports=[],
        cargo_deps=["log"],
    ),
    "logging.ERROR": StdlibMapping(
        python_module="logging",
        python_func="ERROR",
        rust_code="log::LevelFilter::Error",
        rust_imports=[],
        cargo_deps=["log"],
    ),
    "logging.CRITICAL": StdlibMapping(
        python_module="logging",
        python_func="CRITICAL",
        rust_code="log::LevelFilter::Error",  # No critical in Rust, use Error
        rust_imports=[],
        cargo_deps=["log"],
    ),
}


def get_logging_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a logging module function."""
    return LOGGING_MAPPINGS.get(func_name)
