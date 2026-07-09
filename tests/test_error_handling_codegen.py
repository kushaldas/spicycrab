"""Tests for Result-first error handling code generation."""

import pytest

from spicycrab.analyzer.type_resolver import resolve_types
from spicycrab.codegen.emitter import RustEmitter
from spicycrab.parser import parse_source
from spicycrab.utils.errors import CodegenError


def emit_rust(source: str) -> str:
    module = parse_source(source)
    return RustEmitter(resolve_types(module)).emit_module(module)


def test_try_except_assignment_lowers_remainder_into_ok_arm() -> None:
    rust_code = emit_rust(
        """
from spicycrab.types import Result, Ok, Err

def divide(a: int, b: int) -> Result[int, str]:
    if b == 0:
        return Err("division by zero")
    return Ok(a // b)

def safe_divide(a: int, b: int) -> int:
    try:
        result: int = divide(a, b)
        return result
    except Exception as e:
        print(f"Error: {e}")
        return 0
"""
    )

    assert "catch_unwind" not in rust_code
    assert "match divide(a, b)" in rust_code
    assert "Ok(result) => {" in rust_code
    assert "            result" in rust_code
    assert "Err(e) => {" in rust_code
    assert 'println!("{}", format!("Error: {}", e));' in rust_code


def test_try_except_in_result_context_matches_without_question_mark() -> None:
    rust_code = emit_rust(
        """
from spicycrab.types import Result, Ok, Err

def might_fail(flag: bool) -> Result[int, str]:
    if flag:
        return Ok(42)
    return Err("failed")

def recover(flag: bool) -> Result[int, str]:
    try:
        value: int = might_fail(flag)
        return Ok(value)
    except Exception as e:
        return Err(e)
"""
    )

    assert "match might_fail(flag)" in rust_code
    assert "match might_fail(flag)?" not in rust_code
    assert "            Err(e)" in rust_code


def test_try_else_runs_in_ok_arm() -> None:
    rust_code = emit_rust(
        """
from spicycrab.types import Result, Ok, Err

def might_fail(flag: bool) -> Result[int, str]:
    if flag:
        return Ok(42)
    return Err("failed")

def recover(flag: bool) -> Result[int, str]:
    try:
        value: int = might_fail(flag)
    except Exception as e:
        return Err(e)
    else:
        print("ok")
        return Ok(value)
"""
    )

    assert "Ok(value) => {" in rust_code
    assert 'println!("ok");' in rust_code
    assert "            Ok(value)" in rust_code


def test_try_except_requires_result_call() -> None:
    with pytest.raises(CodegenError, match="starts with a Result-returning call"):
        emit_rust(
            """
def main() -> None:
    try:
        print("not fallible")
    except Exception:
        print("handled")
"""
        )


def test_try_except_finally_rejected() -> None:
    with pytest.raises(CodegenError, match="try/except/finally is not supported"):
        emit_rust(
            """
from spicycrab.types import Result, Ok, Err

def might_fail() -> Result[int, str]:
    return Ok(1)

def main() -> None:
    try:
        value: int = might_fail()
        print(value)
    except Exception as e:
        print(e)
    finally:
        print("cleanup")
"""
        )
