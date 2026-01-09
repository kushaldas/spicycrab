"""Tests for the crabpy parser."""

import pytest

from spicycrab.parser import parse_source
from spicycrab.ir.nodes import (
    IRModule,
    IRFunction,
    IRClass,
    IRPrimitiveType,
    IRGenericType,
    PrimitiveType,
)
from spicycrab.utils.errors import TypeAnnotationError, UnsupportedFeatureError


class TestParseBasics:
    """Test basic parsing functionality."""

    def test_parse_empty_module(self) -> None:
        """Test parsing an empty module."""
        module = parse_source("")
        assert isinstance(module, IRModule)
        assert module.functions == []
        assert module.classes == []

    def test_parse_module_docstring(self) -> None:
        """Test parsing module docstring."""
        source = '"""This is a docstring."""'
        module = parse_source(source)
        assert module.docstring == "This is a docstring."

    def test_parse_simple_function(self) -> None:
        """Test parsing a simple typed function."""
        source = """
def add(a: int, b: int) -> int:
    return a + b
"""
        module = parse_source(source)
        assert len(module.functions) == 1

        func = module.functions[0]
        assert func.name == "add"
        assert len(func.params) == 2
        assert func.params[0].name == "a"
        assert func.params[1].name == "b"
        assert isinstance(func.return_type, IRPrimitiveType)
        assert func.return_type.kind == PrimitiveType.INT

    def test_parse_function_with_default_arg(self) -> None:
        """Test parsing a function with a default argument."""
        source = """
def greet(name: str, times: int = 1) -> str:
    return name
"""
        module = parse_source(source)
        func = module.functions[0]
        assert len(func.params) == 2
        assert func.params[1].default is not None

    def test_parse_generic_types(self) -> None:
        """Test parsing generic type annotations."""
        source = """
from typing import List, Dict, Optional

def process(items: List[int], mapping: Dict[str, int]) -> Optional[str]:
    return None
"""
        module = parse_source(source)
        func = module.functions[0]

        # Check List[int]
        param0_type = func.params[0].type
        assert isinstance(param0_type, IRGenericType)
        assert param0_type.name == "List"
        assert len(param0_type.type_args) == 1

        # Check Dict[str, int]
        param1_type = func.params[1].type
        assert isinstance(param1_type, IRGenericType)
        assert param1_type.name == "Dict"
        assert len(param1_type.type_args) == 2

        # Check Optional[str]
        return_type = func.return_type
        assert isinstance(return_type, IRGenericType)
        assert return_type.name == "Optional"

    def test_parse_user_defined_generic_types(self) -> None:
        """Test parsing user-defined generic types (e.g., Arc[str], Mutex[int]).

        User-defined or crate-specific generic types should preserve their type arguments,
        even if they are not in the standard GENERIC_TYPES set.
        """
        source = """
def use_arc(config: Arc[str]) -> None:
    pass

def use_mutex(counter: Arc[Mutex[int]]) -> None:
    pass
"""
        module = parse_source(source)

        # Check Arc[str] - should be IRGenericType with type arg preserved
        func1 = module.functions[0]
        param_type = func1.params[0].type
        assert isinstance(param_type, IRGenericType)
        assert param_type.name == "Arc"
        assert len(param_type.type_args) == 1
        inner_type = param_type.type_args[0]
        assert isinstance(inner_type, IRPrimitiveType)
        assert inner_type.kind == PrimitiveType.STR

        # Check Arc[Mutex[int]] - nested generic types
        func2 = module.functions[1]
        param_type = func2.params[0].type
        assert isinstance(param_type, IRGenericType)
        assert param_type.name == "Arc"
        assert len(param_type.type_args) == 1
        # Inner type should be Mutex[int]
        inner_type = param_type.type_args[0]
        assert isinstance(inner_type, IRGenericType)
        assert inner_type.name == "Mutex"
        assert len(inner_type.type_args) == 1
        # Innermost type should be int
        innermost_type = inner_type.type_args[0]
        assert isinstance(innermost_type, IRPrimitiveType)
        assert innermost_type.kind == PrimitiveType.INT


class TestParseClasses:
    """Test class parsing."""

    def test_parse_simple_class(self) -> None:
        """Test parsing a simple class."""
        source = """
class Counter:
    count: int

    def __init__(self, start: int) -> None:
        self.count = start
"""
        module = parse_source(source)
        assert len(module.classes) == 1

        cls = module.classes[0]
        assert cls.name == "Counter"
        assert len(cls.fields) == 1
        assert cls.fields[0][0] == "count"
        assert len(cls.methods) == 1
        assert cls.methods[0].name == "__init__"

    def test_parse_dataclass(self) -> None:
        """Test parsing a dataclass."""
        source = """
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
"""
        module = parse_source(source)
        cls = module.classes[0]
        assert cls.is_dataclass is True
        assert len(cls.fields) == 2

    def test_parse_context_manager_class(self) -> None:
        """Test parsing a class with context manager methods."""
        source = """
class Timer:
    def __enter__(self) -> None:
        pass

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass
"""
        module = parse_source(source)
        cls = module.classes[0]
        assert cls.has_enter is True
        assert cls.has_exit is True


