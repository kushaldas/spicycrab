"""Compile/run tests for Result-first error handling."""

import shutil

import pytest
from test_integration import transpile_and_run


@pytest.fixture(scope="module")
def check_cargo() -> None:
    """Check if cargo is available."""
    if shutil.which("cargo") is None:
        pytest.skip("cargo not found, skipping integration tests")


def test_try_except_result_match(check_cargo: None) -> None:
    """Test try/except lowering around Result-returning calls."""
    code = """
def might_fail(flag: bool) -> Result[int, str]:
    if flag:
        return Ok(7)
    return Err("failed")

def safe_value(flag: bool) -> int:
    try:
        value: int = might_fail(flag)
        return value + 1
    except Exception as e:
        print(f"handled: {e}")
        return 0

def main() -> None:
    print(safe_value(True))
    print(safe_value(False))
"""
    transpile_and_run(code, ["8", "handled: failed", "0"])


def test_try_else_result_match(check_cargo: None) -> None:
    """Test try/else lowering into the Ok arm."""
    code = """
def might_fail(flag: bool) -> Result[int, str]:
    if flag:
        return Ok(7)
    return Err("failed")

def safe_value(flag: bool) -> Result[int, str]:
    try:
        value: int = might_fail(flag)
    except Exception as e:
        return Err(e)
    else:
        return Ok(value + 1)

def main() -> None:
    ok: Result[int, str] = safe_value(True)
    print(Result.unwrap(ok))
    err: Result[int, str] = safe_value(False)
    if Result.is_err(err):
        print("err")
"""
    transpile_and_run(code, ["8", "err"])
