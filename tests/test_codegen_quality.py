"""Tests for generated Rust quality improvements."""

from spicycrab.analyzer.type_resolver import resolve_types
from spicycrab.codegen.cargo import generate_cargo_toml
from spicycrab.codegen.emitter import RustEmitter
from spicycrab.parser import parse_source


def emit_rust(source: str) -> str:
    module = parse_source(source)
    return RustEmitter(resolve_types(module)).emit_module(module)


def test_consecutive_appends_emit_vec_literal() -> None:
    rust_code = emit_rust(
        """
def create_list() -> list[int]:
    items: list[int] = []
    items.append(1)
    items.append(2)
    items.append(3)
    return items
"""
    )

    assert "let items: Vec<i64> = vec![1, 2, 3];" in rust_code
    assert "let mut items: Vec<i64> = vec![];" not in rust_code
    assert "items.push(" not in rust_code


def test_vec_literal_remains_mutable_when_later_mutated() -> None:
    rust_code = emit_rust(
        """
def create_list() -> list[int]:
    items: list[int] = []
    items.append(1)
    print(len(items))
    items.append(2)
    return items
"""
    )

    assert "let mut items: Vec<i64> = vec![1];" in rust_code
    assert "items.push(2);" in rust_code
    assert "let mut items: Vec<i64> = vec![];" not in rust_code


def test_unused_single_assignment_gets_underscore_binding() -> None:
    rust_code = emit_rust(
        """
def main() -> None:
    unused_value: int = 42
    print("done")
"""
    )

    assert "let _unused_value: i64 = 42;" in rust_code
    assert "let unused_value: i64 = 42;" not in rust_code


def test_elif_condition_counts_as_variable_use() -> None:
    rust_code = emit_rust(
        """
def main() -> None:
    a: int | None = None
    b: int | None = 42
    if a is not None:
        print("a")
    elif b is not None:
        print("b")
"""
    )

    assert "let b: Option<i64> = Some(42);" in rust_code
    assert "let _b: Option<i64> = Some(42);" not in rust_code


def test_unused_vec_built_from_appends_gets_underscore_binding() -> None:
    rust_code = emit_rust(
        """
def main() -> None:
    items: list[int] = []
    items.append(1)
    items.append(2)
    print("done")
"""
    )

    assert "let _items: Vec<i64> = vec![1, 2];" in rust_code
    assert "items.push(" not in rust_code


def test_random_shuffle_marks_argument_mutable() -> None:
    rust_code = emit_rust(
        """
import random

def main() -> None:
    items: list[int] = [1, 2, 3]
    random.shuffle(items)
    print(len(items))
"""
    )

    assert "let mut items: Vec<i64> = vec![1, 2, 3];" in rust_code
    assert "items.shuffle(&mut rand::thread_rng());" in rust_code


def test_tail_if_returns_emit_branch_expressions() -> None:
    rust_code = emit_rust(
        """
def check(x: int) -> str:
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"
"""
    )

    assert 'return "positive".to_string();' not in rust_code
    assert 'return "negative".to_string();' not in rust_code
    assert 'return "zero".to_string();' not in rust_code
    assert '"positive".to_string()' in rust_code
    assert '"negative".to_string()' in rust_code
    assert '"zero".to_string()' in rust_code


def test_vec_init_then_push_allow_not_generated() -> None:
    module = parse_source(
        """
def main() -> None:
    pass
"""
    )
    cargo_toml = generate_cargo_toml("quality_check", modules=[module])

    assert 'vec_init_then_push = "allow"' not in cargo_toml
