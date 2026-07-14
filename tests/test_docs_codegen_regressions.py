"""Regressions for codegen bugs found by transpiling the examples in docs/.

Each case here previously emitted Rust that did not compile (or crashed crabpy
outright), while the docs described the correct output.
"""

from spicycrab.analyzer.type_resolver import resolve_types
from spicycrab.codegen.cargo import generate_cargo_toml
from spicycrab.codegen.emitter import RustEmitter
from spicycrab.parser import parse_source


def emit_rust(source: str) -> str:
    module = parse_source(source)
    return RustEmitter(resolve_types(module)).emit_module(module)


def test_logging_call_does_not_crash_and_keeps_rust_format_string() -> None:
    """log::info!("{}", x): the "{}" is a Rust placeholder, not a str.format field."""
    rust_code = emit_rust(
        """
import logging

def log_user(name: str) -> None:
    logging.info(f"User {name}")
"""
    )

    assert 'log::info!("{}", format!("User {}", name));' in rust_code


def test_logging_import_pulls_in_log_crates() -> None:
    module = parse_source("import logging\n\ndef main() -> None:\n    logging.info('hi')\n")
    cargo = generate_cargo_toml(name="demo", modules=[module])

    assert "log = " in cargo
    assert "env_logger = " in cargo


def test_len_is_cast_to_i64_in_value_position() -> None:
    """Rust's .len() is usize; a `-> int` function needs the cast (E0308)."""
    rust_code = emit_rust(
        """
def count_chars(s: str) -> int:
    return len(s)
"""
    )

    assert "s.len() as i64" in rust_code


def test_len_respects_explicit_rust_int_return_type() -> None:
    rust_code = emit_rust(
        """
from spicycrab.types import usize

def get_length(items: list[str]) -> usize:
    return len(items)
"""
    )

    assert "items.len() as usize" in rust_code


def test_len_comparison_still_casts_the_other_side_to_usize() -> None:
    rust_code = emit_rust(
        """
def main() -> None:
    values: list[int] = [1, 2, 3]
    i: int = 0
    while i < len(values):
        print(values[i])
        i = i + 1
"""
    )

    assert "while (i as usize) < values.len()" in rust_code


def test_reassigned_parameter_is_declared_mut() -> None:
    """Assigning to an immutable argument is E0384."""
    rust_code = emit_rust(
        """
def increment(x: int) -> int:
    x = x + 1
    return x
"""
    )

    assert "pub fn increment(mut x: i64) -> i64" in rust_code


def test_method_mutating_a_self_collection_takes_mut_self() -> None:
    """self.items.append(x) mutates through &self without any assignment."""
    rust_code = emit_rust(
        """
class Stack:
    def __init__(self) -> None:
        self.items: list[int] = []

    def push(self, item: int) -> None:
        self.items.append(item)

    def size(self) -> int:
        return len(self.items)
"""
    )

    assert "pub fn push(&mut self, item: i64)" in rust_code
    # a read-only method must stay immutably borrowed
    assert "pub fn size(&self) -> i64" in rust_code


def test_list_pop_unwraps_the_option() -> None:
    """Python's list.pop() returns the element; Vec::pop returns Option<T>."""
    rust_code = emit_rust(
        """
class Stack:
    def __init__(self) -> None:
        self.items: list[int] = []

    def pop(self) -> int:
        return self.items.pop()
"""
    )

    assert "self.items.pop().unwrap()" in rust_code


def test_owned_field_returned_from_shared_self_is_cloned() -> None:
    """Moving a String out of &self is E0507."""
    rust_code = emit_rust(
        """
class Worker:
    def __init__(self, name: str) -> None:
        self.name: str = name

    def label(self) -> str:
        return self.name

    def count(self) -> int:
        return 1
"""
    )

    assert "self.name.clone()" in rust_code


def test_float_format_spec_drops_the_python_type_char() -> None:
    """Rust has no `f` format trait: {:.2f} is a hard rustc error."""
    rust_code = emit_rust(
        """
def format_price(amount: float) -> str:
    return f"${amount:.2f}"
"""
    )

    assert 'format!("${:.2}", amount)' in rust_code
    assert ":.2f" not in rust_code


def test_format_spec_keeps_traits_rust_shares() -> None:
    rust_code = emit_rust(
        """
def as_hex(n: int) -> str:
    return f"{n:x}"
"""
    )

    assert 'format!("{:x}", n)' in rust_code


def test_dict_subscript_assignment_becomes_insert() -> None:
    rust_code = emit_rust(
        """
def create_dict() -> dict[str, int]:
    ages: dict[str, int] = {}
    ages["Alice"] = 30
    return ages
"""
    )

    assert "let mut ages: HashMap<String, i64> = HashMap::new();" in rust_code
    assert 'ages.insert("Alice".to_string(), 30);' in rust_code


