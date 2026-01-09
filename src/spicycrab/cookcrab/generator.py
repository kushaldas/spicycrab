"""Stub generator: Convert parsed Rust crates to Python stub packages.

This module takes the output of the Rust parser and generates:
- pyproject.toml
- spicycrab_<crate>/__init__.py (Python stubs)
- spicycrab_<crate>/_spicycrab.toml (transpilation mappings)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spicycrab.cookcrab._parser import (
        RustCrate,
        RustFunction,
        RustMethod,
        RustTypeAlias,
    )


# Python reserved keywords - methods with these names must be skipped
PYTHON_RESERVED_KEYWORDS: set[str] = {
    "False",
    "None",
    "True",
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
}


def is_valid_python_identifier(name: str) -> bool:
    """Check if a name is a valid Python identifier (not a reserved keyword)."""
    return name not in PYTHON_RESERVED_KEYWORDS and name.isidentifier()


def python_safe_name(name: str) -> str:
    """Convert a name to a Python-safe identifier.

    If the name is a Python reserved keyword, append an underscore.
    This follows Python's convention (e.g., class_ for class).
    """
    if name in PYTHON_RESERVED_KEYWORDS:
        return f"{name}_"
    return name


# Rust to Python type mapping
RUST_TO_PYTHON_TYPES: dict[str, str] = {
    "i8": "int",
    "i16": "int",
    "i32": "int",
    "i64": "int",
    "i128": "int",
    "isize": "int",
    "u8": "int",
    "u16": "int",
    "u32": "int",
    "u64": "int",
    "u128": "int",
    "usize": "int",
    "f32": "float",
    "f64": "float",
    "bool": "bool",
    "char": "str",
    "String": "str",
    "&str": "str",
    "&'staticstr": "str",
    "()": "None",
}


def returns_result(return_type: str | None) -> bool:
    """Check if a return type is a Result type.

    Detects:
    - Result<T, E>
    - crate::Result<T>
    - std::result::Result<T, E>
    - Custom Result type aliases (e.g., reqwest::Result)
    """
    if not return_type:
        return False
    # Remove leading/trailing whitespace
    rt = return_type.strip()
    # Check for Result pattern
    if rt.startswith("Result<") or rt.startswith("Result "):
        return True
    # Check for qualified Result (e.g., std::result::Result, crate::Result)
    if "::Result<" in rt or "::Result " in rt:
        return True
    # Check for just "Result" at the end of a path (e.g., crate::Result)
    if rt.endswith("::Result") or rt == "Result":
        return True
    return False


def extract_return_type_name(return_type: str | None, self_type: str) -> str | None:
    """Extract the simple type name from a Rust return type.

    Used for method chaining - when a method returns RequestBuilder,
    we need to know that so subsequent method calls can be looked up
    on RequestBuilder rather than the original receiver type.

    Args:
        return_type: The Rust return type string (e.g., "RequestBuilder", "Result<Response, Error>")
        self_type: The type name that "Self" should resolve to

    Returns:
        The type name (e.g., "RequestBuilder", "Response") or None if not determinable
    """
    if not return_type:
        return None

    rt = return_type.strip()

    # Handle Self -> return the struct name
    if rt == "Self":
        return self_type

    # Handle &Self or &mut Self
    if rt in ("&Self", "&mut Self"):
        return self_type

    # Handle references (&T, &mut T)
    if rt.startswith("&"):
        rt = rt[1:].strip()
        if rt.startswith("mut "):
            rt = rt[4:].strip()

    # Handle Result<T, E> -> extract T
    if rt.startswith("Result<") or "::Result<" in rt:
        # Find the content inside Result<...>
        start = rt.find("<")
        if start != -1:
            depth = 0
            end = start
            for i, c in enumerate(rt[start:], start):
                if c == "<":
                    depth += 1
                elif c == ">":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            inner = rt[start + 1 : end]
            # Get the Ok type (before the first comma at depth 0)
            depth = 0
            for i, c in enumerate(inner):
                if c == "<":
                    depth += 1
                elif c == ">":
                    depth -= 1
                elif c == "," and depth == 0:
                    inner = inner[:i].strip()
                    break
            rt = inner

    # Handle Option<T> -> extract T
    if rt.startswith("Option<") or "::Option<" in rt:
        start = rt.find("<")
        if start != -1:
            end = rt.rfind(">")
            if end != -1:
                rt = rt[start + 1 : end].strip()

    # Handle Box<T> -> extract T
    if rt.startswith("Box<") or "::Box<" in rt:
        start = rt.find("<")
        if start != -1:
            end = rt.rfind(">")
            if end != -1:
                rt = rt[start + 1 : end].strip()

    # Strip path prefix (e.g., crate::module::Type -> Type)
    if "::" in rt:
        # Find last :: that's outside angle brackets
        depth = 0
        last_sep = -1
        for i, c in enumerate(rt):
            if c == "<":
                depth += 1
            elif c == ">":
                depth -= 1
            elif rt[i : i + 2] == "::" and depth == 0:
                last_sep = i
        if last_sep >= 0:
            rt = rt[last_sep + 2 :]

    # Skip impl Trait types - too complex to infer
    if rt.startswith("impl "):
        return None

    # Skip primitive types - no need to track these
    primitive_types = {
        "i8",
        "i16",
        "i32",
        "i64",
        "u8",
        "u16",
        "u32",
        "u64",
        "f32",
        "f64",
        "bool",
        "char",
        "str",
        "String",
        "()",
        "usize",
        "isize",
    }
    if rt in primitive_types:
        return None

    # Skip if result is empty or just punctuation
    if not rt or rt in ("()", "(,)", ""):
        return None

    # Final validation - should be a valid identifier
    base_name = rt.split("<")[0].strip()  # Handle generics like Vec<T>
    if not base_name or not base_name[0].isalpha():
        return None

    return base_name


# Special function path overrides for crates that re-export functions at different paths
# Format: (crate_name, function_name) -> (rust_path, rust_imports)
FUNCTION_PATH_OVERRIDES: dict[tuple[str, str], tuple[str, list[str]]] = {
    ("tokio", "sleep"): ("tokio::time::sleep({arg0})", ["tokio::time::sleep"]),
    ("tokio", "sleep_until"): ("tokio::time::sleep_until({arg0})", ["tokio::time::sleep_until"]),
    ("tokio", "spawn"): ("tokio::spawn({arg0})", []),
    ("tokio", "spawn_blocking"): ("tokio::task::spawn_blocking({arg0})", ["tokio::task::spawn_blocking"]),
}


# Standard library types that are commonly used and need stubs
# Format: (crate_name, type_name) -> (class_code, type_mapping, function_mappings)
STD_TYPE_STUBS: dict[tuple[str, str], tuple[str, str, list[tuple[str, str]]]] = {
    ("tokio", "Duration"): (
        # Class stub
        '''
class Duration:
    """A Duration type representing a span of time.

    Maps to std::time::Duration in Rust.
    """

    @staticmethod
    def from_secs(secs: int) -> "Duration":
        """Creates a new Duration from seconds."""
        ...

    @staticmethod
    def from_millis(millis: int) -> "Duration":
        """Creates a new Duration from milliseconds."""
        ...

    @staticmethod
    def from_micros(micros: int) -> "Duration":
        """Creates a new Duration from microseconds."""
        ...

    @staticmethod
    def from_nanos(nanos: int) -> "Duration":
        """Creates a new Duration from nanoseconds."""
        ...

    def as_secs(self) -> int:
        """Returns the number of whole seconds."""
        ...

    def as_millis(self) -> int:
        """Returns the total number of milliseconds."""
        ...
''',
        # Type mapping
        "std::time::Duration",
        # Function mappings (python_suffix, rust_code)
        [
            ("Duration.from_secs", "std::time::Duration::from_secs({arg0} as u64)"),
            ("Duration.from_millis", "std::time::Duration::from_millis({arg0} as u64)"),
            ("Duration.from_micros", "std::time::Duration::from_micros({arg0} as u64)"),
            ("Duration.from_nanos", "std::time::Duration::from_nanos({arg0} as u64)"),
        ],
    ),
    ("tokio", "Instant"): (
        # Class stub
        '''
class Instant:
    """A measurement of a monotonically nondecreasing clock.

    Maps to tokio::time::Instant in Rust.
    """

    @staticmethod
    def now() -> "Instant":
        """Returns the current instant."""
        ...

    def elapsed(self) -> Duration:
        """Returns the time elapsed since this instant."""
        ...
''',
        # Type mapping
        "tokio::time::Instant",
        # Function mappings
        [
            ("Instant.now", "tokio::time::Instant::now()"),
        ],
    ),
    ("tokio", "MpscSender"): (
        # Class stub for mpsc bounded channel sender
        '''
class MpscSender:
    """Sender half of a bounded mpsc channel.

    Maps to tokio::sync::mpsc::Sender<String> in Rust.
    Use with mpsc_channel() for type-safe channel creation.
    """

    async def send(self, value: str) -> None:
        """Sends a value, waiting until there is capacity."""
        ...

    def clone(self) -> "MpscSender":
        """Clones this sender."""
        ...

    def is_closed(self) -> bool:
        """Returns True if the receiver has been dropped."""
        ...
''',
        # Type mapping
        "tokio::sync::mpsc::Sender<String>",
        # Function mappings - none needed, methods are instance methods
        [],
    ),
    ("tokio", "MpscReceiver"): (
        # Class stub for mpsc bounded channel receiver
        '''
class MpscReceiver:
    """Receiver half of a bounded mpsc channel.

    Maps to tokio::sync::mpsc::Receiver<String> in Rust.
    Use with mpsc_channel() for type-safe channel creation.
    """

    async def recv(self) -> str | None:
        """Receives the next value, or None if the channel is closed."""
        ...

    def close(self) -> None:
        """Closes the receiving half without dropping it."""
        ...
''',
        # Type mapping
        "tokio::sync::mpsc::Receiver<String>",
        # Function mappings - none needed, methods are instance methods
        [],
    ),
    ("tokio", "Arc"): (
        # Class stub for Arc (thread-safe reference counting)
        '''
from typing import TypeVar, Generic

T = TypeVar("T")


class Arc(Generic[T]):
    """Thread-safe reference-counting pointer.

    Arc stands for Atomically Reference Counted. It provides shared ownership
    of a value of type T, allocated on the heap. Cloning an Arc produces a new
    Arc that points to the same allocation, increasing the reference count.

    Maps to std::sync::Arc<T> in Rust.

    Common use cases:
    - Sharing immutable data between spawned tasks
    - Combined with Mutex for shared mutable state: Arc[Mutex[T]]

    Example:
        data: Arc[str] = Arc.new("shared config")
        cloned: Arc[str] = Arc.clone(data)

        # Share between tasks
        handle1 = spawn(worker(Arc.clone(data)))
        handle2 = spawn(worker(Arc.clone(data)))
    """

    @staticmethod
    def new(value: T) -> "Arc[T]":
        """Constructs a new Arc<T>.

        Args:
            value: The value to wrap in an Arc.

        Returns:
            A new Arc containing the value.
        """
        ...

    @staticmethod
    def clone(arc: "Arc[T]") -> "Arc[T]":
        """Creates a new Arc that points to the same allocation.

        This increments the strong reference count.

        Args:
            arc: The Arc to clone.

        Returns:
            A new Arc pointing to the same data.
        """
        ...

    @staticmethod
    def strong_count(arc: "Arc[T]") -> int:
        """Gets the number of strong (Arc) pointers to this allocation.

        Args:
            arc: The Arc to check.

        Returns:
            The number of strong references.
        """
        ...

    @staticmethod
    def weak_count(arc: "Arc[T]") -> int:
        """Gets the number of weak (Weak) pointers to this allocation.

        Args:
            arc: The Arc to check.

        Returns:
            The number of weak references.
        """
        ...

    @staticmethod
    def try_unwrap(arc: "Arc[T]") -> T | None:
        """Returns the inner value if the Arc has exactly one strong reference.

        If there are multiple strong references, returns None.

        Args:
            arc: The Arc to unwrap.

        Returns:
            The inner value if ref count is 1, otherwise None.
        """
        ...

    @staticmethod
    def into_inner(arc: "Arc[T]") -> T | None:
        """Returns the inner value if the Arc has exactly one strong reference.

        This is similar to try_unwrap but available on Rust 1.70+.

        Args:
            arc: The Arc to unwrap.

        Returns:
            The inner value if ref count is 1, otherwise None.
        """
        ...
''',
        # Type mapping - generic Arc<T>
        "std::sync::Arc",
        # Function mappings for static methods
        [
            ("Arc.new", "std::sync::Arc::new({arg0})"),
            ("Arc.clone", "std::sync::Arc::clone(&{arg0})"),
            ("Arc.strong_count", "std::sync::Arc::strong_count(&{arg0}) as i64"),
            ("Arc.weak_count", "std::sync::Arc::weak_count(&{arg0}) as i64"),
            ("Arc.try_unwrap", "std::sync::Arc::try_unwrap({arg0}).ok()"),
            ("Arc.into_inner", "std::sync::Arc::into_inner({arg0})"),
        ],
    ),
    ("tokio", "Mutex"): (
        # Class stub for tokio's async Mutex
        '''
class Mutex(Generic[T]):
    """An asynchronous mutual exclusion primitive.

    This is tokio's async-aware Mutex, suitable for use across .await points.
    Unlike std::sync::Mutex, holding a tokio::sync::Mutex guard across an
    await point is safe.

    Maps to tokio::sync::Mutex<T> in Rust.

    Common use case - shared mutable state between tasks:
        counter: Arc[Mutex[int]] = Arc.new(Mutex.new(0))

        async def increment(c: Arc[Mutex[int]]) -> None:
            guard = await c.lock()
            # modify the value through the guard

    Example:
        mutex: Mutex[int] = Mutex.new(0)
        guard = await mutex.lock()
    """

    @staticmethod
    def new(value: T) -> "Mutex[T]":
        """Creates a new Mutex wrapping the given value.

        Args:
            value: The value to protect with the mutex.

        Returns:
            A new Mutex containing the value.
        """
        ...

    async def lock(self) -> "MutexGuard[T]":
        """Locks this mutex, waiting asynchronously if it's already locked.

        Returns:
            A guard that releases the lock when dropped.
        """
        ...

    def try_lock(self) -> "MutexGuard[T] | None":
        """Attempts to acquire the lock without waiting.

        Returns:
            A guard if successful, None if the mutex is already locked.
        """
        ...

    def is_locked(self) -> bool:
        """Returns True if the mutex is currently locked.

        Returns:
            True if locked, False otherwise.
        """
        ...


class MutexGuard(Generic[T]):
    """A guard that releases the mutex when dropped.

    This is returned by Mutex.lock() and provides access to the protected data.
    The lock is automatically released when the guard goes out of scope.
    """
    pass
''',
        # Type mapping
        "tokio::sync::Mutex",
        # Function mappings
        [
            ("Mutex.new", "tokio::sync::Mutex::new({arg0})"),
        ],
    ),
    ("tokio", "RwLock"): (
        # Class stub for tokio's async RwLock
        '''
class RwLock(Generic[T]):
    """An asynchronous reader-writer lock.

    This type of lock allows multiple readers or a single writer at any point
    in time. Useful when you have data that is read frequently but written
    infrequently.

    Maps to tokio::sync::RwLock<T> in Rust.

    Example:
        data: RwLock[list[str]] = RwLock.new(["initial"])

        # Multiple readers allowed
        read_guard = await data.read()

        # Single writer, blocks readers
        write_guard = await data.write()
    """

    @staticmethod
    def new(value: T) -> "RwLock[T]":
        """Creates a new RwLock wrapping the given value.

        Args:
            value: The value to protect with the lock.

        Returns:
            A new RwLock containing the value.
        """
        ...

    async def read(self) -> "RwLockReadGuard[T]":
        """Locks this RwLock for reading, waiting if a writer holds the lock.

        Multiple readers can hold the lock simultaneously.

        Returns:
            A read guard that releases the lock when dropped.
        """
        ...

    async def write(self) -> "RwLockWriteGuard[T]":
        """Locks this RwLock for writing, waiting if any readers or writers hold the lock.

        Returns:
            A write guard that releases the lock when dropped.
        """
        ...

    def try_read(self) -> "RwLockReadGuard[T] | None":
        """Attempts to acquire the read lock without waiting.

        Returns:
            A read guard if successful, None if the lock is held by a writer.
        """
        ...

    def try_write(self) -> "RwLockWriteGuard[T] | None":
        """Attempts to acquire the write lock without waiting.

        Returns:
            A write guard if successful, None if the lock is held.
        """
        ...


class RwLockReadGuard(Generic[T]):
    """A guard that releases the read lock when dropped."""
    pass


class RwLockWriteGuard(Generic[T]):
    """A guard that releases the write lock when dropped."""
    pass
''',
        # Type mapping
        "tokio::sync::RwLock",
        # Function mappings
        [
            ("RwLock.new", "tokio::sync::RwLock::new({arg0})"),
        ],
    ),
}


# Standalone function stubs for functions that aren't detected by the parser
# (e.g., re-exported functions like tokio::spawn which is actually tokio::task::spawn)
# Format: (crate_name, function_name) -> (stub_code, rust_code, rust_imports, is_async)
FUNCTION_STUBS: dict[tuple[str, str], tuple[str, str, list[str], bool]] = {
    ("tokio", "spawn"): (
        '''
async def spawn(future: F) -> JoinHandle:
    """Spawns a new asynchronous task.

    The spawned task may execute on the current thread or another thread.
    Maps to tokio::spawn in Rust.
    """
    ...
''',
        "tokio::spawn({arg0})",
        [],
        True,
    ),
    ("tokio", "spawn_blocking"): (
        '''
async def spawn_blocking(f: F) -> JoinHandle:
    """Runs a blocking function on a dedicated thread pool.

    Maps to tokio::task::spawn_blocking in Rust.
    """
    ...
''',
        "tokio::task::spawn_blocking({arg0})",
        ["tokio::task::spawn_blocking"],
        True,
    ),
    ("tokio", "mpsc_channel"): (
        '''
def mpsc_channel(buffer: int) -> tuple:
    """Creates a bounded mpsc channel for communication between tasks.

    Returns a tuple of (Sender, Receiver).
    Maps to tokio::sync::mpsc::channel in Rust.
    """
    ...
''',
        "tokio::sync::mpsc::channel({arg0})",
        ["tokio::sync::mpsc"],
        False,
    ),
    ("tokio", "mpsc_unbounded_channel"): (
        '''
def mpsc_unbounded_channel() -> tuple:
    """Creates an unbounded mpsc channel for communication between tasks.

    Returns a tuple of (UnboundedSender, UnboundedReceiver).
    Maps to tokio::sync::mpsc::unbounded_channel in Rust.
    """
    ...
''',
        "tokio::sync::mpsc::unbounded_channel()",
        ["tokio::sync::mpsc"],
        False,
    ),
}


# Mapping of methods that require trait imports
# Format: crate_name -> {method_name -> trait_import}
TRAIT_METHOD_IMPORTS: dict[str, dict[str, str]] = {
    "chrono": {
        # Datelike trait methods
        "year": "chrono::Datelike",
        "month": "chrono::Datelike",
        "month0": "chrono::Datelike",
        "day": "chrono::Datelike",
        "day0": "chrono::Datelike",
        "ordinal": "chrono::Datelike",
        "ordinal0": "chrono::Datelike",
        "weekday": "chrono::Datelike",
        "iso_week": "chrono::Datelike",
        "with_year": "chrono::Datelike",
        "with_month": "chrono::Datelike",
        "with_month0": "chrono::Datelike",
        "with_day": "chrono::Datelike",
        "with_day0": "chrono::Datelike",
        "with_ordinal": "chrono::Datelike",
        "with_ordinal0": "chrono::Datelike",
        # Timelike trait methods
        "hour": "chrono::Timelike",
        "minute": "chrono::Timelike",
        "second": "chrono::Timelike",
        "nanosecond": "chrono::Timelike",
        "with_hour": "chrono::Timelike",
        "with_minute": "chrono::Timelike",
        "with_second": "chrono::Timelike",
        "with_nanosecond": "chrono::Timelike",
        "num_seconds_from_midnight": "chrono::Timelike",
    },
}


@dataclass
class FunctionMapping:
    """A function/constructor mapping."""

    python: str
    rust_code: str
    rust_imports: list[str] = field(default_factory=list)
    needs_result: bool = False
    param_types: list[str] = field(default_factory=list)  # Rust types for each param


@dataclass
class MethodMapping:
    """A method mapping."""

    python: str
    rust_code: str
    rust_imports: list[str] = field(default_factory=list)
    needs_result: bool = False
    returns_self: bool = False
    param_types: list[str] = field(default_factory=list)  # Rust types for each param


@dataclass
class TypeMapping:
    """A type mapping."""

    python: str
    rust: str


@dataclass
class GeneratedStub:
    """Generated stub package data."""

    crate_name: str
    version: str
    python_module: str
    init_py: str
    spicycrab_toml: str
    pyproject_toml: str


def sanitize_rust_type(rust_type: str) -> str:
    """Sanitize Rust-specific syntax that doesn't translate to Python.

    Removes lifetimes, dyn keywords, trait bounds, macros, etc.
    Returns a valid Python type or 'object' for unsupported types.
    """
    import re

    # Handle macro invocations (e.g., impl_backtrace!()) -> object
    if "!" in rust_type:
        return "object"

    # Handle parenthesized dyn types like (dyn StdError + ...) -> object
    if rust_type.startswith("(") and "dyn" in rust_type:
        return "object"

    # Handle Rust tuples like (usize, Option<usize>) -> object
    # These need special handling that's beyond simple sanitization
    if rust_type.startswith("(") and "," in rust_type:
        return "object"

    # Handle malformed tuple types (unbalanced parentheses)
    if rust_type.startswith("(") and rust_type.count("(") != rust_type.count(")"):
        return "object"

    # Handle types with references inside generics (e.g., Bound<&usize>)
    # These can't be represented in Python type hints
    if "<&" in rust_type or "< &" in rust_type:
        return "object"

    # Handle types with Self inside generics (e.g., Error<Self>)
    # Self is a Rust-specific type that can't be represented in Python
    if "<Self>" in rust_type or "< Self>" in rust_type or "<Self," in rust_type:
        return "object"

    # Handle Rust array types [T; N]
    if rust_type.startswith("[") and ";" in rust_type:
        return "object"

    # Handle Rust slice types &[T] or [T] -> object
    # These appear in types like &[IoSlice] which becomes IoSlice] after sanitization
    if "[" in rust_type or "]" in rust_type:
        return "object"

    # Handle Rust unit type () and Result<()>
    if rust_type == "()" or rust_type == "Result<()>" or rust_type == "Result< ()>":
        return "None"
    if "<()>" in rust_type or "< ()>" in rust_type:
        return "object"

    # Remove std::ops:: and other common path prefixes
    rust_type = rust_type.replace("std::ops::", "")
    rust_type = rust_type.replace("std::fmt::", "")
    rust_type = rust_type.replace("std::marker::", "")
    rust_type = rust_type.replace("core::ops::", "")
    rust_type = rust_type.replace("core::fmt::", "")

    # Handle Rust-specific std::ops types and other Rust-only types
    rust_only_types = [
        "Bound<",
        "RangeFull",
        "Range<",
        "RangeInclusive<",
        "RangeTo<",
        "RangeFrom<",
        "RangeToInclusive<",
        "Formatter<",
        "Arguments<",
        "PhantomData<",
    ]
    for rust_only in rust_only_types:
        if rust_type.startswith(rust_only):
            return "object"

    # Remove all lifetime annotations ('static, 'a, '_,  etc.)
    rust_type = re.sub(r"'\w*\s*", "", rust_type)

    # Remove dyn keyword
    rust_type = rust_type.replace("dyn ", "")

    # Remove trait bounds (+ Send + Sync, etc.) - keep only the first type/trait
    if "+" in rust_type and not rust_type.startswith("Option") and not rust_type.startswith("Result"):
        rust_type = rust_type.split("+")[0].strip()

    # Remove mut keyword (handle both "mut " and "mut" prefix)
    rust_type = re.sub(r"\bmut\s+", "", rust_type)
    rust_type = re.sub(r"\bmut([A-Z])", r"\1", rust_type)  # mutE -> E
    rust_type = re.sub(r"\bmut\(", "(", rust_type)  # mut(...) -> (...)

    # Handle impl Trait types (can't be expressed in Python)
    if "impl" in rust_type.lower():
        return "object"

    # Remove * const and * mut (raw pointers) -> object
    if rust_type.startswith("*"):
        return "object"

    # Handle empty generics like Request<> -> Request
    rust_type = re.sub(r"<\s*>", "", rust_type)

    # Handle malformed generics with leading comma like Mut<,T> -> object
    if re.search(r"<\s*,", rust_type):
        return "object"

    # Handle incomplete generics that just have > without matching <
    if ">" in rust_type and "<" not in rust_type:
        return "object"

    # Clean up any remaining whitespace issues
    rust_type = " ".join(rust_type.split())

    # If result is empty or just punctuation, return object
    if not rust_type or rust_type in ("()", "(,)", ""):
        return "object"

    return rust_type.strip()


def rust_type_to_python(rust_type: str) -> str:
    """Convert a Rust type to Python type hint."""
    # Remove leading/trailing whitespace
    rust_type = rust_type.strip()

    # First, sanitize Rust-specific syntax
    rust_type = sanitize_rust_type(rust_type)

    # If sanitization returned "object", use it directly
    if rust_type == "object":
        return "object"

    # Direct mapping
    if rust_type in RUST_TO_PYTHON_TYPES:
        return RUST_TO_PYTHON_TYPES[rust_type]

    # Handle reference types
    if rust_type.startswith("&"):
        inner = rust_type[1:].strip()
        return rust_type_to_python(inner)

    # Handle Option<T>
    if rust_type.startswith("Option<") and rust_type.endswith(">"):
        inner = rust_type[7:-1]
        return f"{rust_type_to_python(inner)} | None"

    # Handle Result<T, E>
    if rust_type.startswith("Result<") and rust_type.endswith(">"):
        # Just use the Ok type for simplicity
        inner = rust_type[7:-1]
        # Find the first comma at depth 0
        depth = 0
        for i, c in enumerate(inner):
            if c == "<":
                depth += 1
            elif c == ">":
                depth -= 1
            elif c == "," and depth == 0:
                inner = inner[:i]
                break
        return rust_type_to_python(inner)

    # Handle Vec<T>
    if rust_type.startswith("Vec<") and rust_type.endswith(">"):
        inner = rust_type[4:-1]
        return f"list[{rust_type_to_python(inner)}]"

    # Handle HashMap<K, V>
    if rust_type.startswith("HashMap<") and rust_type.endswith(">"):
        inner = rust_type[8:-1]
        # Find comma at depth 0
        depth = 0
        for i, c in enumerate(inner):
            if c == "<":
                depth += 1
            elif c == ">":
                depth -= 1
            elif c == "," and depth == 0:
                key = inner[:i].strip()
                value = inner[i + 1 :].strip()
                return f"dict[{rust_type_to_python(key)}, {rust_type_to_python(value)}]"
        return "dict"

    # Handle Box<T>
    if rust_type.startswith("Box<") and rust_type.endswith(">"):
        inner = rust_type[4:-1]
        return rust_type_to_python(inner)

    # Handle Box<dyn ...> (dynamic trait object - use object)
    if rust_type.startswith("Box<") and "dyn" in rust_type:
        return "object"

    # Handle Self
    if rust_type == "Self":
        return "Self"

    # Handle path types like crate::module::Type
    # Only apply if :: is outside of angle brackets (not inside generics)
    if "::" in rust_type:
        # Check if :: is inside angle brackets
        depth = 0
        outside_brackets = True
        for i, c in enumerate(rust_type):
            if c == "<":
                depth += 1
            elif c == ">":
                depth -= 1
            elif rust_type[i : i + 2] == "::" and depth == 0:
                # Found :: outside brackets, safe to split
                outside_brackets = True
                break
            elif rust_type[i : i + 2] == "::" and depth > 0:
                # Found :: inside brackets, not safe to split
                outside_brackets = False
                break

        if outside_brackets and depth == 0:
            # Split on the last :: that's outside brackets
            last_sep = -1
            depth = 0
            for i, c in enumerate(rust_type):
                if c == "<":
                    depth += 1
                elif c == ">":
                    depth -= 1
                elif rust_type[i : i + 2] == "::" and depth == 0:
                    last_sep = i
            if last_sep >= 0:
                # Recursively process the remaining type after stripping namespace
                return rust_type_to_python(rust_type[last_sep + 2 :])
        else:
            # :: is inside angle brackets (associated type like U::Target)
            # This is too complex to represent in Python, use object
            return "object"

    # Handle standard library error types
    if rust_type in ("StdError", "Error", "std::error::Error"):
        return "Exception"

    # Handle impl Trait (just use object for now)
    if rust_type.startswith("impl "):
        return "object"

    # Final validation - catch any remaining invalid Python type syntax
    # Check for unbalanced angle brackets
    if rust_type.count("<") != rust_type.count(">"):
        return "object"

    # Check for > without < (partial generic remnants)
    if ">" in rust_type and "<" not in rust_type:
        return "object"

    # Check for unknown generics with angle brackets (e.g., Ref<T>, Own<T>)
    # These are Rust generics that we don't have mappings for
    if "<" in rust_type and ">" in rust_type:
        # We've handled all known generics above (Option, Result, Vec, HashMap, Box)
        # Any remaining generics are unknown Rust types
        return "object"

    # Default: return the type name as-is (likely a custom type)
    return rust_type


def generate_method_signature(method: RustMethod, type_name: str) -> str:
    """Generate Python method signature from Rust method."""
    params = []

    if method.self_type:
        params.append("self")

    for param in method.params:
        py_type = rust_type_to_python(param.rust_type)
        # Use safe name for parameters too
        safe_param_name = python_safe_name(param.name)
        params.append(f"{safe_param_name}: {py_type}")

    params_str = ", ".join(params)

    # Determine return type
    if method.return_type:
        ret_type = rust_type_to_python(method.return_type)
        # Handle Self return type
        if ret_type == "Self":
            ret_type = "Self"
    else:
        ret_type = "None"

    # Use safe name for method name
    safe_method_name = python_safe_name(method.name)
    return f"def {safe_method_name}({params_str}) -> {ret_type}: ..."


def generate_static_method_signature(method: RustMethod, type_name: str) -> str:
    """Generate Python static method signature from Rust static method."""
    params = []

    for param in method.params:
        py_type = rust_type_to_python(param.rust_type)
        # Use safe name for parameters too
        safe_param_name = python_safe_name(param.name)
        params.append(f"{safe_param_name}: {py_type}")

    params_str = ", ".join(params)

    # Determine return type
    if method.return_type:
        ret_type = rust_type_to_python(method.return_type)
        if ret_type == "Self" or ret_type == type_name:
            ret_type = f'"{type_name}"'
    else:
        ret_type = "None"

    # Use safe name for method name
    safe_method_name = python_safe_name(method.name)
    return f"def {safe_method_name}({params_str}) -> {ret_type}: ..."


def generate_function_signature(func: RustFunction) -> str:
    """Generate Python function signature from Rust free-standing function."""
    params = []

    for param in func.params:
        py_type = rust_type_to_python(param.rust_type)
        safe_param_name = python_safe_name(param.name)
        params.append(f"{safe_param_name}: {py_type}")

    params_str = ", ".join(params)

    # Determine return type
    if func.return_type:
        ret_type = rust_type_to_python(func.return_type)
    else:
        ret_type = "None"

    # Use safe name for function name
    safe_func_name = python_safe_name(func.name)

    # Add async keyword for async functions
    async_kw = "async " if func.is_async else ""
    return f"{async_kw}def {safe_func_name}({params_str}) -> {ret_type}: ..."


def is_result_type_alias(alias: RustTypeAlias) -> bool:
    """Check if this type alias is a Result type (wraps core::result::Result)."""
    target = alias.target_type.lower()
    return "result" in target and ("core::result" in target or "std::result" in target)


def generate_result_class(alias: RustTypeAlias, crate_name: str) -> list[str]:
    """Generate a Result class for a Result type alias."""
    lines = [
        "",
        "T = TypeVar('T')",
        "E = TypeVar('E')",
        "",
        "",
        f"class {alias.name}(Generic[T, E]):",
        f'    """A Result type alias for {crate_name}.',
        "",
        f"    Maps to {crate_name}::{alias.name} which is an alias for {alias.target_type}.",
        '    """',
        "",
        "    @staticmethod",
        f'    def Ok(value: T) -> "{alias.name}[T, E]":',
        '        """Create a successful result."""',
        "        ...",
        "",
        "    @staticmethod",
        f'    def Err(error: E) -> "{alias.name}[T, E]":',
        '        """Create an error result."""',
        "        ...",
    ]
    return lines


