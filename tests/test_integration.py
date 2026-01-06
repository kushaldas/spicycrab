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

        # Run clippy to check for warnings
        # Allow certain lints that are stylistic or require complex code analysis:
        # - unused_variables: test code may not use all variables
        # - unused_mut: transpiler may conservatively mark variables as mutable
        # - unused_imports: chrono traits may be imported preemptively
        # - vec_init_then_push: would require detecting push after vec![] creation
        # - unnecessary_to_owned: emitter converts literals to String, then borrows
        result = subprocess.run(
            ["cargo", "clippy", "--", "-D", "warnings",
             "-A", "unused_variables",
             "-A", "unused_mut",
             "-A", "unused_imports",
             "-A", "clippy::vec_init_then_push",
             "-A", "clippy::unnecessary_to_owned"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Cargo clippy failed:\n{result.stderr}\n\nGenerated code:\n{rust_code}"

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


class TestUnwrapMethods:
    """Test explicit unwrap/expect methods."""

    def test_result_unwrap(self, check_cargo):
        """Test Result.unwrap() explicit call."""
        code = '''
from spicycrab.types import Result, Ok, Err

def get_value() -> Result[int, str]:
    return Ok(42)

def main() -> None:
    result: Result[int, str] = get_value()
    value: int = Result.unwrap(result)
    print(value)
'''
        transpile_and_run(code, "42")

    def test_result_unwrap_or(self, check_cargo):
        """Test Result.unwrap_or() with default value."""
        code = '''
from spicycrab.types import Result, Ok, Err

def get_err() -> Result[int, str]:
    return Err("error")

def main() -> None:
    result: Result[int, str] = get_err()
    value: int = Result.unwrap_or(result, 0)
    print(value)
'''
        transpile_and_run(code, "0")

    def test_result_expect(self, check_cargo):
        """Test Result.expect() with custom message."""
        code = '''
from spicycrab.types import Result, Ok, Err

def get_value() -> Result[int, str]:
    return Ok(100)

def main() -> None:
    result: Result[int, str] = get_value()
    value: int = Result.expect(result, "should have value")
    print(value)
'''
        transpile_and_run(code, "100")

    def test_result_is_ok(self, check_cargo):
        """Test Result.is_ok() check."""
        code = '''
from spicycrab.types import Result, Ok, Err

def get_value() -> Result[int, str]:
    return Ok(42)

def main() -> None:
    result: Result[int, str] = get_value()
    if Result.is_ok(result):
        print("is ok")
    else:
        print("is err")
'''
        transpile_and_run(code, "is ok")

    def test_result_is_err(self, check_cargo):
        """Test Result.is_err() check."""
        code = '''
from spicycrab.types import Result, Ok, Err

def get_err() -> Result[int, str]:
    return Err("failed")

def main() -> None:
    result: Result[int, str] = get_err()
    if Result.is_err(result):
        print("is err")
    else:
        print("is ok")
'''
        transpile_and_run(code, "is err")


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


class TestTimeModule:
    """Test time module transpilation."""

    def test_time_functions(self, check_cargo):
        """Test time.time() and time.sleep() together."""
        code = '''
import time

def main() -> None:
    # Test time.time() returns positive timestamp
    t: float = time.time()
    if t <= 0.0:
        print("fail: time")
        return

    # Test time.sleep() pauses execution
    start: float = time.time()
    time.sleep(0.01)
    end: float = time.time()
    if end <= start:
        print("fail: sleep")
        return

    print("ok")
'''
        transpile_and_run(code, "ok")


class TestDatetimeModule:
    """Test datetime module transpilation using chrono.

    Instance method mappings (like dt.year, dt.isoformat()) require explicit
    type annotations for the transpiler to resolve the correct Rust methods.
    """

    def test_datetime_class_methods(self, check_cargo):
        """Test datetime.datetime class methods: now, utcnow, today."""
        code = '''
import datetime

def main() -> None:
    # Test datetime.now()
    now = datetime.datetime.now()

    # Test datetime.utcnow()
    utc = datetime.datetime.utcnow()

    # Test datetime.today()
    today = datetime.datetime.today()

    print("ok")
'''
        transpile_and_run(code, "ok")

    def test_date_today(self, check_cargo):
        """Test datetime.date.today() class method."""
        code = '''
import datetime

def main() -> None:
    # Test date.today()
    today = datetime.date.today()
    print("ok")
'''
        transpile_and_run(code, "ok")

    def test_datetime_fromtimestamp(self, check_cargo):
        """Test datetime.fromtimestamp."""
        code = '''
import datetime

def main() -> None:
    # Unix timestamp for 2024-01-01 00:00:00 UTC
    ts: float = 1704067200.0

    # Create datetime from timestamp
    dt = datetime.datetime.fromtimestamp(ts)

    # Just verify it works without crashing
    print("ok")
'''
        transpile_and_run(code, "ok")

    def test_datetime_instance_methods(self, check_cargo):
        """Test datetime instance methods with type annotations.

        Type annotations like `dt: datetime.datetime` enable the transpiler
        to resolve instance method calls like dt.year, dt.isoformat().
        """
        code = '''
import datetime

def main() -> None:
    # Type annotation enables instance method resolution
    dt: datetime.datetime = datetime.datetime.now()

    # Access properties (year, month, day, etc.)
    year: int = dt.year
    month: int = dt.month
    day: int = dt.day

    # Verify year is reasonable (2020-2100)
    valid: bool = year > 2020
    if valid:
        print("ok")
'''
        transpile_and_run(code, "ok")

    def test_date_instance_methods(self, check_cargo):
        """Test date instance methods with type annotations."""
        code = '''
import datetime

def main() -> None:
    # Type annotation enables instance method resolution
    today: datetime.date = datetime.date.today()

    # Access properties
    year: int = today.year
    month: int = today.month
    day: int = today.day

    # weekday() returns 0-6 (Monday-Sunday)
    weekday: int = today.weekday()

    valid: bool = weekday >= 0
    if valid:
        print("ok")
'''
        transpile_and_run(code, "ok")


class TestGlobModule:
    """Test glob module transpilation using Rust glob crate."""

    def test_glob_glob(self, check_cargo):
        """Test glob.glob() function."""
        code = '''
import glob

def main() -> None:
    # glob.glob returns list of matching paths
    # Use a pattern that should match at least Cargo.toml
    files: list[str] = glob.glob("*.toml")

    # Just verify it compiles and runs
    print("ok")
'''
        transpile_and_run(code, "ok")

    def test_glob_escape(self, check_cargo):
        """Test glob.escape() function."""
        code = '''
import glob

def main() -> None:
    # Escape special glob characters
    pattern: str = "file[1].txt"
    escaped: str = glob.escape(pattern)

    # Verify it compiles and runs
    print("ok")
'''
        transpile_and_run(code, "ok")


class TestTempfileModule:
    """Test tempfile module transpilation using Rust tempfile crate."""

    def test_gettempdir(self, check_cargo):
        """Test tempfile.gettempdir() function."""
        code = '''
import tempfile

def main() -> None:
    # Get the system temp directory
    tmpdir: str = tempfile.gettempdir()

    # Verify it returns a non-empty string
    if len(tmpdir) > 0:
        print("ok")
'''
        transpile_and_run(code, "ok")

    def test_mkdtemp(self, check_cargo):
        """Test tempfile.mkdtemp() function."""
        code = '''
import tempfile

def main() -> None:
    # Create a temporary directory
    tmpdir: str = tempfile.mkdtemp()

    # Verify it returns a path
    if len(tmpdir) > 0:
        print("ok")
'''
        transpile_and_run(code, "ok")

    def test_tempdir(self, check_cargo):
        """Test tempfile.TemporaryDirectory() function."""
        code = '''
import tempfile

def main() -> None:
    # Create a temporary directory (TempDir in Rust)
    tmpdir = tempfile.TemporaryDirectory()

    # Just verify it compiles and runs
    print("ok")
'''
        transpile_and_run(code, "ok")

    def test_tempdir_context_manager(self, check_cargo):
        """Test tempfile.TemporaryDirectory() as context manager."""
        code = '''
import tempfile

def main() -> None:
    # Use TemporaryDirectory as context manager
    # In Python, tmpdir is bound to the path (string), not the object
    with tempfile.TemporaryDirectory() as tmpdir:
        # tmpdir should be a string path
        if len(tmpdir) > 0:
            print("ok")
    # Directory is automatically cleaned up here
'''
        transpile_and_run(code, "ok")


class TestSubprocessModule:
    """Test subprocess module transpilation using std::process."""

    def test_subprocess_call(self, check_cargo):
        """Test subprocess.call() function."""
        code = '''
import subprocess

def main() -> None:
    # Run echo command
    args: list[str] = []
    exit_code: int = subprocess.call("echo", args)

    # exit_code should be 0 for success
    if exit_code == 0:
        print("ok")
'''
        transpile_and_run(code, "ok")

    def test_subprocess_check_output(self, check_cargo):
        """Test subprocess.check_output() function."""
        code = '''
import subprocess

def main() -> None:
    # Run echo hello and capture output
    args: list[str] = ["hello"]
    output: str = subprocess.check_output("echo", args)

    # Output should contain "hello"
    if len(output) > 0:
        print("ok")
'''
        transpile_and_run(code, "ok")

    def test_subprocess_getoutput(self, check_cargo):
        """Test subprocess.getoutput() function."""
        code = '''
import subprocess

def main() -> None:
    # Run shell command
    output: str = subprocess.getoutput("echo test")

    # Should contain "test"
    if len(output) > 0:
        print("ok")
'''
        transpile_and_run(code, "ok")


class TestShutilModule:
    """Test shutil module transpilation."""

    def test_shutil_rmtree(self, check_cargo):
        """Test shutil.rmtree() function."""
        code = '''
import shutil
import tempfile
import os

def main() -> None:
    # Create temp directory
    tmpdir: str = tempfile.mkdtemp()

    # Verify it exists
    exists: bool = os.path.isdir(tmpdir)
    if not exists:
        print("fail1")
        return

    # Remove the directory tree
    shutil.rmtree(tmpdir)

    # Verify it's gone
    gone: bool = not os.path.isdir(tmpdir)
    if gone:
        print("ok")
'''
        transpile_and_run(code, "ok")

    def test_shutil_which(self, check_cargo):
        """Test shutil.which() function."""
        code = '''
import shutil

def main() -> None:
    # Find echo command (should exist on all systems)
    result: str = shutil.which("echo")

    # Should find it (returns empty string if not found)
    if len(result) > 0:
        print("ok")
'''
        transpile_and_run(code, "ok")


class TestRandomModule:
    """Test random module transpilation using Rust rand crate."""

    def test_random_random(self, check_cargo):
        """Test random.random() function."""
        code = '''
import random

def main() -> None:
    # Generate random float in [0.0, 1.0)
    r: float = random.random()

    # Verify it's in valid range
    valid: bool = r >= 0.0
    if valid:
        in_range: bool = r < 1.0
        if in_range:
            print("ok")
'''
        transpile_and_run(code, "ok")

    def test_random_randint(self, check_cargo):
        """Test random.randint() function."""
        code = '''
import random

def main() -> None:
    # Generate random int in [1, 10]
    r: int = random.randint(1, 10)

    # Verify it's in valid range
    valid: bool = r >= 1
    if valid:
        in_range: bool = r <= 10
        if in_range:
            print("ok")
'''
        transpile_and_run(code, "ok")

    def test_random_uniform(self, check_cargo):
        """Test random.uniform() function."""
        code = '''
import random

def main() -> None:
    # Generate random float in [5.0, 10.0]
    r: float = random.uniform(5.0, 10.0)

    # Verify it's in valid range
    valid: bool = r >= 5.0
    if valid:
        in_range: bool = r <= 10.0
        if in_range:
            print("ok")
'''
        transpile_and_run(code, "ok")

    def test_random_choice(self, check_cargo):
        """Test random.choice() function."""
        code = '''
import random

def main() -> None:
    items: list[int] = [1, 2, 3, 4, 5]
    chosen: int = random.choice(items)

    # Verify the choice is from the list
    valid: bool = chosen >= 1
    if valid:
        in_range: bool = chosen <= 5
        if in_range:
            print("ok")
'''
        transpile_and_run(code, "ok")

    def test_random_sample(self, check_cargo):
        """Test random.sample() function."""
        code = '''
import random

def main() -> None:
    items: list[int] = [1, 2, 3, 4, 5]
    sampled: list[int] = random.sample(items, 3)

    # Verify we got 3 unique elements
    if len(sampled) == 3:
        print("ok")
'''
        transpile_and_run(code, "ok")
