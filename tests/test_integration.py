"""Integration tests that compile and run generated Rust code."""

import subprocess
import tempfile
import shutil
from pathlib import Path

import pytest

from spicycrab.parser import parse_file
from spicycrab.analyzer.type_resolver import resolve_types
from spicycrab.codegen.emitter import RustEmitter
from spicycrab.codegen.cargo import generate_cargo_toml


def transpile_and_run(python_code: str, expected_output: str | list[str]) -> None:
    """Transpile Python code to Rust, compile, run, and verify output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Write Python code to temp file
        py_file = tmpdir / "test_code.py"
        py_file.write_text(python_code)

        # Parse and transpile
        ir_module = parse_file(py_file)
        resolver = resolve_types(ir_module)
        emitter = RustEmitter(resolver)
        rust_code = emitter.emit_module(ir_module)

        # Create Rust project structure
        src_dir = tmpdir / "src"
        src_dir.mkdir()

        main_rs = src_dir / "main.rs"
        main_rs.write_text(rust_code)

        # Generate Cargo.toml
        # Check if serde_json is needed (for Any type)
        uses_serde_json = "serde_json" in resolver.imports
        cargo_toml = tmpdir / "Cargo.toml"
        cargo_content = generate_cargo_toml(
            name="test_code", modules=[ir_module], uses_serde_json=uses_serde_json
        )
        cargo_toml.write_text(cargo_content)

        # Build
        result = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Cargo build failed:\n{result.stderr}"

        # Run
        result = subprocess.run(
            ["cargo", "run", "--release", "-q"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Cargo run failed:\n{result.stderr}"

        # Verify output
        actual_output = result.stdout.strip()
        if isinstance(expected_output, list):
            actual_lines = actual_output.split('\n')
            for expected, actual in zip(expected_output, actual_lines):
                assert expected == actual, f"Expected '{expected}', got '{actual}'"
        else:
            assert actual_output == expected_output, f"Expected '{expected_output}', got '{actual_output}'"


@pytest.fixture(scope="module")
def check_cargo():
    """Check if cargo is available."""
    if shutil.which("cargo") is None:
        pytest.skip("cargo not found, skipping integration tests")


class TestBasicTranspilation:
    """Test basic Python to Rust transpilation."""

    def test_hello_world(self, check_cargo):
        """Test simple print statement."""
        code = '''
def main() -> None:
    print("Hello, World!")
'''
        transpile_and_run(code, "Hello, World!")

    def test_arithmetic(self, check_cargo):
        """Test arithmetic operations."""
        code = '''
def main() -> None:
    x: int = 10
    y: int = 3
    print(x + y)
    print(x - y)
    print(x * y)
    print(x // y)
'''
        transpile_and_run(code, ["13", "7", "30", "3"])

    def test_function_call(self, check_cargo):
        """Test function definition and call."""
        code = '''
def add(a: int, b: int) -> int:
    return a + b

def main() -> None:
    result: int = add(5, 7)
    print(result)
'''
        transpile_and_run(code, "12")

    def test_if_else(self, check_cargo):
        """Test if/else control flow."""
        code = '''
def check(x: int) -> str:
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"

def main() -> None:
    print(check(5))
    print(check(-3))
    print(check(0))
'''
        transpile_and_run(code, ["positive", "negative", "zero"])

    def test_for_loop(self, check_cargo):
        """Test for loop."""
        code = '''
def main() -> None:
    total: int = 0
    for i in range(5):
        total = total + i
    print(total)
'''
        transpile_and_run(code, "10")

    def test_while_loop(self, check_cargo):
        """Test while loop."""
        code = '''
def main() -> None:
    x: int = 0
    while x < 5:
        x = x + 1
    print(x)
'''
        transpile_and_run(code, "5")


class TestClassTranspilation:
    """Test class transpilation."""

    def test_simple_class(self, check_cargo):
        """Test simple class with methods."""
        code = '''
class Counter:
    def __init__(self, start: int) -> None:
        self.value = start

    def increment(self) -> None:
        self.value = self.value + 1

    def get(self) -> int:
        return self.value

def main() -> None:
    c: Counter = Counter(10)
    c.increment()
    c.increment()
    print(c.get())
'''
        transpile_and_run(code, "12")

    def test_dataclass(self, check_cargo):
        """Test dataclass transpilation."""
        code = '''
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

def main() -> None:
    p: Point = Point(3, 4)
    print(p.x)
    print(p.y)
'''
        transpile_and_run(code, ["3", "4"])


class TestContextManagers:
    """Test context manager transpilation."""

    def test_context_manager_basic(self, check_cargo):
        """Test basic context manager (RAII pattern)."""
        code = '''
class Resource:
    def __init__(self, name: str) -> None:
        self.name = name

    def __enter__(self) -> object:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    def use(self) -> None:
        print(self.name)

def main() -> None:
    with Resource("test") as r:
        r.use()
'''
        transpile_and_run(code, "test")


class TestStdlibOS:
    """Test os module transpilation."""

    def test_os_getcwd(self, check_cargo):
        """Test os.getcwd() transpilation."""
        code = '''
import os

def main() -> None:
    cwd: str = os.getcwd()
    # Just verify it returns a non-empty string
    if len(cwd) > 0:
        print("ok")
    else:
        print("fail")
'''
        transpile_and_run(code, "ok")

    def test_os_path_exists(self, check_cargo):
        """Test os.path.exists() transpilation."""
        code = '''
import os

def main() -> None:
    # /tmp should exist on most systems
    exists: bool = os.path.exists("/tmp")
    if exists:
        print("exists")
    else:
        print("not exists")
'''
        transpile_and_run(code, "exists")

    def test_os_path_isdir(self, check_cargo):
        """Test os.path.isdir() transpilation."""
        code = '''
import os

def main() -> None:
    is_dir: bool = os.path.isdir("/tmp")
    if is_dir:
        print("is_dir")
    else:
        print("not_dir")
'''
        transpile_and_run(code, "is_dir")


class TestStdlibSys:
    """Test sys module transpilation."""

    def test_sys_argv(self, check_cargo):
        """Test sys.argv transpilation."""
        code = '''
import sys

def main() -> None:
    args: list[str] = sys.argv
    # At minimum, argv[0] is the program name
    if len(args) >= 1:
        print("ok")
    else:
        print("fail")
'''
        transpile_and_run(code, "ok")


class TestStdlibPathlib:
    """Test pathlib module transpilation."""

    def test_path_exists(self, check_cargo):
        """Test Path.exists() transpilation."""
        code = '''
from pathlib import Path

def main() -> None:
    p: Path = Path("/tmp")
    if p.exists():
        print("exists")
    else:
        print("not exists")
'''
        transpile_and_run(code, "exists")

    def test_path_is_dir(self, check_cargo):
        """Test Path.is_dir() transpilation."""
        code = '''
from pathlib import Path

def main() -> None:
    p: Path = Path("/tmp")
    if p.is_dir():
        print("is_dir")
    else:
        print("not_dir")
'''
        transpile_and_run(code, "is_dir")


class TestListOperations:
    """Test list operations."""

    def test_list_creation_and_len(self, check_cargo):
        """Test list creation and len()."""
        code = '''
def main() -> None:
    items: list[int] = [1, 2, 3, 4, 5]
    print(len(items))
'''
        transpile_and_run(code, "5")

    def test_list_append(self, check_cargo):
        """Test list append."""
        code = '''
def main() -> None:
    items: list[int] = []
    items.append(1)
    items.append(2)
    items.append(3)
    print(len(items))
'''
        transpile_and_run(code, "3")


class TestStringOperations:
    """Test string operations."""

    def test_string_upper(self, check_cargo):
        """Test string upper()."""
        code = '''
def main() -> None:
    s: str = "hello"
    print(s.upper())
'''
        transpile_and_run(code, "HELLO")

    def test_string_lower(self, check_cargo):
        """Test string lower()."""
        code = '''
def main() -> None:
    s: str = "HELLO"
    print(s.lower())
'''
        transpile_and_run(code, "hello")

    def test_string_replace(self, check_cargo):
        """Test string replace()."""
        code = '''
def main() -> None:
    s: str = "hello world"
    print(s.replace("world", "rust"))
'''
        transpile_and_run(code, "hello rust")


class TestErrorHandling:
    """Test Result type and error handling transpilation."""

    def test_result_type_ok(self, check_cargo):
        """Test function returning Result with Ok."""
        code = '''
def parse_positive(s: str) -> Result[int, str]:
    if s.isdigit():
        return Ok(int(s))
    return Err("not a number")

def main() -> None:
    result: Result[int, str] = parse_positive("42")
    print("done")
'''
        transpile_and_run(code, "done")

    def test_question_mark_operator(self, check_cargo):
        """Test ? operator for error propagation."""
        code = '''
def might_fail(x: int) -> Result[int, str]:
    if x < 0:
        return Err("negative")
    return Ok(x * 2)

def caller() -> Result[int, str]:
    # This should use ? operator
    value: int = might_fail(5)
    return Ok(value + 1)

def main() -> None:
    # Call the function and check result
    result: Result[int, str] = caller()
    print("ok")
'''
        transpile_and_run(code, "ok")

    def test_raise_becomes_err(self, check_cargo):
        """Test that raise translates to return Err."""
        code = '''
def validate(x: int) -> Result[int, str]:
    if x < 0:
        raise ValueError("must be positive")
    return Ok(x)

def main() -> None:
    result: Result[int, str] = validate(10)
    print("validated")
'''
        transpile_and_run(code, "validated")


class TestMainFunction:
    """Test that def main() generates a binary executable."""

    def test_main_function_generates_binary(self, check_cargo):
        """Test that a file with main() compiles and runs as binary."""
        code = '''
def add(a: int, b: int) -> int:
    return a + b

def main() -> None:
    result: int = add(2, 3)
    print(result)
'''
        transpile_and_run(code, "5")

    def test_main_with_args_and_return(self, check_cargo):
        """Test main with complex operations."""
        code = '''
def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def main() -> None:
    print(factorial(5))
'''
        transpile_and_run(code, "120")

    def test_main_with_list_operations(self, check_cargo):
        """Test main with list operations."""
        code = '''
def sum_list(items: list[int]) -> int:
    total: int = 0
    for item in items:
        total = total + item
    return total

def main() -> None:
    numbers: list[int] = [1, 2, 3, 4, 5]
    print(sum_list(numbers))
'''
        transpile_and_run(code, "15")

    def test_main_with_class_annotated_init(self, check_cargo):
        """Test main with class using annotated self.attr: Type = value in __init__."""
        code = '''
class Counter:
    def __init__(self, value: int) -> None:
        self.value: int = value

    def get(self) -> int:
        return self.value

def main() -> None:
    c: Counter = Counter(42)
    print(c.get())
'''
        transpile_and_run(code, "42")


class TestAnyType:
    """Test Any type mapping to serde_json::Value."""

    def test_dict_str_any_empty(self, check_cargo):
        """Test dict[str, Any] type with empty dict."""
        code = '''
from typing import Any

def main() -> None:
    data: dict[str, Any] = {}
    print("created dict")
'''
        transpile_and_run(code, "created dict")

    def test_dict_str_any_len(self, check_cargo):
        """Test dict[str, Any] length check."""
        code = '''
from typing import Any

def check_empty(data: dict[str, Any]) -> bool:
    return len(data) == 0

def main() -> None:
    data: dict[str, Any] = {}
    if check_empty(data):
        print("empty")
'''
        transpile_and_run(code, "empty")


class TestSysModule:
    """Test sys module functionality."""

    def test_sys_platform(self, check_cargo):
        """Test sys.platform returns a platform string."""
        code = '''
import sys

def main() -> None:
    platform: str = sys.platform
    if len(platform) > 0:
        print("has platform")
'''
        transpile_and_run(code, "has platform")

    def test_sys_exit_zero(self, check_cargo):
        """Test sys.exit(0) exits successfully."""
        code = '''
import sys

def main() -> None:
    print("before exit")
    sys.exit(0)
'''
        # Note: exit(0) means success, program terminates before any further output
        transpile_and_run(code, "before exit")