def generate_init_py(crate: RustCrate, crate_name: str) -> str:
    """Generate __init__.py content for the stub package."""
    # Check if we need Generic/TypeVar for Result type aliases
    has_result_alias = any(is_result_type_alias(a) for a in crate.type_aliases)

    typing_imports = ["Self"]
    if has_result_alias:
        typing_imports.extend(["TypeVar", "Generic"])

    lines = [
        f'"""Python stubs for the {crate_name} Rust crate.',
        "",
        f"Install with: cookcrab install {crate_name}",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        f"from typing import {', '.join(typing_imports)}",
    ]

    # Generate Result class for Result type aliases
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            lines.extend(generate_result_class(alias, crate_name))

    # Add standard library type stubs (e.g., Duration for tokio)
    std_types_added = []
    for (stub_crate, type_name), (class_code, _rust_type, _func_mappings) in STD_TYPE_STUBS.items():
        if stub_crate == crate_name:
            lines.append(class_code)
            std_types_added.append(type_name)

    # Add standalone function stubs (e.g., spawn for tokio)
    manual_functions_added = []
    for (stub_crate, func_name), (stub_code, _rust_code, _rust_imports, _is_async) in FUNCTION_STUBS.items():
        if stub_crate == crate_name:
            lines.append(stub_code)
            manual_functions_added.append(func_name)

    # Collect all types and their methods
    type_methods: dict[str, list[RustMethod]] = {}
    for impl in crate.impls:
        if impl.type_name not in type_methods:
            type_methods[impl.type_name] = []
        type_methods[impl.type_name].extend(impl.methods)

    # Generate classes for structs
    all_types = []
    for struct in crate.structs:
        all_types.append(struct.name)
        lines.append("")
        if struct.doc:
            lines.append(f"class {struct.name}:")
            lines.append(f'    """{struct.doc}"""')
        else:
            lines.append(f"class {struct.name}:")

        methods = type_methods.get(struct.name, [])
        if not methods:
            lines.append("    pass")
        else:
            for method in methods:
                lines.append("")
                if method.is_static:
                    lines.append("    @staticmethod")
                    sig = generate_static_method_signature(method, struct.name)
                else:
                    sig = generate_method_signature(method, struct.name)
                lines.append(f"    {sig}")

    # Generate classes for enums
    for enum in crate.enums:
        all_types.append(enum.name)
        lines.append("")
        if enum.doc:
            lines.append(f"class {enum.name}:")
            lines.append(f'    """{enum.doc}"""')
        else:
            lines.append(f"class {enum.name}:")

        # Add variants as class attributes
        for variant in enum.variants:
            safe_name = python_safe_name(variant.name)
            lines.append(f'    {safe_name}: "{enum.name}"')

        methods = type_methods.get(enum.name, [])
        if methods:
            for method in methods:
                lines.append("")
                if method.is_static:
                    lines.append("    @staticmethod")
                    sig = generate_static_method_signature(method, enum.name)
                else:
                    sig = generate_method_signature(method, enum.name)
                lines.append(f"    {sig}")

    # Generate free-standing functions
    all_functions = []
    for func in crate.functions:
        if func.is_pub:  # Only export public functions
            safe_name = python_safe_name(func.name)
            all_functions.append(safe_name)
            lines.append("")
            if func.doc:
                lines.append(f'"""{func.doc}"""')
            sig = generate_function_signature(func)
            lines.append(sig)

    # Add Result type aliases to all_types
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            all_types.insert(0, alias.name)  # Put Result first

    # Add __all__ - order: functions, manual stubs, std types, crate types
    lines.append("")
    all_items = all_functions + manual_functions_added + std_types_added + all_types
    all_str = ", ".join(f'"{t}"' for t in all_items)
    lines.append(f"__all__: list[str] = [{all_str}]")
    lines.append("")

    return "\n".join(lines)


