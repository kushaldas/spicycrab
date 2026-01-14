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

from spicycrab.debug_log import increment, log_decision

if TYPE_CHECKING:
    from spicycrab.cookcrab._parser import (
        RustCrate,
        RustFunction,
        RustMethod,
        RustParam,
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


def make_unique_param_names(params: list) -> list[str]:
    """Make parameter names unique, handling duplicate `_` parameters.

    Rust allows multiple parameters named `_` (unused), but Python doesn't.
    This function renames duplicates to `_1`, `_2`, etc.
    """
    seen: dict[str, int] = {}
    result: list[str] = []

    for param in params:
        name = param.name
        safe_name = python_safe_name(name)

        if safe_name in seen:
            # Duplicate found, add suffix
            count = seen[safe_name]
            seen[safe_name] = count + 1
            unique_name = f"{safe_name}{count}"
        else:
            seen[safe_name] = 1
            unique_name = safe_name

        result.append(unique_name)

    return result


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


# Common private module names in Rust crates
# These modules typically contain implementation details and types are re-exported at parent level
COMMON_PRIVATE_MODULES: set[str] = {
    # Organization patterns
    "builder",
    "builders",
    "parser",
    "parsers",
    "matches",
    "matcher",
    "internal",
    "private",
    "detail",
    "details",
    "impl",
    "impls",
    "core",
    "util",
    "utils",
    "helper",
    "helpers",
    "common",
    "types",
    "primitives",
    # Specific patterns
    "alg",
    "algorithm",
    "algorithms",
    "direct",  # josekit: jwe::alg::direct
    "enc",
    "encoding",
    "dec",
    "decoding",
    "ser",
    "de",
    "fmt",
    "format",
    "io",
    "net",
    "sync",
    "async_impl",
    "blocking",
    "runtime",
    "error",
    "errors",
    "result",
    # clap internal modules
    "command",
    "arg",
    # reqwest internal modules
    "response",
    "request",
    "client",
    "wasm",
    # config crate internal modules
    "config",  # config::config::Config -> config::Config
    "file",
    "value",
    "source",
    # Date/time patterns (chrono)
    "naive",
    "datetime",
    "date",
    "time",
    "local",
    "utc",
    "offset",
    "duration",
    "weekday",
    "month",
    "fixed",
    # Logging patterns
    "log_impl",
    "logger",
    "logging",
    # Block API patterns (sha2, digest crates)
    "block_api",
    # TLS/rustls internal modules
    "webpki",
    "anchors",
    "verify",
    "server_conn",
    "client_conn",
    "conn",
    "tls12",
    "tls13",
    "ciphersuites",
    "suites",
    # native-tls internal modules (platform-specific implementations)
    "imp",
    "schannel",
    "security_framework",
    "openssl",
}


def _is_private_module_component(component: str, snake_name: str) -> bool:
    """Check if a module component looks like a private submodule for a type.

    Private submodules are detected by:
    1. Component is in the common private modules list
    2. Exact match with snake_case type name ONLY if it's a compound name (has underscores)
    3. Snake_name ends with component (e.g., arg_matches ends with matches)
       but component must be substantial (>= 50% of snake_name length)

    We are conservative to avoid stripping public submodule names like:
    - jws in jws_header (jws is a real public module)
    - jwt in jwt_payload (jwt is a real public module)
    - jwk in Jwk (jwk is the public module where Jwk lives)
    """
    # Check against common private module names
    if component in COMMON_PRIVATE_MODULES:
        return True

    # Exact match with compound names only (e.g., jws_header for JwsHeader)
    # For simple names like Jwk in jwk, the module is likely public, not private
    if component == snake_name and "_" in snake_name:
        return True

    # Snake_name ends with _component and component is substantial
    # e.g., arg_matches ends with matches, so strip "matches" module
    suffix_with_underscore = f"_{component}"
    if snake_name.endswith(suffix_with_underscore) and len(component) >= len(snake_name) * 0.5:
        return True

    return False


def get_public_module_path(module_path: str, type_name: str) -> str:
    """Get the public module path for a type.

    Many Rust crates define types in private submodules and re-export them
    at the parent level. For example:
    - JwsHeader is defined in jws::jws_header but re-exported as jws::JwsHeader
    - ArgMatches is defined in parser::matches but re-exported as clap::ArgMatches
    - Command is defined in builder::command but re-exported as clap::Command
    - Jwk is defined in jwk::jwk but re-exported as jwk::Jwk

    This function recursively strips private module components until we reach
    a public-looking path. It uses heuristics to detect private submodules:
    1. Component is a common private module name (builder, parser, internal, etc.)
    2. Component matches the snake_case type name exactly (only for compound names)
    3. Snake_case type name contains the component
    4. Repeated module name (e.g., jwk::jwk -> jwk)

    Returns empty string if the type appears to be exported at the crate root.
    """
    if not module_path:
        return ""

    parts = module_path.split("::")
    if not parts:
        return module_path

    # Get the snake_case version of the type name
    snake_name = camel_to_snake(type_name)

    # First, strip repeated module components (e.g., jwk::jwk -> jwk)
    # This handles cases like josekit::jwk::jwk::Jwk -> josekit::jwk::Jwk
    original_parts_count = len(parts)
    while len(parts) >= 2 and parts[-1] == parts[-2]:
        parts.pop()

    # Then recursively strip private-looking module components from the end
    while parts and _is_private_module_component(parts[-1], snake_name):
        parts.pop()

    result = "::".join(parts)
    if len(parts) != original_parts_count:
        log_decision(
            "module_path_stripped",
            original=module_path,
            result=result,
            type_name=type_name,
        )
        increment("module_paths_stripped")
    return result


def escape_docstring(doc: str) -> str:
    """Escape a string for use in a Python docstring.

    Escapes backslashes to prevent Python from interpreting them as
    escape sequences (e.g., \\u{1f600} in Rust code examples).
    """
    # Escape backslashes so \u doesn't become a unicode escape
    return doc.replace("\\", "\\\\")


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

    # Skip unit type and booleans - no need to track these for chaining
    skip_types = {"()", "bool"}
    if rt in skip_types:
        return None

    # Return primitive types as-is - needed for type coercion (.into())
    # The caller can use this to add type conversions
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
        "char",
        "str",
        "String",
        "usize",
        "isize",
    }
    if rt in primitive_types:
        return rt  # Return the primitive type for type conversion info

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
            ("Arc.strong_count", "std::sync::Arc::strong_count(&{arg0})"),
            ("Arc.weak_count", "std::sync::Arc::weak_count(&{arg0})"),
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
    # =========================================================================
    # actix-web types
    # =========================================================================
    ("actix-web", "HttpResponse"): (
        # Class stub for HttpResponse and HttpResponseBuilder
        '''
class HttpResponse:
    """HTTP response type.

    Use the static methods to create responses with specific status codes,
    then chain builder methods to set body, headers, etc.

    Maps to actix_web::HttpResponse in Rust.

    Example:
        return HttpResponse.Ok().body("Hello World!")
        return HttpResponse.Ok().json({"key": "value"})
        return HttpResponse.NotFound().body("Not found")
    """

    @staticmethod
    def Ok() -> "HttpResponseBuilder":
        """Creates a 200 OK response builder."""
        ...

    @staticmethod
    def Created() -> "HttpResponseBuilder":
        """Creates a 201 Created response builder."""
        ...

    @staticmethod
    def Accepted() -> "HttpResponseBuilder":
        """Creates a 202 Accepted response builder."""
        ...

    @staticmethod
    def NoContent() -> "HttpResponseBuilder":
        """Creates a 204 No Content response builder."""
        ...

    @staticmethod
    def BadRequest() -> "HttpResponseBuilder":
        """Creates a 400 Bad Request response builder."""
        ...

    @staticmethod
    def Unauthorized() -> "HttpResponseBuilder":
        """Creates a 401 Unauthorized response builder."""
        ...

    @staticmethod
    def Forbidden() -> "HttpResponseBuilder":
        """Creates a 403 Forbidden response builder."""
        ...

    @staticmethod
    def NotFound() -> "HttpResponseBuilder":
        """Creates a 404 Not Found response builder."""
        ...

    @staticmethod
    def InternalServerError() -> "HttpResponseBuilder":
        """Creates a 500 Internal Server Error response builder."""
        ...


class HttpResponseBuilder:
    """Builder for constructing HTTP responses.

    Returned by HttpResponse status methods. Chain methods to configure
    the response body, headers, and content type.
    """

    def body(self, data: str) -> "HttpResponse":
        """Set the response body as a string."""
        ...

    def json(self, data: object) -> "HttpResponse":
        """Set the response body as JSON."""
        ...

    def content_type(self, ct: str) -> "HttpResponseBuilder":
        """Set the Content-Type header."""
        ...

    def insert_header(self, header: tuple[str, str]) -> "HttpResponseBuilder":
        """Insert a custom header."""
        ...

    def finish(self) -> "HttpResponse":
        """Finish building and return the response."""
        ...
''',
        # Type mapping
        "actix_web::HttpResponse",
        # Function mappings for static constructors
        [
            ("HttpResponse.Ok", "actix_web::HttpResponse::Ok()"),
            ("HttpResponse.Created", "actix_web::HttpResponse::Created()"),
            ("HttpResponse.Accepted", "actix_web::HttpResponse::Accepted()"),
            ("HttpResponse.NoContent", "actix_web::HttpResponse::NoContent()"),
            ("HttpResponse.BadRequest", "actix_web::HttpResponse::BadRequest()"),
            ("HttpResponse.Unauthorized", "actix_web::HttpResponse::Unauthorized()"),
            ("HttpResponse.Forbidden", "actix_web::HttpResponse::Forbidden()"),
            ("HttpResponse.NotFound", "actix_web::HttpResponse::NotFound()"),
            ("HttpResponse.InternalServerError", "actix_web::HttpResponse::InternalServerError()"),
        ],
    ),
    ("actix-web", "App"): (
        # Class stub for App builder
        '''
class App:
    """Application builder for configuring actix-web services.

    Create with App.new(), then chain methods to add routes, middleware,
    and application data.

    Maps to actix_web::App in Rust.

    Example:
        app = App.new().app_data(Data.new(state)).service(handler)
    """

    @staticmethod
    def new() -> "App":
        """Create a new application builder."""
        ...

    def app_data(self, data: object) -> "App":
        """Set application-wide shared data.

        Data is wrapped in web::Data<T> and can be extracted in handlers.
        """
        ...

    def service(self, handler: object) -> "App":
        """Register an HTTP service (handler function)."""
        ...

    def route(self, path: str, route: object) -> "App":
        """Configure a route for a specific path and method."""
        ...

    def wrap(self, middleware: object) -> "App":
        """Wrap the application with middleware."""
        ...

    def configure(self, f: object) -> "App":
        """Run external configuration as part of application building."""
        ...
''',
        # Type mapping
        "actix_web::App",
        # Function mappings
        [
            ("App.new", "actix_web::App::new()"),
        ],
    ),
    ("actix-web", "HttpServer"): (
        # Class stub for HttpServer
        '''
class HttpServer:
    """HTTP server that manages worker threads and connections.

    Create with HttpServer.new() passing an App factory, then configure
    bindings and run the server.

    Maps to actix_web::HttpServer in Rust.

    Example:
        HttpServer.new(lambda: App.new().service(index))
            .bind("127.0.0.1:8080")
            .run()
    """

    @staticmethod
    def new(factory: object) -> "HttpServer":
        """Create a new HTTP server with an application factory.

        The factory is called for each worker thread to create the App.
        """
        ...

    def bind(self, addr: str) -> "HttpServer":
        """Bind to a socket address (e.g., "127.0.0.1:8080")."""
        ...

    def bind_rustls(self, addr: str, config: object) -> "HttpServer":
        """Bind with TLS using rustls."""
        ...

    def workers(self, num: int) -> "HttpServer":
        """Set the number of worker threads (default: number of CPUs)."""
        ...

    async def run(self) -> None:
        """Start the server and wait for it to finish."""
        ...
''',
        # Type mapping
        "actix_web::HttpServer",
        # Function mappings (static constructors only, methods go in STD_METHOD_STUBS)
        [
            ("HttpServer.new", "actix_web::HttpServer::new(move || {arg0})"),
        ],
    ),
    ("actix-web", "Data"): (
        # Class stub for web::Data (shared application state)
        '''
class Data(Generic[T]):
    """Shared application state extractor.

    Wraps data in Arc for thread-safe sharing between handlers.
    Register with App.app_data() and extract in handler parameters.

    Maps to actix_web::web::Data<T> in Rust.

    Example:
        # In main:
        state = Data.new(AppState())
        app = App.new().app_data(state)

        # In handler:
        async def index(data: Data[AppState]) -> HttpResponse:
            return HttpResponse.Ok().body(data.app_name)
    """

    @staticmethod
    def new(value: T) -> "Data[T]":
        """Create new shared application data."""
        ...
''',
        # Type mapping
        "actix_web::web::Data",
        # Function mappings
        [
            ("Data.new", "actix_web::web::Data::new({arg0})"),
        ],
    ),
    ("actix-web", "Query"): (
        # Class stub for web::Query (query string extractor)
        '''
class Query(Generic[T]):
    """Query string parameter extractor.

    Extracts typed data from the URL query string.
    The type T must implement serde::Deserialize.

    Maps to actix_web::web::Query<T> in Rust.

    Example:
        @dataclass
        class Params:
            name: str
            page: int

        async def search(params: Query[Params]) -> HttpResponse:
            return HttpResponse.Ok().body(f"Searching for {params.name}")
    """
    pass
''',
        # Type mapping
        "actix_web::web::Query",
        # No static constructors
        [],
    ),
    ("actix-web", "Json"): (
        # Class stub for web::Json (JSON extractor/responder)
        '''
class Json(Generic[T]):
    """JSON extractor and responder.

    As extractor: Deserializes JSON request body into type T.
    As responder: Serializes type T to JSON response.

    Maps to actix_web::web::Json<T> in Rust.

    Example:
        @dataclass
        class User:
            name: str
            email: str

        async def create_user(user: Json[User]) -> Json[User]:
            # user.name, user.email are accessible
            return Json(user)
    """

    def __init__(self, value: T) -> None:
        """Create a JSON response from a value."""
        ...
''',
        # Type mapping
        "actix_web::web::Json",
        # No static constructors
        [],
    ),
    ("actix-web", "Form"): (
        # Class stub for web::Form (form data extractor)
        '''
class Form(Generic[T]):
    """URL-encoded form data extractor.

    Extracts typed data from application/x-www-form-urlencoded request body.
    The type T must implement serde::Deserialize.

    Maps to actix_web::web::Form<T> in Rust.

    Example:
        @dataclass
        class LoginForm:
            username: str
            password: str

        async def login(form: Form[LoginForm]) -> HttpResponse:
            # form.username, form.password are accessible
            return HttpResponse.Ok().body("Logged in")
    """
    pass
''',
        # Type mapping
        "actix_web::web::Form",
        # No static constructors
        [],
    ),
    ("actix-web", "Path"): (
        # Class stub for web::Path (path parameter extractor)
        '''
class Path(Generic[T]):
    """Path parameter extractor.

    Extracts typed data from URL path segments.
    The type T must implement serde::Deserialize.

    Maps to actix_web::web::Path<T> in Rust.

    Example:
        # Route: /users/{user_id}
        async def get_user(path: Path[int]) -> HttpResponse:
            user_id = path.into_inner()
            return HttpResponse.Ok().body(f"User {user_id}")

        # Multiple params: /users/{user_id}/posts/{post_id}
        @dataclass
        class PathParams:
            user_id: int
            post_id: int

        async def get_post(path: Path[PathParams]) -> HttpResponse:
            return HttpResponse.Ok().body(f"Post {path.post_id}")
    """

    def into_inner(self) -> T:
        """Extract the inner value."""
        ...
''',
        # Type mapping
        "actix_web::web::Path",
        # No static constructors
        [],
    ),
    ("actix-web", "HttpRequest"): (
        # Class stub for HttpRequest
        '''
class HttpRequest:
    """HTTP request type.

    Contains request metadata like method, URI, headers, etc.
    Can be extracted in handlers when you need low-level access.

    Maps to actix_web::HttpRequest in Rust.

    Example:
        async def handler(req: HttpRequest) -> HttpResponse:
            method = req.method()
            path = req.path()
            return HttpResponse.Ok().body(f"{method} {path}")
    """

    def method(self) -> str:
        """Get the HTTP method."""
        ...

    def uri(self) -> str:
        """Get the request URI."""
        ...

    def path(self) -> str:
        """Get the URL path."""
        ...

    def query_string(self) -> str:
        """Get the raw query string."""
        ...

    def headers(self) -> object:
        """Get request headers."""
        ...
''',
        # Type mapping
        "actix_web::HttpRequest",
        # No static constructors
        [],
    ),
    ("actix-web", "Route"): (
        # Class stub for web::Route (route configuration)
        '''
class Route:
    """Route configuration for HTTP method handlers.

    Created by web::get(), web::post(), etc. functions.
    Use .to() to attach a handler function.

    Maps to actix_web::web::Route in Rust.

    Example:
        # Register a GET route
        app = App.new().route("/", get().to(index))

        # Register a POST route
        app = App.new().route("/submit", post().to(submit_handler))
    """

    def to(self, handler: object) -> "Route":
        """Attach a handler function to this route.

        The handler must be an async function that returns an HttpResponse
        or impl Responder.
        """
        ...
''',
        # Type mapping
        "actix_web::web::Route",
        # No static constructors (instance method to() is in STD_METHOD_STUBS)
        [],
    ),
    # =========================================================================
    # clap/clap_builder types
    # =========================================================================
    ("clap_builder", "ArgAction"): (
        # Class stub for ArgAction enum
        '''
class ArgAction:
    """Behavior of arguments when they are encountered while parsing.

    Maps to clap::builder::ArgAction in Rust.

    Common variants:
    - SetTrue: Flag that sets to true when present
    - SetFalse: Flag that sets to false when present
    - Set: Store a single value (default)
    - Append: Collect multiple values
    - Count: Count occurrences

    Example:
        cmd.arg(Arg.new("verbose").short("v").action(ArgAction.SetTrue()))
    """

    @staticmethod
    def SetTrue() -> "ArgAction":
        """Flag that sets to true when present."""
        ...

    @staticmethod
    def SetFalse() -> "ArgAction":
        """Flag that sets to false when present."""
        ...

    @staticmethod
    def Set() -> "ArgAction":
        """Store a single value (default behavior)."""
        ...

    @staticmethod
    def Append() -> "ArgAction":
        """Collect multiple occurrences into a Vec."""
        ...

    @staticmethod
    def Count() -> "ArgAction":
        """Count the number of occurrences."""
        ...

    @staticmethod
    def Help() -> "ArgAction":
        """Print help and exit."""
        ...

    @staticmethod
    def Version() -> "ArgAction":
        """Print version and exit."""
        ...
''',
        # Type mapping
        "clap_builder::ArgAction",
        # Function mappings for enum variant constructors
        [
            ("ArgAction.SetTrue", "clap_builder::ArgAction::SetTrue"),
            ("ArgAction.SetFalse", "clap_builder::ArgAction::SetFalse"),
            ("ArgAction.Set", "clap_builder::ArgAction::Set"),
            ("ArgAction.Append", "clap_builder::ArgAction::Append"),
            ("ArgAction.Count", "clap_builder::ArgAction::Count"),
            ("ArgAction.Help", "clap_builder::ArgAction::Help"),
            ("ArgAction.Version", "clap_builder::ArgAction::Version"),
        ],
    ),
    ("clap_builder", "ValueHint"): (
        # Class stub for ValueHint enum
        '''
class ValueHint:
    """Provide shell completion hints for argument values.

    Maps to clap::builder::ValueHint in Rust.

    Example:
        cmd.arg(Arg.new("file").value_hint(ValueHint.FilePath()))
    """

    @staticmethod
    def Unknown() -> "ValueHint":
        """Unknown hint (default)."""
        ...

    @staticmethod
    def Other() -> "ValueHint":
        """Other type."""
        ...

    @staticmethod
    def AnyPath() -> "ValueHint":
        """Any path (file or directory)."""
        ...

    @staticmethod
    def FilePath() -> "ValueHint":
        """Path to a file."""
        ...

    @staticmethod
    def DirPath() -> "ValueHint":
        """Path to a directory."""
        ...

    @staticmethod
    def ExecutablePath() -> "ValueHint":
        """Path to an executable."""
        ...

    @staticmethod
    def CommandName() -> "ValueHint":
        """Command name."""
        ...

    @staticmethod
    def CommandString() -> "ValueHint":
        """Command string."""
        ...

    @staticmethod
    def CommandWithArguments() -> "ValueHint":
        """Command with arguments."""
        ...

    @staticmethod
    def Username() -> "ValueHint":
        """Username."""
        ...

    @staticmethod
    def Hostname() -> "ValueHint":
        """Hostname."""
        ...

    @staticmethod
    def Url() -> "ValueHint":
        """URL."""
        ...

    @staticmethod
    def EmailAddress() -> "ValueHint":
        """Email address."""
        ...
''',
        # Type mapping
        "clap_builder::ValueHint",
        # Function mappings for enum variant constructors
        [
            ("ValueHint.Unknown", "clap_builder::ValueHint::Unknown"),
            ("ValueHint.Other", "clap_builder::ValueHint::Other"),
            ("ValueHint.AnyPath", "clap_builder::ValueHint::AnyPath"),
            ("ValueHint.FilePath", "clap_builder::ValueHint::FilePath"),
            ("ValueHint.DirPath", "clap_builder::ValueHint::DirPath"),
            ("ValueHint.ExecutablePath", "clap_builder::ValueHint::ExecutablePath"),
            ("ValueHint.CommandName", "clap_builder::ValueHint::CommandName"),
            ("ValueHint.CommandString", "clap_builder::ValueHint::CommandString"),
            ("ValueHint.CommandWithArguments", "clap_builder::ValueHint::CommandWithArguments"),
            ("ValueHint.Username", "clap_builder::ValueHint::Username"),
            ("ValueHint.Hostname", "clap_builder::ValueHint::Hostname"),
            ("ValueHint.Url", "clap_builder::ValueHint::Url"),
            ("ValueHint.EmailAddress", "clap_builder::ValueHint::EmailAddress"),
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
    # =========================================================================
    # actix-web error functions
    # =========================================================================
    ("actix-web", "ErrorBadRequest"): (
        '''
def ErrorBadRequest(msg: str) -> object:
    """Create a 400 Bad Request error.

    Use in handlers to return an error response.

    Example:
        if not valid:
            return Err(ErrorBadRequest("Invalid input"))
    """
    ...
''',
        "actix_web::error::ErrorBadRequest({arg0})",
        ["actix_web::error"],
        False,
    ),
    ("actix-web", "ErrorUnauthorized"): (
        '''
def ErrorUnauthorized(msg: str) -> object:
    """Create a 401 Unauthorized error."""
    ...
''',
        "actix_web::error::ErrorUnauthorized({arg0})",
        ["actix_web::error"],
        False,
    ),
    ("actix-web", "ErrorForbidden"): (
        '''
def ErrorForbidden(msg: str) -> object:
    """Create a 403 Forbidden error."""
    ...
''',
        "actix_web::error::ErrorForbidden({arg0})",
        ["actix_web::error"],
        False,
    ),
    ("actix-web", "ErrorNotFound"): (
        '''
def ErrorNotFound(msg: str) -> object:
    """Create a 404 Not Found error."""
    ...
''',
        "actix_web::error::ErrorNotFound({arg0})",
        ["actix_web::error"],
        False,
    ),
    ("actix-web", "ErrorInternalServerError"): (
        '''
def ErrorInternalServerError(msg: str) -> object:
    """Create a 500 Internal Server Error."""
    ...
''',
        "actix_web::error::ErrorInternalServerError({arg0})",
        ["actix_web::error"],
        False,
    ),
    ("actix-web", "get"): (
        '''
def get() -> object:
    """Create a GET route configuration.

    Use with App.route() to configure a GET endpoint.

    Example:
        App.new().route("/", get().to(handler))
    """
    ...
''',
        "actix_web::web::get()",
        [],  # No import needed - using fully-qualified path
        False,
    ),
    ("actix-web", "post"): (
        '''
def post() -> object:
    """Create a POST route configuration."""
    ...
''',
        "actix_web::web::post()",
        [],  # No import needed - using fully-qualified path
        False,
    ),
    ("actix-web", "put"): (
        '''
def put() -> object:
    """Create a PUT route configuration."""
    ...
''',
        "actix_web::web::put()",
        [],  # No import needed - using fully-qualified path
        False,
    ),
    ("actix-web", "delete"): (
        '''
def delete() -> object:
    """Create a DELETE route configuration."""
    ...
''',
        "actix_web::web::delete()",
        [],  # No import needed - using fully-qualified path
        False,
    ),
    ("actix-web", "patch"): (
        '''
def patch() -> object:
    """Create a PATCH route configuration."""
    ...
''',
        "actix_web::web::patch()",
        [],  # No import needed - using fully-qualified path
        False,
    ),
}


# Hardcoded method stubs for specific method behaviors not captured by parser
# Format: (crate_name, type_name, method_name) -> (rust_code, returns_self, needs_result, returns_type, param_types)
# rust_code uses {self} for receiver and {arg0}, {arg1} etc for arguments
# param_types: list of Rust type strings for each parameter (used to transform args, e.g., &str prevents .to_string())
STD_METHOD_STUBS: dict[tuple[str, str, str], tuple[str, bool, bool, str | None, list[str] | None]] = {
    # actix-web HttpServer methods
    ("actix-web", "HttpServer", "bind"): (
        "{self}.bind({arg0}).unwrap()",  # bind returns Result, unwrap it
        True,  # returns_self
        False,  # needs_result (we already unwrap)
        None,  # returns_type
        ["&str"],  # param_types: bind takes &str address
    ),
    ("actix-web", "HttpServer", "run"): (
        "{self}.run().await",  # run() returns Server, need .await
        False,  # returns_self
        False,  # needs_result
        None,  # returns_type
        None,  # param_types
    ),
    # actix-web App methods
    ("actix-web", "App", "route"): (
        "{self}.route({arg0}, {arg1})",
        True,  # returns_self for chaining
        False,  # needs_result
        None,  # returns_type
        ["&str"],  # param_types: route takes &str path, then Route
    ),
    # actix-web Route methods
    ("actix-web", "Route", "to"): (
        "{self}.to({arg0})",
        True,  # returns_self for chaining
        False,  # needs_result
        None,  # returns_type
        None,  # param_types
    ),
    # redis Cmd async methods - convenience wrappers that include .await
    ("redis", "Cmd", "query_async_await"): (
        "{self}.query_async({arg0}).await",
        False,  # returns_self
        True,  # needs_result - adds ? after .await
        None,  # returns_type
        ["&mut ConnectionManager"],  # param_types
    ),
    # redis Client async methods
    ("redis", "Client", "get_connection_manager_await"): (
        "{self}.get_connection_manager().await",
        False,  # returns_self
        True,  # needs_result - adds ?
        "ConnectionManager",  # returns_type
        None,  # param_types
    ),
    # base64 Engine trait method
    ("base64", "URL_SAFE_NO_PAD", "decode"): (
        "base64::engine::general_purpose::URL_SAFE_NO_PAD.decode({arg0})",
        False,  # returns_self
        True,  # needs_result - decode returns Result
        "Vec<u8>",  # returns_type
        ["&[u8]"],  # param_types
    ),
    ("base64", "STANDARD", "decode"): (
        "base64::engine::general_purpose::STANDARD.decode({arg0})",
        False,  # returns_self
        True,  # needs_result
        "Vec<u8>",  # returns_type
        ["&[u8]"],  # param_types
    ),
    ("base64", "STANDARD_NO_PAD", "decode"): (
        "base64::engine::general_purpose::STANDARD_NO_PAD.decode({arg0})",
        False,  # returns_self
        True,  # needs_result
        "Vec<u8>",  # returns_type
        ["&[u8]"],  # param_types
    ),
    ("base64", "URL_SAFE", "decode"): (
        "base64::engine::general_purpose::URL_SAFE.decode({arg0})",
        False,  # returns_self
        True,  # needs_result
        "Vec<u8>",  # returns_type
        ["&[u8]"],  # param_types
    ),
    ("base64", "URL_SAFE_NO_PAD", "encode"): (
        "base64::engine::general_purpose::URL_SAFE_NO_PAD.encode({arg0})",
        False,  # returns_self
        False,  # needs_result - encode returns String
        "String",  # returns_type
        ["&[u8]"],  # param_types
    ),
    ("base64", "STANDARD", "encode"): (
        "base64::engine::general_purpose::STANDARD.encode({arg0})",
        False,  # returns_self
        False,  # needs_result
        "String",  # returns_type
        ["&[u8]"],  # param_types
    ),
    # josekit JwtPayload convenience methods
    ("josekit", "JwtPayload", "set_issued_at_now"): (
        "{self}.set_issued_at(&std::time::SystemTime::now())",
        True,  # returns_self for chaining
        False,  # needs_result
        None,  # returns_type
        None,  # param_types
    ),
    ("josekit", "JwtPayload", "set_expires_at_hours"): (
        "{self}.set_expires_at(&(std::time::SystemTime::now() + std::time::Duration::from_secs({arg0} * 3600)))",
        True,  # returns_self for chaining
        False,  # needs_result
        None,  # returns_type
        ["u64"],  # param_types - hours as integer
    ),
    # josekit .claim() methods return Option<&Value>, need .cloned() to get owned value
    ("josekit", "JwtPayload", "claim"): (
        "{self}.claim({arg0}).cloned()",
        False,  # returns_self
        False,  # needs_result
        "Option<Value>",  # returns_type
        ["&str"],  # param_types
    ),
    ("josekit", "JwsHeader", "claim"): (
        "{self}.claim({arg0}).cloned()",
        False,  # returns_self
        False,  # needs_result
        "Option<Value>",  # returns_type
        ["&str"],  # param_types
    ),
    ("josekit", "JweHeader", "claim"): (
        "{self}.claim({arg0}).cloned()",
        False,  # returns_self
        False,  # needs_result
        "Option<Value>",  # returns_type
        ["&str"],  # param_types
    ),
    ("josekit", "JwsHeaderSet", "claim"): (
        "{self}.claim({arg0}).cloned()",
        False,  # returns_self
        False,  # needs_result
        "Option<Value>",  # returns_type
        ["&str"],  # param_types
    ),
    ("josekit", "JweHeaderSet", "claim"): (
        "{self}.claim({arg0}).cloned()",
        False,  # returns_self
        False,  # needs_result
        "Option<Value>",  # returns_type
        ["&str"],  # param_types
    ),
    ("josekit", "JwtPayloadValidator", "claim"): (
        "{self}.claim({arg0}).cloned()",
        False,  # returns_self
        False,  # needs_result
        "Option<Value>",  # returns_type
        ["&str"],  # param_types
    ),
    # sha2 Sha256 instance methods
    ("sha2", "Sha256", "update"): (
        "{self}.update({arg0})",
        True,  # returns_self for chaining
        False,  # needs_result
        None,  # returns_type
        ["&[u8]"],  # param_types
    ),
    ("sha2", "Sha256", "finalize"): (
        "{self}.finalize()",
        False,  # returns_self
        False,  # needs_result
        "GenericArray<u8, U32>",  # returns_type (digest output)
        None,  # param_types
    ),
    ("sha2", "Sha256", "finalize_hex"): (
        "hex::encode({self}.finalize())",
        False,  # returns_self
        False,  # needs_result
        "String",  # returns_type
        None,  # param_types
    ),
    ("sha2", "Sha512", "update"): (
        "{self}.update({arg0})",
        True,  # returns_self for chaining
        False,  # needs_result
        None,  # returns_type
        ["&[u8]"],  # param_types
    ),
    ("sha2", "Sha512", "finalize"): (
        "{self}.finalize()",
        False,  # returns_self
        False,  # needs_result
        "GenericArray<u8, U64>",  # returns_type
        None,  # param_types
    ),
    # serde_json Value methods that return references - need .cloned() for owned values
    ("serde_json", "Value", "as_object"): (
        "{self}.as_object().cloned()",
        False,  # returns_self
        False,  # needs_result
        "Option<Map<String, Value>>",  # returns_type
        None,  # param_types
    ),
    ("serde_json", "Value", "as_array"): (
        "{self}.as_array().cloned()",
        False,  # returns_self
        False,  # needs_result
        "Option<Vec<Value>>",  # returns_type
        None,  # param_types
    ),
    ("serde_json", "Value", "as_str"): (
        "{self}.as_str().map(|s| s.to_string())",
        False,  # returns_self
        False,  # needs_result
        "Option<String>",  # returns_type
        None,  # param_types
    ),
    # serde_json Map.get returns Option<&Value>, override with .cloned()
    ("serde_json", "Map", "get"): (
        "{self}.get({arg0}).cloned()",
        False,  # returns_self
        False,  # needs_result
        "Option<Value>",  # returns_type
        ["&str"],  # param_types
    ),
}


# Hardcoded macro stubs for crates that export macros (macros can't be auto-detected by parsing)
# Format: crate_name -> list of (python_stub, toml_mapping)
# python_stub: Python function stub code
# toml_mapping: dict with keys (python, rust_code, rust_imports, needs_result, param_types)
CRATE_MACRO_STUBS: dict[str, list[tuple[str, dict]]] = {
    "serde_json": [
        (
            '''
def json(value: Any) -> "Value":
    """Convert a Python value to a serde_json::Value.

    Uses the serde_json::json! macro.
    """
    ...
''',
            {
                "python": "serde_json.json",
                "rust_code": "serde_json::json!({arg0})",
                "rust_imports": [],
                "needs_result": False,
                "param_types": ["impl Serialize"],
            },
        ),
    ],
    "log": [
        (
            '''
def trace(message: str) -> None:
    """Logs a message at the trace level."""
    ...
''',
            {
                "python": "log.trace",
                "rust_code": 'log::trace!("{}", {arg0})',
                "rust_imports": [],
                "needs_result": False,
                "param_types": ["&str"],
            },
        ),
        (
            '''
def debug(message: str) -> None:
    """Logs a message at the debug level."""
    ...
''',
            {
                "python": "log.debug",
                "rust_code": 'log::debug!("{}", {arg0})',
                "rust_imports": [],
                "needs_result": False,
                "param_types": ["&str"],
            },
        ),
        (
            '''
def info(message: str) -> None:
    """Logs a message at the info level."""
    ...
''',
            {
                "python": "log.info",
                "rust_code": 'log::info!("{}", {arg0})',
                "rust_imports": [],
                "needs_result": False,
                "param_types": ["&str"],
            },
        ),
        (
            '''
def warn(message: str) -> None:
    """Logs a message at the warn level."""
    ...
''',
            {
                "python": "log.warn",
                "rust_code": 'log::warn!("{}", {arg0})',
                "rust_imports": [],
                "needs_result": False,
                "param_types": ["&str"],
            },
        ),
        (
            '''
def error(message: str) -> None:
    """Logs a message at the error level."""
    ...
''',
            {
                "python": "log.error",
                "rust_code": 'log::error!("{}", {arg0})',
                "rust_imports": [],
                "needs_result": False,
                "param_types": ["&str"],
            },
        ),
        (
            '''
def eprintln(message: str) -> None:
    """Print to stderr."""
    ...
''',
            {
                "python": "log.eprintln",
                "rust_code": 'eprintln!("{}", {arg0})',
                "rust_imports": [],
                "needs_result": False,
                "param_types": ["&str"],
            },
        ),
    ],
}

# Hardcoded type stubs for types that aren't properly detected (e.g., type aliases, internal types)
# Format: crate_name -> list of (python_stub, type_mapping, function_mappings)
# function_mappings is list of dicts with keys (python, rust_code, rust_imports, needs_result, param_types)
CRATE_TYPE_STUBS: dict[str, list[tuple[str, str, list[dict]]]] = {
    "sha2": [
        (
            '''
class Sha256:
    """SHA-256 hasher.

    Maps to sha2::Sha256 in Rust (type alias for CoreWrapper<Sha256VarCore>).
    """

    @staticmethod
    def digest(data: bytes) -> bytes:
        """Compute SHA-256 hash of data in one shot.

        Args:
            data: Bytes to hash

        Returns:
            32-byte hash digest
        """
        ...

    @staticmethod
    def new() -> "Sha256":
        """Create a new SHA-256 hasher."""
        ...

    def update(self, data: bytes) -> None:
        """Update the hasher with data."""
        ...

    def finalize(self) -> bytes:
        """Finalize and return the hash."""
        ...
''',
            "sha2::Sha256",
            [
                {
                    "python": "sha2.Sha256.digest",
                    "rust_code": "sha2::Sha256::digest({arg0})",
                    "rust_imports": ["sha2::Sha256", "sha2::Digest"],
                    "needs_result": False,
                    "param_types": ["&[u8]"],
                },
                {
                    "python": "sha2.Sha256.new",
                    "rust_code": "sha2::Sha256::new()",
                    "rust_imports": ["sha2::Sha256", "sha2::Digest"],
                    "needs_result": False,
                    "param_types": [],
                },
            ],
        ),
        (
            '''
class Sha512:
    """SHA-512 hasher.

    Maps to sha2::Sha512 in Rust.
    """

    @staticmethod
    def digest(data: bytes) -> bytes:
        """Compute SHA-512 hash of data in one shot."""
        ...

    @staticmethod
    def new() -> "Sha512":
        """Create a new SHA-512 hasher."""
        ...
''',
            "sha2::Sha512",
            [
                {
                    "python": "sha2.Sha512.digest",
                    "rust_code": "sha2::Sha512::digest({arg0})",
                    "rust_imports": ["sha2::Sha512", "sha2::Digest"],
                    "needs_result": False,
                    "param_types": ["&[u8]"],
                },
                {
                    "python": "sha2.Sha512.new",
                    "rust_code": "sha2::Sha512::new()",
                    "rust_imports": ["sha2::Sha512", "sha2::Digest"],
                    "needs_result": False,
                    "param_types": [],
                },
            ],
        ),
    ],
}

# Hardcoded constant stubs for module-level constants (e.g., base64 engines)
# Format: crate_name -> list of (const_name, python_type, rust_path, method_mappings)
# method_mappings is list of dicts with keys (method_name, rust_code_template, needs_result, param_types, returns)
# rust_code_template uses {self} for the constant and {argN} for arguments
CRATE_CONSTANT_STUBS: dict[str, list[tuple[str, str, str, list[dict]]]] = {
    "base64": [
        # URL_SAFE_NO_PAD engine constant
        (
            "URL_SAFE_NO_PAD",
            "GeneralPurpose",
            "base64::engine::general_purpose::URL_SAFE_NO_PAD",
            [
                {
                    "method_name": "decode",
                    "rust_code_template": "base64::engine::general_purpose::URL_SAFE_NO_PAD.decode({arg0})",
                    "rust_imports": ["base64::Engine"],
                    "needs_result": True,
                    "param_types": ["&[u8]"],
                    "returns": "Vec<u8>",
                },
                {
                    "method_name": "encode",
                    "rust_code_template": "base64::engine::general_purpose::URL_SAFE_NO_PAD.encode({arg0})",
                    "rust_imports": ["base64::Engine"],
                    "needs_result": False,
                    "param_types": ["&[u8]"],
                    "returns": "String",
                },
            ],
        ),
        # STANDARD engine constant
        (
            "STANDARD",
            "GeneralPurpose",
            "base64::engine::general_purpose::STANDARD",
            [
                {
                    "method_name": "decode",
                    "rust_code_template": "base64::engine::general_purpose::STANDARD.decode({arg0})",
                    "rust_imports": ["base64::Engine"],
                    "needs_result": True,
                    "param_types": ["&[u8]"],
                    "returns": "Vec<u8>",
                },
                {
                    "method_name": "encode",
                    "rust_code_template": "base64::engine::general_purpose::STANDARD.encode({arg0})",
                    "rust_imports": ["base64::Engine"],
                    "needs_result": False,
                    "param_types": ["&[u8]"],
                    "returns": "String",
                },
            ],
        ),
        # STANDARD_NO_PAD engine constant
        (
            "STANDARD_NO_PAD",
            "GeneralPurpose",
            "base64::engine::general_purpose::STANDARD_NO_PAD",
            [
                {
                    "method_name": "decode",
                    "rust_code_template": "base64::engine::general_purpose::STANDARD_NO_PAD.decode({arg0})",
                    "rust_imports": ["base64::Engine"],
                    "needs_result": True,
                    "param_types": ["&[u8]"],
                    "returns": "Vec<u8>",
                },
                {
                    "method_name": "encode",
                    "rust_code_template": "base64::engine::general_purpose::STANDARD_NO_PAD.encode({arg0})",
                    "rust_imports": ["base64::Engine"],
                    "needs_result": False,
                    "param_types": ["&[u8]"],
                    "returns": "String",
                },
            ],
        ),
        # URL_SAFE engine constant
        (
            "URL_SAFE",
            "GeneralPurpose",
            "base64::engine::general_purpose::URL_SAFE",
            [
                {
                    "method_name": "decode",
                    "rust_code_template": "base64::engine::general_purpose::URL_SAFE.decode({arg0})",
                    "rust_imports": ["base64::Engine"],
                    "needs_result": True,
                    "param_types": ["&[u8]"],
                    "returns": "Vec<u8>",
                },
                {
                    "method_name": "encode",
                    "rust_code_template": "base64::engine::general_purpose::URL_SAFE.encode({arg0})",
                    "rust_imports": ["base64::Engine"],
                    "needs_result": False,
                    "param_types": ["&[u8]"],
                    "returns": "String",
                },
            ],
        ),
    ],
    "josekit": [
        # Dir - Direct encryption algorithm for JWE
        (
            "Dir",
            "DirectJweAlgorithm",
            "josekit::jwe::Dir",
            [
                {
                    "method_name": "encrypter_from_bytes",
                    "rust_code_template": "josekit::jwe::Dir.encrypter_from_bytes({arg0})",
                    "rust_imports": ["josekit::jwe::Dir"],
                    "needs_result": True,
                    "param_types": ["&[u8]"],
                    "returns": "DirectJweEncrypter",
                },
                {
                    "method_name": "encrypter_from_jwk",
                    "rust_code_template": "josekit::jwe::Dir.encrypter_from_jwk(&{arg0})",
                    "rust_imports": ["josekit::jwe::Dir"],
                    "needs_result": True,
                    "param_types": ["&Jwk"],
                    "returns": "DirectJweEncrypter",
                },
                {
                    "method_name": "decrypter_from_bytes",
                    "rust_code_template": "josekit::jwe::Dir.decrypter_from_bytes({arg0})",
                    "rust_imports": ["josekit::jwe::Dir"],
                    "needs_result": True,
                    "param_types": ["&[u8]"],
                    "returns": "DirectJweDecrypter",
                },
                {
                    "method_name": "decrypter_from_jwk",
                    "rust_code_template": "josekit::jwe::Dir.decrypter_from_jwk(&{arg0})",
                    "rust_imports": ["josekit::jwe::Dir"],
                    "needs_result": True,
                    "param_types": ["&Jwk"],
                    "returns": "DirectJweDecrypter",
                },
            ],
        ),
    ],
}


# Hardcoded param_types overrides for functions that need explicit reference types
# This fixes cases where generic types like "T" would cause ownership transfer
# when the API actually expects borrowing (impl AsRef<T>)
# Format: crate_name -> {function_python_name -> list of param_types}
CRATE_FUNCTION_PARAM_OVERRIDES: dict[str, dict[str, list[str]]] = {
    "base64": {
        # base64::encode and decode take impl AsRef<[u8]>, so they borrow
        "base64.encode": ["&[u8]"],
        "base64.decode": ["&[u8]"],
        "base64.encode_engine": ["&[u8]", "&E"],
        "base64.decode_engine": ["&[u8]", "&E"],
        "base64.decode_engine_vec": ["&[u8]", "&mut Vec<u8>", "&E"],
        "base64.decode_engine_slice": ["&[u8]", "&mut [u8]", "&E"],
    },
}

# Hardcoded type path overrides for types that are re-exported from internal modules
# Maps (crate_name, type_name) -> public_rust_path
# Use this when cookcrab generates internal module paths (e.g. redis::cmd::Cmd)
# but the public API uses a re-export (e.g. redis::Cmd)
CRATE_TYPE_PATH_OVERRIDES: dict[tuple[str, str], str] = {
    # redis types - re-exported from internal modules
    ("redis", "Client"): "redis::Client",
    ("redis", "Cmd"): "redis::Cmd",
    ("redis", "Connection"): "redis::Connection",
    ("redis", "ConnectionManager"): "redis::aio::ConnectionManager",
    ("redis", "Pipeline"): "redis::Pipeline",
    ("redis", "RedisError"): "redis::RedisError",
    ("redis", "RedisResult"): "redis::RedisResult",
    ("redis", "Value"): "redis::Value",
    ("redis", "InfoDict"): "redis::InfoDict",
}

# Static constructor function mappings - convenience functions disguised as static methods
# These generate TOML function mappings only (no Python stubs - those come from the class definition)
# Format: (crate_name, python_path) -> (rust_code, rust_imports, needs_result, param_types)
STATIC_CONSTRUCTOR_MAPPINGS: dict[tuple[str, str], tuple[str, list[str], bool, list[str] | None]] = {
    # redis Cmd convenience constructors - Cmd.get(key) -> redis::cmd("GET").arg(key)
    ("redis", "redis.Cmd.get"): (
        'redis::cmd("GET").arg({arg0})',
        [],
        False,
        ["&str"],
    ),
    ("redis", "redis.Cmd.set"): (
        'redis::cmd("SET").arg({arg0}).arg({arg1})',
        [],
        False,
        ["&str", "&str"],
    ),
    ("redis", "redis.Cmd.hget"): (
        'redis::cmd("HGET").arg({arg0}).arg({arg1})',
        [],
        False,
        ["&str", "&str"],
    ),
    ("redis", "redis.Cmd.hset"): (
        'redis::cmd("HSET").arg({arg0}).arg({arg1}).arg({arg2})',
        [],
        False,
        ["&str", "&str", "&str"],
    ),
    ("redis", "redis.Cmd.hgetall"): (
        'redis::cmd("HGETALL").arg({arg0})',
        [],
        False,
        ["&str"],
    ),
    ("redis", "redis.Cmd.smembers"): (
        'redis::cmd("SMEMBERS").arg({arg0})',
        [],
        False,
        ["&str"],
    ),
    ("redis", "redis.Cmd.sismember"): (
        'redis::cmd("SISMEMBER").arg({arg0}).arg({arg1})',
        [],
        False,
        ["&str", "&str"],
    ),
    ("redis", "redis.Cmd.sadd"): (
        'redis::cmd("SADD").arg({arg0}).arg({arg1})',
        [],
        False,
        ["&str", "&str"],
    ),
    ("redis", "redis.Cmd.del_"): (
        'redis::cmd("DEL").arg({arg0})',
        [],
        False,
        ["&str"],
    ),
    ("redis", "redis.Cmd.exists"): (
        'redis::cmd("EXISTS").arg({arg0})',
        [],
        False,
        ["&str"],
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


def get_smart_param_type(param: RustParam) -> str:
    """Get appropriate Rust param_type using structured type info.

    This uses the new RustTypeInfo to make smarter decisions about borrowing:
    - If type_info.expects_borrow is True (impl AsRef<T>), suggest &T form
    - If type_info.is_reference is True, keep the reference
    - Otherwise fall back to the raw rust_type

    This reduces the need for hardcoded CRATE_FUNCTION_PARAM_OVERRIDES.
    """
    type_info = param.type_info
    if type_info is None:
        # No structured info available, fall back to raw type
        return param.rust_type

    # If the type is already a reference, use it as-is
    if type_info.is_reference:
        return param.rust_type

    # If the type is impl AsRef<X>, suggest &X (borrow form)
    if type_info.is_impl_trait and type_info.expects_borrow:
        trait_bound = type_info.trait_bound or ""
        # Extract inner type from AsRef<X>, Borrow<X>, etc.
        # e.g., "AsRef<[u8]>" -> "&[u8]"
        # e.g., "AsRef<str>" -> "&str"
        import re

        match = re.search(r"AsRef<([^>]+)>|Borrow<([^>]+)>", trait_bound)
        if match:
            inner_type = match.group(1) or match.group(2)
            if inner_type:
                return f"&{inner_type}"

    # For Into<T> or TryInto<T>, the type takes ownership - use T or the raw type
    if type_info.is_impl_trait and type_info.expects_owned:
        # Don't add & for Into bounds
        return param.rust_type

    # Default: use raw rust_type
    return param.rust_type


def get_param_types_for_function(params: list[RustParam], crate_name: str, func_name: str) -> list[str]:
    """Get param_types for a function, using type_info when available.

    Checks for hardcoded overrides first, then falls back to smart detection.
    """
    # First check for explicit overrides (for backwards compat / special cases)
    full_func_name = f"{crate_name}.{func_name}"
    if crate_name in CRATE_FUNCTION_PARAM_OVERRIDES:
        override_map = CRATE_FUNCTION_PARAM_OVERRIDES[crate_name]
        if full_func_name in override_map:
            log_decision(
                "param_types_override",
                crate=crate_name,
                function=func_name,
                param_types=override_map[full_func_name],
            )
            return override_map[full_func_name]

    # Use smart type detection based on type_info
    return [get_smart_param_type(p) for p in params]


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

    # Make parameter names unique (handles duplicate `_` in Rust)
    unique_names = make_unique_param_names(method.params)
    for param, unique_name in zip(method.params, unique_names):
        py_type = rust_type_to_python(param.rust_type)
        params.append(f"{unique_name}: {py_type}")

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

    # Make parameter names unique (handles duplicate `_` in Rust)
    unique_names = make_unique_param_names(method.params)
    for param, unique_name in zip(method.params, unique_names):
        py_type = rust_type_to_python(param.rust_type)
        params.append(f"{unique_name}: {py_type}")

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

    # Make parameter names unique (handles duplicate `_` in Rust)
    unique_names = make_unique_param_names(func.params)
    for param, unique_name in zip(func.params, unique_names):
        py_type = rust_type_to_python(param.rust_type)
        params.append(f"{unique_name}: {py_type}")

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
    rust_crate_ident = crate_name_to_rust_ident(crate_name)
    lines = [
        "",
        "T = TypeVar('T')",
        "E = TypeVar('E')",
        "",
        "",
        f"class {alias.name}(Generic[T, E]):",
        f'    """A Result type alias for {crate_name}.',
        "",
        f"    Maps to {rust_crate_ident}::{alias.name} which is an alias for {alias.target_type}.",
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

    # Add macro stubs (e.g., log macros)
    macro_functions_added = []
    if crate_name in CRATE_MACRO_STUBS:
        for python_stub, _toml_mapping in CRATE_MACRO_STUBS[crate_name]:
            lines.append(python_stub)
            # Extract function name from stub (first line after def)
            for line in python_stub.strip().split("\n"):
                if line.startswith("def "):
                    func_name = line.split("(")[0].replace("def ", "")
                    macro_functions_added.append(func_name)
                    break

    # Add hardcoded type stubs (e.g., sha2::Sha256)
    hardcoded_types_added = []
    if crate_name in CRATE_TYPE_STUBS:
        for python_stub, _rust_type, _func_mappings in CRATE_TYPE_STUBS[crate_name]:
            lines.append(python_stub)
            # Extract type name from stub (first class line)
            for line in python_stub.strip().split("\n"):
                if line.startswith("class "):
                    type_name = line.split("(")[0].split(":")[0].replace("class ", "")
                    hardcoded_types_added.append(type_name)
                    break

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
            lines.append(f'    """{escape_docstring(struct.doc)}"""')
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
            lines.append(f'    """{escape_docstring(enum.doc)}"""')
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
                lines.append(f'"""{escape_docstring(func.doc)}"""')
            sig = generate_function_signature(func)
            lines.append(sig)

    # Generate enum variant alias constants (e.g., HS256: HmacJwsAlgorithm)
    all_constants = []
    if crate.enum_variant_aliases:
        lines.append("")
        lines.append("# ====================================================")
        lines.append("# Algorithm/Variant Constants - convenient top-level exports")
        lines.append("# ====================================================")
        lines.append("")
        for alias in crate.enum_variant_aliases:
            safe_name = python_safe_name(alias.alias_name)
            all_constants.append(safe_name)
            lines.append(f"{safe_name}: {alias.enum_type}")

    # Generate hardcoded constant stubs (e.g., base64 engine constants)
    if crate_name in CRATE_CONSTANT_STUBS:
        lines.append("")
        lines.append("# ====================================================")
        lines.append("# Module-level Constants")
        lines.append("# ====================================================")
        lines.append("")
        for const_name, python_type, _rust_path, _methods in CRATE_CONSTANT_STUBS[crate_name]:
            all_constants.append(const_name)
            lines.append(f"{const_name}: {python_type} = ...")

    # Add Result type aliases to all_types
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            all_types.insert(0, alias.name)  # Put Result first

    # Add __all__ - order: functions, manual stubs, std types, crate types, constants
    lines.append("")
    all_items = all_functions + manual_functions_added + std_types_added + all_types + all_constants
    all_str = ", ".join(f'"{t}"' for t in all_items)
    lines.append(f"__all__: list[str] = [{all_str}]")
    lines.append("")

    return "\n".join(lines)


def crate_name_to_rust_ident(crate_name: str) -> str:
    """Convert a crate name to a valid Rust identifier.

    Cargo allows hyphens in crate names, but Rust code uses underscores.
    For example, 'native-tls' becomes 'native_tls' in Rust code.
    """
    return crate_name.replace("-", "_")


def generate_spicycrab_toml(crate: RustCrate, crate_name: str, version: str, python_module: str) -> str:
    """Generate _spicycrab.toml content."""
    # Convert crate name for use in Rust code paths
    rust_crate_ident = crate_name_to_rust_ident(crate_name)

    lines = [
        "[package]",
        f'name = "{crate_name}"',
        f'rust_crate = "{rust_crate_ident}"',
        f'rust_version = "{version}"',
        f'python_module = "{python_module}"',
        "",
        "[cargo.dependencies]",
        f'{crate_name} = "{version}"',
        "",
    ]

    # Add features section if available
    if crate.available_features:
        lines.append("[cargo.features]")
        # Format available features as TOML array
        features_str = ", ".join(f'"{f}"' for f in crate.available_features)
        lines.append(f"available = [{features_str}]")
        # Format default features as TOML array
        if crate.default_features:
            defaults_str = ", ".join(f'"{f}"' for f in crate.default_features)
            lines.append(f"default = [{defaults_str}]")
        else:
            lines.append("default = []")
        lines.append("")

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

    # Generate mappings for macro stubs (e.g., log macros)
    # Note: Macros are detected via #[macro_export], but signatures can't be auto-extracted
    detected_macro_names = {m.name for m in crate.macros if m.is_exported}
    hardcoded_macro_names: set[str] = set()

    if crate_name in CRATE_MACRO_STUBS:
        lines.append("# Macro mappings (signatures from hardcoded stubs)")
        for _python_stub, toml_mapping in CRATE_MACRO_STUBS[crate_name]:
            # Extract macro name from python path (e.g., "log.trace" -> "trace")
            macro_name = toml_mapping["python"].split(".")[-1]
            hardcoded_macro_names.add(macro_name)

            lines.append("[[mappings.functions]]")
            lines.append(f'python = "{toml_mapping["python"]}"')
            # Escape double quotes for TOML
            rust_code = toml_mapping["rust_code"].replace('"', '\\"')
            lines.append(f'rust_code = "{rust_code}"')
            if toml_mapping.get("rust_imports"):
                imports_str = ", ".join(f'"{i}"' for i in toml_mapping["rust_imports"])
                lines.append(f"rust_imports = [{imports_str}]")
            else:
                lines.append("rust_imports = []")
            needs_result = "true" if toml_mapping.get("needs_result") else "false"
            lines.append(f"needs_result = {needs_result}")
            if toml_mapping.get("param_types"):
                param_types_str = ", ".join(f'"{t}"' for t in toml_mapping["param_types"])
                lines.append(f"param_types = [{param_types_str}]")
            lines.append("")

    # Log discovered macros that don't have hardcoded stubs
    uncovered_macros = detected_macro_names - hardcoded_macro_names
    if uncovered_macros:
        log_decision(
            "uncovered_macros",
            crate=crate_name,
            detected=list(uncovered_macros),
            message="These exported macros were detected but have no hardcoded stubs",
        )
        macro_list = ", ".join(sorted(uncovered_macros))
        lines.append(f"# NOTE: Detected {len(uncovered_macros)} macros without stubs: {macro_list}")
        lines.append("# To use these macros, add signatures to CRATE_MACRO_STUBS in generator.py")
        lines.append("")

    # Generate mappings for hardcoded type stubs (e.g., sha2::Sha256)
    if crate_name in CRATE_TYPE_STUBS:
        for _python_stub, rust_type, func_mappings in CRATE_TYPE_STUBS[crate_name]:
            # Add function mappings for the type's static methods
            for mapping in func_mappings:
                lines.append("# Hardcoded type function")
                lines.append("[[mappings.functions]]")
                lines.append(f'python = "{mapping["python"]}"')
                lines.append(f'rust_code = "{mapping["rust_code"]}"')
                if mapping.get("rust_imports"):
                    imports_str = ", ".join(f'"{i}"' for i in mapping["rust_imports"])
                    lines.append(f"rust_imports = [{imports_str}]")
                else:
                    lines.append("rust_imports = []")
                needs_result = "true" if mapping.get("needs_result") else "false"
                lines.append(f"needs_result = {needs_result}")
                if mapping.get("param_types"):
                    param_types_str = ", ".join(f'"{t}"' for t in mapping["param_types"])
                    lines.append(f"param_types = [{param_types_str}]")
                lines.append("")

    # Generate mappings for free-standing functions
    for func in crate.functions:
        if func.is_pub:
            # Generate argument placeholders
            args = ", ".join(f"{{arg{i}}}" for i in range(len(func.params)))
            py_func_name = python_safe_name(func.name)

            # Get param_types using smart detection (checks overrides + type_info)
            param_types = get_param_types_for_function(func.params, crate_name, py_func_name)
            param_types_str = ", ".join(f'"{t}"' for t in param_types)

            # Check for path overrides (e.g., tokio::sleep -> tokio::time::sleep)
            override_key = (crate_name, func.name)
            if override_key in FUNCTION_PATH_OVERRIDES:
                rust_code_template, rust_imports = FUNCTION_PATH_OVERRIDES[override_key]
                rust_code = rust_code_template
                log_decision(
                    "function_path_override",
                    crate=crate_name,
                    function=func.name,
                    rust_code=rust_code,
                )
                increment("function_path_overrides")
            else:
                # Use module_path if available, applying the public path heuristic
                public_path = get_public_module_path(func.module_path, func.name)
                if public_path:
                    func_path = f"{rust_crate_ident}::{public_path}::{func.name}"
                else:
                    func_path = f"{rust_crate_ident}::{func.name}"
                rust_code = f"{func_path}({args})"
                rust_imports = [func_path]

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
        # Check for explicit type path override first
        override_key = (crate_name, struct.name)
        if override_key in CRATE_TYPE_PATH_OVERRIDES:
            struct_path = CRATE_TYPE_PATH_OVERRIDES[override_key]
        else:
            # Get the full Rust path for the struct, applying the public path heuristic
            public_path = get_public_module_path(struct.module_path, struct.name)
            if public_path:
                struct_path = f"{rust_crate_ident}::{public_path}::{struct.name}"
            else:
                struct_path = f"{rust_crate_ident}::{struct.name}"

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
                    lines.append(f'rust_code = "{rust_crate_ident}::anyhow!({args})"')
                    lines.append("rust_imports = []")
                    lines.append(f"needs_result = {needs_result_val}")
                    if param_types:
                        lines.append(f"param_types = [{param_types_str}]")
                    lines.append("")
                else:
                    lines.append("[[mappings.functions]]")
                    lines.append(f'python = "{crate_name}.{struct.name}.{py_method_name}"')
                    lines.append(f'rust_code = "{struct_path}::{method.name}({args})"')
                    lines.append(f'rust_imports = ["{struct_path}"]')
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

                # Check if method returns a Result type
                needs_result_val = "true" if returns_result(method.return_type) else "false"

                # Extract return type for method chaining
                returns_type = extract_return_type_name(method.return_type, struct.name)

                lines.append("[[mappings.methods]]")
                lines.append(f'python = "{struct.name}.{py_method_name}"')
                if args:
                    lines.append(f'rust_code = "{{self}}.{method.name}({args})"')
                else:
                    lines.append(f'rust_code = "{{self}}.{method.name}()"')
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

    # Generate mappings for hardcoded method stubs
    for (stub_crate, type_name, method_name), method_info in STD_METHOD_STUBS.items():
        rust_code, returns_self, needs_result, returns_type, param_types = method_info
        if stub_crate == crate_name:
            lines.append(f"# {type_name}.{method_name} hardcoded method")
            lines.append("[[mappings.methods]]")
            lines.append(f'python = "{type_name}.{method_name}"')
            lines.append(f'rust_code = "{rust_code}"')
            lines.append("rust_imports = []")
            lines.append(f"needs_result = {'true' if needs_result else 'false'}")
            if returns_self:
                lines.append("returns_self = true")
            if returns_type:
                lines.append(f'returns = "{returns_type}"')
            if param_types:
                param_types_str = ", ".join(f'"{t}"' for t in param_types)
                lines.append(f"param_types = [{param_types_str}]")
            lines.append("")

    # Generate mappings for static constructor functions (convenience methods)
    for (stub_crate, python_path), mapping_info in STATIC_CONSTRUCTOR_MAPPINGS.items():
        rust_code, rust_imports, needs_result, param_types = mapping_info
        if stub_crate == crate_name:
            lines.append(f"# {python_path} static constructor")
            lines.append("[[mappings.functions]]")
            lines.append(f'python = "{python_path}"')
            # Use single quotes if rust_code contains double quotes
            if '"' in rust_code:
                lines.append(f"rust_code = '{rust_code}'")
            else:
                lines.append(f'rust_code = "{rust_code}"')
            if rust_imports:
                imports_str = ", ".join(f'"{i}"' for i in rust_imports)
                lines.append(f"rust_imports = [{imports_str}]")
            else:
                lines.append("rust_imports = []")
            lines.append(f"needs_result = {'true' if needs_result else 'false'}")
            if param_types:
                param_types_str = ", ".join(f'"{t}"' for t in param_types)
                lines.append(f"param_types = [{param_types_str}]")
            lines.append("")

    # Generate mappings for hardcoded constant stubs (e.g., base64 engine constants)
    if crate_name in CRATE_CONSTANT_STUBS:
        lines.append("# =====================================================")
        lines.append("# Module-level Constant Method Mappings")
        lines.append("# =====================================================")
        lines.append("")
        for const_name, _python_type, rust_path, method_mappings in CRATE_CONSTANT_STUBS[crate_name]:
            for method_info in method_mappings:
                method_name = method_info["method_name"]
                rust_code = method_info["rust_code_template"]
                rust_imports = method_info.get("rust_imports", [])
                needs_result = method_info.get("needs_result", False)
                param_types = method_info.get("param_types", [])
                returns = method_info.get("returns")

                lines.append(f"# {const_name}.{method_name} hardcoded method")
                lines.append("[[mappings.methods]]")
                lines.append(f'python = "{const_name}.{method_name}"')
                lines.append(f'rust_code = "{rust_code}"')
                if rust_imports:
                    imports_str = ", ".join(f'"{i}"' for i in rust_imports)
                    lines.append(f"rust_imports = [{imports_str}]")
                else:
                    lines.append("rust_imports = []")
                lines.append(f"needs_result = {'true' if needs_result else 'false'}")
                if returns:
                    lines.append(f'returns = "{returns}"')
                if param_types:
                    param_types_str = ", ".join(f'"{t}"' for t in param_types)
                    lines.append(f"param_types = [{param_types_str}]")
                lines.append("")

    # Generate mappings for enum variant aliases (e.g., HS256, RS256, etc.)
    # These are top-level constants that alias enum variants
    if crate.enum_variant_aliases:
        lines.append("# =====================================================")
        lines.append("# Enum Variant Alias Constants")
        lines.append("# =====================================================")
        lines.append("")
        for alias in crate.enum_variant_aliases:
            safe_name = python_safe_name(alias.alias_name)
            # Build the Rust path: crate::module::ALIAS
            if alias.module_path:
                rust_path = f"{rust_crate_ident}::{alias.module_path}::{alias.alias_name}"
            else:
                rust_path = f"{rust_crate_ident}::{alias.alias_name}"

            lines.append(f"# {safe_name} constant")
            lines.append("[[mappings.functions]]")
            lines.append(f'python = "{crate_name}.{safe_name}"')
            lines.append(f'rust_code = "{rust_path}"')
            lines.append(f'rust_imports = ["{rust_path}"]')
            lines.append("needs_result = false")
            lines.append("")

        # Generate method call mappings for enum variant aliases
        # First, build a map of enum types to their methods
        enum_methods: dict[str, list] = {}
        for impl in crate.impls:
            if impl.type_name not in enum_methods:
                enum_methods[impl.type_name] = []
            enum_methods[impl.type_name].extend(impl.methods)

        lines.append("# =====================================================")
        lines.append("# Enum Variant Alias Method Mappings")
        lines.append("# =====================================================")
        lines.append("")
        for alias in crate.enum_variant_aliases:
            safe_name = python_safe_name(alias.alias_name)
            # Get methods for the enum type
            methods = enum_methods.get(alias.enum_type, [])
            for method in methods:
                # Build Rust path for the constant
                if alias.module_path:
                    rust_const_path = f"{rust_crate_ident}::{alias.module_path}::{alias.alias_name}"
                else:
                    rust_const_path = f"{rust_crate_ident}::{alias.alias_name}"

                # Generate argument placeholders
                args = ", ".join(f"{{arg{i}}}" for i in range(len(method.params)))
                py_method_name = python_safe_name(method.name)

                # Collect param types
                param_types = [p.rust_type for p in method.params]
                param_types_str = ", ".join(f'"{t}"' for t in param_types)

                # Check if method returns a Result type
                needs_result_val = "true" if returns_result(method.return_type) else "false"

                lines.append("[[mappings.functions]]")
                lines.append(f'python = "{crate_name}.{safe_name}.{py_method_name}"')
                lines.append(f'rust_code = "{rust_const_path}.{method.name}({args})"')
                lines.append(f'rust_imports = ["{rust_const_path}"]')
                lines.append(f"needs_result = {needs_result_val}")
                if param_types:
                    lines.append(f"param_types = [{param_types_str}]")
                lines.append("")

    # Generate type mappings for Result type aliases
    for alias in crate.type_aliases:
        if is_result_type_alias(alias):
            lines.append("# Result type alias")
            lines.append("[[mappings.types]]")
            lines.append(f'python = "{alias.name}"')
            lines.append(f'rust = "{rust_crate_ident}::{alias.name}"')
            lines.append("")

    # Generate type mappings for standard library types
    for (stub_crate, type_name), (_class_code, rust_type, _func_mappings) in STD_TYPE_STUBS.items():
        if stub_crate == crate_name:
            lines.append(f"# {type_name} from std")
            lines.append("[[mappings.types]]")
            lines.append(f'python = "{type_name}"')
            lines.append(f'rust = "{rust_type}"')
            lines.append("")

    # Generate type mappings for hardcoded types (e.g., sha2::Sha256)
    if crate_name in CRATE_TYPE_STUBS:
        for _python_stub, rust_type, _func_mappings in CRATE_TYPE_STUBS[crate_name]:
            # Extract type name from rust_type (last component)
            type_name = rust_type.split("::")[-1]
            lines.append("[[mappings.types]]")
            lines.append(f'python = "{type_name}"')
            lines.append(f'rust = "{rust_type}"')
            lines.append("")

    # Generate type mappings for structs (skip those handled by STD_TYPE_STUBS)
    for struct in crate.structs:
        if struct.name in std_type_names:
            continue
        # Check for explicit type path override first
        override_key = (crate_name, struct.name)
        if override_key in CRATE_TYPE_PATH_OVERRIDES:
            rust_path = CRATE_TYPE_PATH_OVERRIDES[override_key]
        else:
            # Use module_path if available, applying the public path heuristic
            public_path = get_public_module_path(struct.module_path, struct.name)
            if public_path:
                rust_path = f"{rust_crate_ident}::{public_path}::{struct.name}"
            else:
                rust_path = f"{rust_crate_ident}::{struct.name}"
        lines.append("[[mappings.types]]")
        lines.append(f'python = "{struct.name}"')
        lines.append(f'rust = "{rust_path}"')
        lines.append("")

    for enum in crate.enums:
        if enum.name in std_type_names:
            continue
        # Check for explicit type path override first
        override_key = (crate_name, enum.name)
        if override_key in CRATE_TYPE_PATH_OVERRIDES:
            rust_path = CRATE_TYPE_PATH_OVERRIDES[override_key]
        else:
            # Use module_path if available, applying the public path heuristic
            public_path = get_public_module_path(enum.module_path, enum.name)
            if public_path:
                rust_path = f"{rust_crate_ident}::{public_path}::{enum.name}"
            else:
                rust_path = f"{rust_crate_ident}::{enum.name}"
        lines.append("[[mappings.types]]")
        lines.append(f'python = "{enum.name}"')
        lines.append(f'rust = "{rust_path}"')
        lines.append("")

    # Generate enum variant mappings for direct variant access (e.g., Protocol.Tlsv12)
    lines.append("# Enum variant access mappings")
    for enum in crate.enums:
        if enum.name in std_type_names:
            continue
        # Use module_path if available, applying the public path heuristic
        public_path = get_public_module_path(enum.module_path, enum.name)
        if public_path:
            rust_enum_path = f"{rust_crate_ident}::{public_path}::{enum.name}"
        else:
            rust_enum_path = f"{rust_crate_ident}::{enum.name}"
        for variant in enum.variants:
            safe_variant_name = python_safe_name(variant.name)
            lines.append("[[mappings.enum_variants]]")
            lines.append(f'python = "{enum.name}.{safe_variant_name}"')
            lines.append(f'rust = "{rust_enum_path}::{variant.name}"')
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
