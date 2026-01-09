"""Debug logging for spicycrab - completely optional, disabled by default.

This module provides a non-invasive logging system for tracking decisions
made during stub generation and transpilation. When disabled (the default),
all logging functions are no-ops with zero overhead.

Usage:
    # In CLI, enable logging:
    from spicycrab.debug_log import enable_logging, save_log
    enable_logging("transpile", "my_file")
    # ... do transpilation ...
    save_log(output_dir)

    # In any module, add log calls (no-ops when disabled):
    from spicycrab.debug_log import log_decision, increment
    log_decision("stub_lookup", key="chrono.Utc.now", found=True)
    increment("stub_hits")
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Global logger instance - None means logging is disabled
_logger: SpicycrabLogger | None = None


def is_logging_enabled() -> bool:
    """Check if debug logging is enabled."""
    return _logger is not None


def enable_logging(operation: str, name: str) -> None:
    """Enable debug logging for this session.

    Args:
        operation: Type of operation ("transpile" or "stubs")
        name: Name identifier (e.g., source file stem or crate name)
    """
    global _logger
    _logger = SpicycrabLogger(operation, name)


def get_logger() -> SpicycrabLogger | None:
    """Get the current logger (None if disabled)."""
    return _logger


def log_decision(decision_type: str, **details: Any) -> None:
    """Log a decision - no-op if logging disabled.

    Args:
        decision_type: Category of decision (e.g., "stub_lookup", "type_resolution")
        **details: Key-value pairs describing the decision
    """
    if _logger:
        _logger.log_decision(decision_type, **details)


def increment(counter: str, amount: int = 1) -> None:
    """Increment a counter - no-op if logging disabled.

    Args:
        counter: Name of the counter (e.g., "stub_hits", "stub_misses")
        amount: Amount to increment by (default 1)
    """
    if _logger:
        _logger.increment(counter, amount)


def save_log(output_dir: Path) -> Path | None:
    """Save the log to disk.

    Args:
        output_dir: Directory where .spicycrab-logs/ will be created

    Returns:
        Path to the saved log file, or None if logging was disabled
    """
    if _logger:
        return _logger.save(output_dir)
    return None


def disable_logging() -> None:
    """Disable logging and clear the logger."""
    global _logger
    _logger = None


@dataclass
class SpicycrabLogger:
    """Debug logger that captures decisions for regression tracking.

    This logger collects:
    - Individual decisions with their details
    - Summary counters for quick comparison
    - Metadata about the operation
    """

    operation: str  # "transpile" or "stubs"
    name: str  # crate name or source file name
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    decisions: list[dict[str, Any]] = field(default_factory=list)
    _summary: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def log_decision(self, decision_type: str, **details: Any) -> None:
        """Record a decision with its details."""
        self.decisions.append({"type": decision_type, **details})

    def increment(self, counter: str, amount: int = 1) -> None:
        """Increment a summary counter."""
        self._summary[counter] += amount

    def save(self, output_dir: Path) -> Path:
        """Save the log to a JSON file.

        Creates .spicycrab-logs/<operation>/<name>_<timestamp>.json
        """
        log_dir = output_dir / ".spicycrab-logs" / self.operation
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"{self.name}_{timestamp}.json"
        log_path = log_dir / filename

        data = {
            "version": "1.0",
            "timestamp": self.timestamp,
            "operation": self.operation,
            "name": self.name,
            "summary": dict(self._summary),
            "decisions": self.decisions,
        }

        log_path.write_text(json.dumps(data, indent=2))
        return log_path