def generate_spicycrab_toml(crate: RustCrate, crate_name: str, version: str, python_module: str) -> str:
    """Generate _spicycrab.toml content."""
    lines = [
        "[package]",
        f'name = "{crate_name}"',
        f'rust_crate = "{crate_name}"',
        f'rust_version = "{version}"',
        f'python_module = "{python_module}"',
        "",
        "[cargo.dependencies]",
        f'{crate_name} = "{version}"',
        "",
    ]

    # Collect type names that are handled by STD_TYPE_STUBS to avoid duplicates
    std_type_names: set[str] = {
        type_name for (stub_crate, type_name), _ in STD_TYPE_STUBS.items() if stub_crate == crate_name
    }

    # Generate mappings for Result type aliases (Result.Ok, Result.Err)
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            # Result.Ok -> Ok({arg0})
            lines.append("# Result type alias - Ok constructor")
            lines.append("[[mappings.functions]]")
            lines.append(f'python = "{crate_name}.{alias.name}.Ok"')
            lines.append('rust_code = "Ok({arg0})"')
            lines.append("rust_imports = []")
            lines.append("needs_result = false")
            lines.append("")
            # Result.Err -> Err({arg0})
            lines.append("# Result type alias - Err constructor")
            lines.append("[[mappings.functions]]")
            lines.append(f'python = "{crate_name}.{alias.name}.Err"')
            lines.append('rust_code = "Err({arg0})"')
            lines.append("rust_imports = []")
            lines.append("needs_result = false")
            lines.append("")

    # Generate mappings for standard library types (e.g., Duration for tokio)
    for (stub_crate, type_name), (_class_code, rust_type, func_mappings) in STD_TYPE_STUBS.items():
        if stub_crate == crate_name:
            # Add function mappings for constructors
            for py_suffix, rust_code in func_mappings:
                lines.append(f"# {type_name} constructor from std")
                lines.append("[[mappings.functions]]")
                lines.append(f'python = "{crate_name}.{py_suffix}"')
                lines.append(f'rust_code = "{rust_code}"')
                lines.append("rust_imports = []")
                lines.append("needs_result = false")
                lines.append("")

    # Generate mappings for standalone function stubs (e.g., spawn for tokio)
    for (stub_crate, func_name), (_stub_code, rust_code, rust_imports, is_async) in FUNCTION_STUBS.items():
        if stub_crate == crate_name:
            lines.append(f"# {func_name} standalone function")
            lines.append("[[mappings.functions]]")
            lines.append(f'python = "{crate_name}.{func_name}"')
            lines.append(f'rust_code = "{rust_code}"')
            if rust_imports:
                imports_str = ", ".join(f'"{i}"' for i in rust_imports)
                lines.append(f"rust_imports = [{imports_str}]")
            else:
                lines.append("rust_imports = []")
            lines.append("needs_result = false")
            if is_async:
                lines.append("is_async = true")
            lines.append("")

    # Generate mappings for free-standing functions
    for func in crate.functions:
        if func.is_pub:
            # Generate argument placeholders
            args = ", ".join(f"{{arg{i}}}" for i in range(len(func.params)))
            py_func_name = python_safe_name(func.name)
            param_types = [p.rust_type for p in func.params]
            param_types_str = ", ".join(f'"{t}"' for t in param_types)

            # Check for path overrides (e.g., tokio::sleep -> tokio::time::sleep)
            override_key = (crate_name, func.name)
            if override_key in FUNCTION_PATH_OVERRIDES:
                rust_code_template, rust_imports = FUNCTION_PATH_OVERRIDES[override_key]
                rust_code = rust_code_template
            else:
                rust_code = f"{crate_name}::{func.name}({args})"
                rust_imports = [f"{crate_name}::{func.name}"]

            lines.append("[[mappings.functions]]")
            lines.append(f'python = "{crate_name}.{py_func_name}"')
            lines.append(f'rust_code = "{rust_code}"')
            if rust_imports:
                imports_str = ", ".join(f'"{i}"' for i in rust_imports)
                lines.append(f"rust_imports = [{imports_str}]")
            else:
                lines.append("rust_imports = []")
            # Check if function returns a Result type
            needs_result_val = "true" if returns_result(func.return_type) else "false"
            lines.append(f"needs_result = {needs_result_val}")
            if func.is_async:
                lines.append("is_async = true")
            if param_types:
                lines.append(f"param_types = [{param_types_str}]")
            lines.append("")

    # Collect all types and their methods
    type_methods: dict[str, list[RustMethod]] = {}
    for impl in crate.impls:
        if impl.type_name not in type_methods:
            type_methods[impl.type_name] = []
        type_methods[impl.type_name].extend(impl.methods)

    # Generate function mappings (static methods / constructors)
    # Skip structs that are handled by STD_TYPE_STUBS to avoid duplicate/conflicting mappings
    for struct in crate.structs:
        if struct.name in std_type_names:
            continue
        methods = type_methods.get(struct.name, [])
        for method in methods:
            if method.is_static:
                # Generate argument placeholders
                args = ", ".join(f"{{arg{i}}}" for i in range(len(method.params)))
                # Use safe name for Python, original for Rust
                py_method_name = python_safe_name(method.name)
                # Collect param types for type-aware argument transformation
                param_types = [p.rust_type for p in method.params]
                param_types_str = ", ".join(f'"{t}"' for t in param_types)

                # Check if method returns a Result type
                needs_result_val = "true" if returns_result(method.return_type) else "false"

                # Special case: Error.msg in anyhow should use anyhow! macro
                if struct.name == "Error" and method.name == "msg" and crate_name == "anyhow":
                    lines.append("# Error.msg - use anyhow! macro for string messages")
                    lines.append("[[mappings.functions]]")
                    lines.append(f'python = "{crate_name}.{struct.name}.{py_method_name}"')
                    lines.append(f'rust_code = "{crate_name}::anyhow!({args})"')
                    lines.append("rust_imports = []")
                    lines.append(f"needs_result = {needs_result_val}")
                    if param_types:
                        lines.append(f"param_types = [{param_types_str}]")
                    lines.append("")
                else:
                    lines.append("[[mappings.functions]]")
                    lines.append(f'python = "{crate_name}.{struct.name}.{py_method_name}"')
                    lines.append(f'rust_code = "{crate_name}::{struct.name}::{method.name}({args})"')
                    lines.append(f'rust_imports = ["{crate_name}::{struct.name}"]')
                    lines.append(f"needs_result = {needs_result_val}")
                    if param_types:
                        lines.append(f"param_types = [{param_types_str}]")
                    lines.append("")

    # Generate method mappings (instance methods)
    # Get trait method imports for this crate
    crate_trait_methods = TRAIT_METHOD_IMPORTS.get(crate_name, {})

    # Skip structs that are handled by STD_TYPE_STUBS
    for struct in crate.structs:
        if struct.name in std_type_names:
            continue
        methods = type_methods.get(struct.name, [])
        for method in methods:
            if not method.is_static:
                # Generate argument placeholders
                args = ", ".join(f"{{arg{i}}}" for i in range(len(method.params)))
                # Use safe name for Python, original for Rust
                py_method_name = python_safe_name(method.name)
                # Collect param types for type-aware argument transformation
                param_types = [p.rust_type for p in method.params]
                param_types_str = ", ".join(f'"{t}"' for t in param_types)
                returns_self = method.return_type and (
                    "Self" in method.return_type or struct.name in method.return_type
                )

                # Check if this method requires a trait import
                trait_import = crate_trait_methods.get(method.name, "")
                rust_imports = [trait_import] if trait_import else []

                # Check if return type needs conversion to i64 (Python int)
                # Small integer types (i32, u32, i16, u16, etc.) need explicit cast
                # Use "as i64" instead of ".into()" to avoid ambiguity in format contexts
                needs_cast = method.return_type in {"i8", "i16", "i32", "u8", "u16", "u32"}
                into_suffix = " as i64" if needs_cast else ""

                # Check if method returns a Result type
                needs_result_val = "true" if returns_result(method.return_type) else "false"

                # Extract return type for method chaining
                returns_type = extract_return_type_name(method.return_type, struct.name)

                lines.append("[[mappings.methods]]")
                lines.append(f'python = "{struct.name}.{py_method_name}"')
                if args:
                    lines.append(f'rust_code = "{{self}}.{method.name}({args}){into_suffix}"')
                else:
                    lines.append(f'rust_code = "{{self}}.{method.name}(){into_suffix}"')
                if rust_imports:
                    imports_str = ", ".join(f'"{i}"' for i in rust_imports)
                    lines.append(f"rust_imports = [{imports_str}]")
                else:
                    lines.append("rust_imports = []")
                lines.append(f"needs_result = {needs_result_val}")
                if returns_self:
                    lines.append("returns_self = true")
                if returns_type:
                    lines.append(f'returns = "{returns_type}"')
                if param_types:
                    lines.append(f"param_types = [{param_types_str}]")
                lines.append("")

    # Generate type mappings for Result type aliases
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            lines.append("# Result type alias")
            lines.append("[[mappings.types]]")
            lines.append(f'python = "{alias.name}"')
            lines.append(f'rust = "{crate_name}::{alias.name}"')
            lines.append("")

    # Generate type mappings for standard library types
    for (stub_crate, type_name), (_class_code, rust_type, _func_mappings) in STD_TYPE_STUBS.items():
        if stub_crate == crate_name:
            lines.append(f"# {type_name} from std")
            lines.append("[[mappings.types]]")
            lines.append(f'python = "{type_name}"')
            lines.append(f'rust = "{rust_type}"')
            lines.append("")

    # Generate type mappings for structs (skip those handled by STD_TYPE_STUBS)
    for struct in crate.structs:
        if struct.name in std_type_names:
            continue
        lines.append("[[mappings.types]]")
        lines.append(f'python = "{struct.name}"')
        lines.append(f'rust = "{crate_name}::{struct.name}"')
        lines.append("")

    for enum in crate.enums:
        if enum.name in std_type_names:
            continue
        lines.append("[[mappings.types]]")
        lines.append(f'python = "{enum.name}"')
        lines.append(f'rust = "{crate_name}::{enum.name}"')
        lines.append("")

    return "\n".join(lines)