class TestParseControlFlow:
    """Test control flow parsing."""

    def test_parse_if_statement(self) -> None:
        """Test parsing if statements."""
        source = """
def check(x: int) -> str:
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"
"""
        module = parse_source(source)
        func = module.functions[0]
        assert len(func.body) == 1  # One if statement

    def test_parse_for_loop(self) -> None:
        """Test parsing for loops."""
        source = """
def sum_list(items: list) -> int:
    total: int = 0
    for item in items:
        total += item
    return total
"""
        module = parse_source(source)
        func = module.functions[0]
        assert len(func.body) == 3  # assign, for, return

    def test_parse_while_loop(self) -> None:
        """Test parsing while loops."""
        source = """
def countdown(n: int) -> int:
    while n > 0:
        n -= 1
    return n
"""
        module = parse_source(source)
        func = module.functions[0]
        assert len(func.body) == 2  # while, return


class TestParseErrors:
    """Test error handling in parsing."""

    def test_missing_type_annotation(self) -> None:
        """Test that missing type annotations raise errors."""
        source = """
def add(a, b: int) -> int:
    return a + b
"""
        with pytest.raises(TypeAnnotationError):
            parse_source(source)

    def test_async_function_is_supported(self) -> None:
        """Test that async functions are correctly parsed."""
        source = """
async def fetch(url: str) -> str:
    return url
"""
        module = parse_source(source)
        assert len(module.functions) == 1
        func = module.functions[0]
        assert func.is_async is True
        assert func.name == "fetch"

    def test_unsupported_nested_function(self) -> None:
        """Test that nested functions raise errors."""
        source = """
def outer() -> int:
    def inner() -> int:
        return 1
    return inner()
"""
        with pytest.raises(UnsupportedFeatureError):
            parse_source(source)


class TestRustNativeTypes:
    """Test parsing of Rust native types from spicycrab.types."""

    def test_parse_unsigned_integers(self) -> None:
        """Test parsing unsigned integer types (u8, u16, u32, u64)."""
        source = """
from spicycrab.types import u8, u16, u32, u64

def add_bytes(a: u8, b: u8) -> u8:
    return a + b

def add_shorts(a: u16, b: u16) -> u16:
    return a + b

def add_ints(a: u32, b: u32) -> u32:
    return a + b

def add_longs(a: u64, b: u64) -> u64:
    return a + b
"""
        module = parse_source(source)
        assert len(module.functions) == 4

        # Check u8 function
        func = module.functions[0]
        assert func.name == "add_bytes"
        assert func.params[0].type.name == "u8"
        assert func.return_type.name == "u8"

    def test_parse_signed_integers(self) -> None:
        """Test parsing signed integer types (i8, i16, i32, i64)."""
        source = """
from spicycrab.types import i8, i16, i32, i64

def process(a: i32, b: i64) -> i32:
    return a
"""
        module = parse_source(source)
        func = module.functions[0]
        assert func.params[0].type.name == "i32"
        assert func.params[1].type.name == "i64"
        assert func.return_type.name == "i32"

    def test_parse_size_types(self) -> None:
        """Test parsing usize and isize types."""
        source = """
from spicycrab.types import usize, isize

def get_len(items: list[str]) -> usize:
    return len(items)

def get_offset(base: isize, delta: isize) -> isize:
    return base + delta
"""
        module = parse_source(source)
        assert module.functions[0].return_type.name == "usize"
        assert module.functions[1].return_type.name == "isize"

    def test_parse_float_types(self) -> None:
        """Test parsing f32 and f64 types."""
        source = """
from spicycrab.types import f32, f64

def compute_single(x: f32, y: f32) -> f32:
    return x * y

def compute_double(x: f64, y: f64) -> f64:
    return x * y
"""
        module = parse_source(source)
        assert module.functions[0].return_type.name == "f32"
        assert module.functions[1].return_type.name == "f64"

    def test_parse_mixed_types(self) -> None:
        """Test parsing mixed Rust native and Python types."""
        source = """
from spicycrab.types import u32, f64

def process(count: u32, values: list[f64]) -> int:
    return 0
"""
        module = parse_source(source)
        func = module.functions[0]
        assert func.params[0].type.name == "u32"
        # list[f64] should be a generic type
        assert func.params[1].type.name == "list"
        # return type is Python int -> will resolve to i64
        assert func.return_type.kind == PrimitiveType.INT