def test_dict_read_indexes_by_str_not_string() -> None:
    """HashMap implements Index<&Q>, so the key must not be a String."""
    rust_code = emit_rust(
        """
def lookup(ages: dict[str, int]) -> int:
    return ages["Alice"]
"""
    )

    assert 'ages["Alice"]' in rust_code


def test_list_subscript_assignment_casts_index_to_usize() -> None:
    rust_code = emit_rust(
        """
def set_item(values: list[int], i: int) -> list[int]:
    values[i] = 99
    return values
"""
    )

    assert "pub fn set_item(mut values: Vec<i64>" in rust_code
    assert "values[i as usize] = 99;" in rust_code


def test_pathlib_methods_map_to_std_fs() -> None:
    rust_code = emit_rust(
        """
from pathlib import Path

def read_file(path: Path) -> str:
    return path.read_text()

def join_paths(base: Path, name: str) -> Path:
    return base / name
"""
    )

    assert "std::fs::read_to_string(&path).unwrap()" in rust_code
    # pathlib overloads `/` as join; a real division is E0369
    assert "base.join(name)" in rust_code


def test_rust_std_statics_emit_paths_not_python_attribute_syntax() -> None:
    rust_code = emit_rust(
        """
from rust_std.sync import Arc

def share() -> None:
    data: Arc[str] = Arc.new("shared")
    count: int = Arc.strong_count(data)
    print(count)
"""
    )

    assert "std::sync::Arc::new(" in rust_code
    assert "Arc.new(" not in rust_code


def test_rust_std_result_helpers_unwrap_outside_result_context() -> None:
    """A `?` baked into the mapping template is E0277 in a non-Result function."""
    rust_code = emit_rust(
        """
from rust_std.fs import read_to_string

def read_file(path: str) -> str:
    return read_to_string(path)
"""
    )

    assert "std::fs::read_to_string(path).unwrap()" in rust_code


def test_os_environ_get_maps_to_std_env_var() -> None:
    """Unmapped, os.environ.get fell through to dict .get() and emitted a literal `os`."""
    rust_code = emit_rust(
        """
import os

def get_home() -> str:
    return os.environ.get("HOME", "")
"""
    )

    assert 'std::env::var("HOME").unwrap_or("".to_string())' in rust_code
    assert "os.environ" not in rust_code


def test_os_environ_get_without_default_yields_option() -> None:
    rust_code = emit_rust(
        """
import os

def maybe_home() -> str | None:
    return os.environ.get("HOME")
"""
    )

    assert 'std::env::var("HOME").ok()' in rust_code


def test_rust_std_constants_emit_full_paths() -> None:
    """UNIX_EPOCH / Ordering.SeqCst are values, not calls, and leaked as Python syntax."""
    rust_code = emit_rust(
        """
from rust_std.time import SystemTime, UNIX_EPOCH

def get_timestamp() -> int:
    now = SystemTime.now()
    since_epoch = now.duration_since(UNIX_EPOCH)
    return since_epoch.as_secs()
"""
    )

    assert "std::time::UNIX_EPOCH" in rust_code
    # duration_since returns a Result, and as_secs a u64
    assert ".unwrap()" in rust_code
    assert "as_secs() as i64" in rust_code


def test_atomic_ordering_variant_emits_full_path() -> None:
    rust_code = emit_rust(
        """
from rust_std.sync import AtomicBool, Ordering

def use_atomics() -> None:
    flag: AtomicBool = AtomicBool.new(False)
    flag.store(True, Ordering.SeqCst)
"""
    )

    assert "std::sync::atomic::Ordering::SeqCst" in rust_code
    assert "Ordering.SeqCst" not in rust_code


def test_rwlock_read_is_not_mistaken_for_a_file_read() -> None:
    """lock.read() collided with the IO read() mapping and compiled to read_to_string."""
    rust_code = emit_rust(
        """
from rust_std.sync import RwLock

def use_rwlock() -> None:
    lock: RwLock[str] = RwLock.new("data")
    reader = lock.read()
    print(reader)
"""
    )

    assert "lock.read().unwrap()" in rust_code
    assert "read_to_string" not in rust_code


def test_pathlib_read_text_still_wins_over_rust_std_path() -> None:
    """The rust_std method tables must not hijack pathlib, which shares the name Path."""
    rust_code = emit_rust(
        """
from pathlib import Path

def read_file(path: Path) -> str:
    return path.read_text()
"""
    )

    assert "std::fs::read_to_string(&path).unwrap()" in rust_code


def test_any_type_pulls_in_serde_json_dependency() -> None:
    source = """
from typing import Any

def process(data: dict[str, Any]) -> int:
    return len(data)
"""
    module = parse_source(source)
    rust_code = RustEmitter(resolve_types(module)).emit_module(module)
    cargo = generate_cargo_toml(name="demo", modules=[module], uses_serde_json="serde_json::" in rust_code)

    assert "serde_json::Value" in rust_code
    assert "serde_json = " in cargo