def generate_pyproject_toml(crate_name: str, version: str, python_module: str) -> str:
    """Generate pyproject.toml content."""
    return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "spicycrab-{crate_name}"
version = "{version}"
description = "spicycrab type stubs for the {crate_name} Rust crate"
requires-python = ">=3.11"
dependencies = []

[project.entry-points."spicycrab.stubs"]
{crate_name} = "{python_module}"

[tool.hatch.build.targets.wheel]
packages = ["{python_module}"]
'''


def generate_reexport_init_py(crate_name: str, source_crates: list[str]) -> str:
    """Generate __init__.py that re-exports from source crate stubs."""
    lines = [
        f'"""Python stubs for the {crate_name} Rust crate.',
        "",
        f"This crate re-exports from: {', '.join(source_crates)}",
        '"""',
        "",
        "from __future__ import annotations",
        "",
    ]

    # Import and re-export from each source crate
    for source in source_crates:
        source_module = f"spicycrab_{source.replace('-', '_')}"
        lines.append(f"from {source_module} import *  # noqa: F401, F403")

    lines.append("")
    return "\n".join(lines)


def generate_reexport_toml(
    crate_name: str,
    source_crates: list[str],
    version: str,
    python_module: str,
    output_dir: Path,
) -> str:
    """Generate _spicycrab.toml that copies and rewrites mappings from source crate stubs.

    Reads the generated source crate toml files and rewrites:
    - clap_builder -> clap (or whatever the re-export crate is)
    - python paths: clap_builder.X -> clap.X
    - rust_code: clap_builder::X -> clap::X (since clap re-exports clap_builder)
    - rust_imports: same
    """
    lines = [
        "[package]",
        f'name = "{crate_name}"',
        f'rust_crate = "{crate_name}"',
        f'rust_version = "{version}"',
        f'python_module = "{python_module}"',
        "",
        "# This crate re-exports from other crates",
        f"# Source crates: {', '.join(source_crates)}",
        "",
        "[cargo.dependencies]",
        f'{crate_name} = "{version}"',
        "",
    ]

    # Read and rewrite mappings from each source crate
    for source_crate in source_crates:
        source_module = f"spicycrab_{source_crate.replace('-', '_')}"
        source_toml_path = output_dir / source_crate / source_module / "_spicycrab.toml"

        if not source_toml_path.exists():
            continue

        source_content = source_toml_path.read_text()

        # Find and copy all [[mappings.functions]] and [[mappings.methods]] blocks
        in_mapping_block = False
        current_block: list[str] = []

        for line in source_content.split("\n"):
            if line.startswith("[[mappings."):
                if current_block and in_mapping_block:
                    # Process and add the previous block
                    rewritten_block = _rewrite_mapping_block(current_block, source_crate, crate_name)
                    lines.extend(rewritten_block)
                    lines.append("")
                current_block = [line]
                in_mapping_block = True
            elif in_mapping_block:
                if line.startswith("[") and not line.startswith("[["):
                    # End of mappings section
                    if current_block:
                        rewritten_block = _rewrite_mapping_block(current_block, source_crate, crate_name)
                        lines.extend(rewritten_block)
                        lines.append("")
                    in_mapping_block = False
                    current_block = []
                else:
                    current_block.append(line)

        # Process last block if any
        if current_block and in_mapping_block:
            rewritten_block = _rewrite_mapping_block(current_block, source_crate, crate_name)
            lines.extend(rewritten_block)
            lines.append("")

    return "\n".join(lines)


def _rewrite_mapping_block(block: list[str], source_crate: str, target_crate: str) -> list[str]:
    """Rewrite a mapping block, replacing source crate references with target crate."""
    result = []
    for line in block:
        # Rewrite python paths: clap_builder.X -> clap.X
        if line.startswith("python = "):
            line = line.replace(f'"{source_crate}.', f'"{target_crate}.')
        # Rewrite rust_code: clap_builder:: -> clap::
        elif line.startswith("rust_code = "):
            line = line.replace(f"{source_crate}::", f"{target_crate}::")
        # Rewrite rust_imports: ["clap_builder::X"] -> ["clap::X"]
        elif line.startswith("rust_imports = "):
            line = line.replace(f'"{source_crate}::', f'"{target_crate}::')
        result.append(line)
    return result


def generate_reexport_pyproject(crate_name: str, source_crates: list[str], version: str, python_module: str) -> str:
    """Generate pyproject.toml with dependencies on source crate stubs."""
    deps = ", ".join(f'"spicycrab-{s}"' for s in source_crates)
    return f'''[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "spicycrab-{crate_name}"
version = "{version}"
description = "spicycrab type stubs for the {crate_name} Rust crate (re-exports from {", ".join(source_crates)})"
requires-python = ">=3.11"
dependencies = [{deps}]

[project.entry-points."spicycrab.stubs"]
{crate_name} = "{python_module}"

[tool.hatch.build.targets.wheel]
packages = ["{python_module}"]
'''


def generate_reexport_stub_package(
    crate_name: str,
    source_crates: list[str],
    version: str,
    output_dir: Path,
) -> None:
    """Generate a stub package that re-exports from source crate stubs.

    Args:
        crate_name: Name of the wrapper crate (e.g., "clap")
        source_crates: Names of source crates (e.g., ["clap_builder"])
        version: Crate version
        output_dir: Directory to write the stub package to
    """
    python_module = f"spicycrab_{crate_name.replace('-', '_')}"

    # Generate content
    init_py = generate_reexport_init_py(crate_name, source_crates)
    spicycrab_toml = generate_reexport_toml(crate_name, source_crates, version, python_module, output_dir)
    pyproject_toml = generate_reexport_pyproject(crate_name, source_crates, version, python_module)

    # Create output directory structure
    pkg_dir = output_dir / crate_name / python_module
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Write files
    (output_dir / crate_name / "pyproject.toml").write_text(pyproject_toml)
    (pkg_dir / "__init__.py").write_text(init_py)
    (pkg_dir / "_spicycrab.toml").write_text(spicycrab_toml)

    # Create README
    readme = f"""# spicycrab-{crate_name}

Python type stubs for the [{crate_name}](https://crates.io/crates/{crate_name}) Rust crate.

This crate re-exports from: {", ".join(source_crates)}

**Install with cookcrab, NOT pip:**

```bash
cookcrab install {crate_name}
```

## Usage

```python
from {python_module} import Command, Arg, ...
```

## Dependencies

This package depends on:
{chr(10).join(f"- spicycrab-{s}" for s in source_crates)}
"""
    (output_dir / crate_name / "README.md").write_text(readme)


def generate_stub_package(
    crate: RustCrate,
    crate_name: str,
    version: str,
    output_dir: Path,
    source_crates: list[str] | None = None,
) -> GeneratedStub:
    """Generate a complete stub package from a parsed Rust crate.

    Args:
        crate: Parsed Rust crate from the parser
        crate_name: Name of the crate
        version: Crate version
        output_dir: Directory to write the stub package to

    Returns:
        GeneratedStub with the generated content
    """
    # Normalize crate name for Python module
    python_module = f"spicycrab_{crate_name.replace('-', '_')}"

    # Generate content
    init_py = generate_init_py(crate, crate_name)
    spicycrab_toml = generate_spicycrab_toml(crate, crate_name, version, python_module)
    pyproject_toml = generate_pyproject_toml(crate_name, version, python_module)

    # Create output directory structure
    pkg_dir = output_dir / crate_name / python_module
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Write files
    (output_dir / crate_name / "pyproject.toml").write_text(pyproject_toml)
    (pkg_dir / "__init__.py").write_text(init_py)
    (pkg_dir / "_spicycrab.toml").write_text(spicycrab_toml)

    # Create README
    readme = f"""# spicycrab-{crate_name}

Python type stubs for the [{crate_name}](https://crates.io/crates/{crate_name}) Rust crate.

**Install with cookcrab, NOT pip:**

```bash
cookcrab install {crate_name}
```

## Usage

```python
from {python_module} import ...
```
"""
    (output_dir / crate_name / "README.md").write_text(readme)

    return GeneratedStub(
        crate_name=crate_name,
        version=version,
        python_module=python_module,
        init_py=init_py,
        spicycrab_toml=spicycrab_toml,
        pyproject_toml=pyproject_toml,
    )
