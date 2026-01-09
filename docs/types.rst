Type System
===========

spicycrab maps Python type annotations to Rust types.

Primitive Types
---------------

int
^^^

.. code-block:: python

   x: int = 42
   count: int = -10

.. code-block:: rust

   let x: i64 = 42;
   let count: i64 = -10;

float
^^^^^

.. code-block:: python

   pi: float = 3.14159
   rate: float = 0.05

.. code-block:: rust

   let pi: f64 = 3.14159;
   let rate: f64 = 0.05;

str
^^^

.. code-block:: python

   name: str = "Alice"
   empty: str = ""

.. code-block:: rust

   let name: String = "Alice".to_string();
   let empty: String = String::new();

bool
^^^^

.. code-block:: python

   active: bool = True
   done: bool = False

.. code-block:: rust

   let active: bool = true;
   let done: bool = false;

None
^^^^

.. code-block:: python

   def do_nothing() -> None:
       pass

.. code-block:: rust

   pub fn do_nothing() {
   }

Rust Native Types
-----------------

For precise control over integer and float sizes, import Rust native types
from ``spicycrab.types``. These map directly to their Rust equivalents.

Integer Types
^^^^^^^^^^^^^

.. code-block:: python

   from spicycrab.types import u8, u16, u32, u64, i8, i16, i32, i64, usize, isize

   def add_bytes(a: u8, b: u8) -> u8:
       return a + b

   def index_size(arr: list[str]) -> usize:
       return len(arr)

   counter: i32 = 0

.. code-block:: rust

   pub fn add_bytes(a: u8, b: u8) -> u8 {
       a + b
   }

   pub fn index_size(arr: Vec<String>) -> usize {
       arr.len()
   }

   let counter: i32 = 0;

Available integer types:

+-------------------+---------------------+----------------------------------+
| Python            | Rust                | Range                            |
+===================+=====================+==================================+
| ``u8``            | ``u8``              | 0 to 255                         |
+-------------------+---------------------+----------------------------------+
| ``u16``           | ``u16``             | 0 to 65,535                      |
+-------------------+---------------------+----------------------------------+
| ``u32``           | ``u32``             | 0 to 4,294,967,295               |
+-------------------+---------------------+----------------------------------+
| ``u64``           | ``u64``             | 0 to 18,446,744,073,709,551,615  |
+-------------------+---------------------+----------------------------------+
| ``u128``          | ``u128``            | 0 to 2^128-1                     |
+-------------------+---------------------+----------------------------------+
| ``usize``         | ``usize``           | Platform-dependent (pointer size)|
+-------------------+---------------------+----------------------------------+
| ``i8``            | ``i8``              | -128 to 127                      |
+-------------------+---------------------+----------------------------------+
| ``i16``           | ``i16``             | -32,768 to 32,767                |
+-------------------+---------------------+----------------------------------+
| ``i32``           | ``i32``             | -2,147,483,648 to 2,147,483,647  |
+-------------------+---------------------+----------------------------------+
| ``i64``           | ``i64``             | -2^63 to 2^63-1                  |
+-------------------+---------------------+----------------------------------+
| ``i128``          | ``i128``            | -2^127 to 2^127-1                |
+-------------------+---------------------+----------------------------------+
| ``isize``         | ``isize``           | Platform-dependent (pointer size)|
+-------------------+---------------------+----------------------------------+

Float Types
^^^^^^^^^^^

.. code-block:: python

   from spicycrab.types import f32, f64

   def compute_single(x: f32, y: f32) -> f32:
       return x * y

   precise: f64 = 3.141592653589793

.. code-block:: rust

   pub fn compute_single(x: f32, y: f32) -> f32 {
       x * y
   }

   let precise: f64 = 3.141592653589793;

+-------------------+---------------------+----------------------------------+
| Python            | Rust                | Precision                        |
+===================+=====================+==================================+
| ``f32``           | ``f32``             | 32-bit IEEE 754                  |
+-------------------+---------------------+----------------------------------+
| ``f64``           | ``f64``             | 64-bit IEEE 754 (Python default) |
+-------------------+---------------------+----------------------------------+

.. note::

   Python's ``int`` maps to ``i64`` and ``float`` maps to ``f64`` by default.
   Use explicit Rust types when you need specific sizes for performance,
   memory constraints, or FFI compatibility.

Collection Types
----------------

List
^^^^

.. code-block:: python

   numbers: list[int] = [1, 2, 3]
   names: list[str] = ["Alice", "Bob"]

.. code-block:: rust

   let numbers: Vec<i64> = vec![1, 2, 3];
   let names: Vec<String> = vec!["Alice".to_string(), "Bob".to_string()];

Dict
^^^^

.. code-block:: python

   ages: dict[str, int] = {"Alice": 30, "Bob": 25}

.. code-block:: rust

   let ages: HashMap<String, i64> = HashMap::from([
       ("Alice".to_string(), 30),
       ("Bob".to_string(), 25),
   ]);

Set
^^^

.. code-block:: python

   unique: set[int] = {1, 2, 3}

.. code-block:: rust

   let unique: HashSet<i64> = HashSet::from([1, 2, 3]);

Tuple
^^^^^

.. code-block:: python

   point: tuple[int, int] = (10, 20)
   rgb: tuple[int, int, int] = (255, 128, 0)

.. code-block:: rust

   let point: (i64, i64) = (10, 20);
   let rgb: (i64, i64, i64) = (255, 128, 0);

Optional Types
--------------

Optional
^^^^^^^^

.. code-block:: python

   from typing import Optional

   name: Optional[str] = None
   value: Optional[int] = 42

.. code-block:: rust

   let name: Option<String> = None;
   let value: Option<i64> = Some(42);

Checking Optional
^^^^^^^^^^^^^^^^^

Both ``is None`` and ``is not None`` are supported:

.. code-block:: python

   def greet(name: Optional[str]) -> str:
       if name is None:
           return "Hello, stranger!"
       return f"Hello, {name}!"

   def process(value: str | None) -> None:
       if value is not None:
           print(f"Got: {value}")

.. code-block:: rust

   pub fn greet(name: Option<String>) -> String {
       if name.is_none() {
           return "Hello, stranger!".to_string();
       }
       format!("Hello, {}!", name.unwrap())
   }

   pub fn process(value: Option<String>) {
       if value.is_some() {
           println!("Got: {}", value.unwrap());
       }
   }

Union syntax ``T | None`` is equivalent to ``Optional[T]``:

.. code-block:: python

   # Both are equivalent
   name: Optional[str] = None
   name: str | None = None

Returning Optional
^^^^^^^^^^^^^^^^^^

Functions returning ``T | None`` or ``Optional[T]`` automatically wrap
non-None return values in ``Some()``:

.. code-block:: python

   def maybe_get(flag: bool) -> str | None:
       if flag:
           return "value"
       return None

.. code-block:: rust

   pub fn maybe_get(flag: bool) -> Option<String> {
       if flag {
           return Some("value".to_string());
       }
       None
   }

Result Types
------------

For error handling, use ``Result[T, E]``:

.. code-block:: python

   from spicycrab.types import Result, Ok, Err

   def parse_int(s: str) -> Result[int, str]:
       if s.isdigit():
           return Ok(int(s))
       return Err("not a number")

.. code-block:: rust

   pub fn parse_int(s: String) -> Result<i64, String> {
       if s.chars().all(|c| c.is_ascii_digit()) {
           return Ok(s.parse::<i64>().unwrap());
       }
       Err("not a number".to_string())
   }

See :doc:`error_handling` for more details.

Path Types
----------

.. code-block:: python

   from pathlib import Path

   p: Path = Path("/home/user")

.. code-block:: rust

   let p: PathBuf = PathBuf::from("/home/user");

Any Type (Dynamic Values)
-------------------------

Python's ``Any`` type maps to ``serde_json::Value``, allowing storage of
arbitrary JSON-compatible values. This is useful for working with dynamic
data structures like configuration files or API responses.

Basic usage
^^^^^^^^^^^

.. code-block:: python

   from typing import Any

   def process(data: dict[str, Any]) -> int:
       return len(data)

.. code-block:: rust

   pub fn process(data: HashMap<String, Value>) -> i64 {
       data.len() as i64
   }

Dictionary with Any values
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from typing import Any

   config: dict[str, Any] = {}

.. code-block:: rust

   let config: HashMap<String, Value> = HashMap::new();

.. note::

   When using ``Any``, the generated Rust code requires the ``serde_json``
   crate. This dependency is automatically added to ``Cargo.toml``.

.. warning::

   Literal values (strings, numbers, etc.) are not automatically converted
   to ``Value``. For complex dynamic data, consider using JSON parsing:

   .. code-block:: python

      import json
      data: dict[str, Any] = json.loads('{"key": "value"}')

Type Mapping Reference
----------------------

**Python Built-in Types:**

+-------------------+---------------------+
| Python            | Rust                |
+===================+=====================+
| ``int``           | ``i64``             |
+-------------------+---------------------+
| ``float``         | ``f64``             |
+-------------------+---------------------+
| ``str``           | ``String``          |
+-------------------+---------------------+
| ``bool``          | ``bool``            |
+-------------------+---------------------+
| ``None``          | ``()``              |
+-------------------+---------------------+
| ``list[T]``       | ``Vec<T>``          |
+-------------------+---------------------+
| ``dict[K, V]``    | ``HashMap<K, V>``   |
+-------------------+---------------------+
| ``set[T]``        | ``HashSet<T>``      |
+-------------------+---------------------+
| ``tuple[A, B]``   | ``(A, B)``          |
+-------------------+---------------------+
| ``Optional[T]``   | ``Option<T>``       |
+-------------------+---------------------+
| ``Result[T, E]``  | ``Result<T, E>``    |
+-------------------+---------------------+
| ``Path``          | ``PathBuf``         |
+-------------------+---------------------+
| ``Any``           | ``Value``           |
+-------------------+---------------------+

**Rust Native Types (from spicycrab.types):**

+-------------------+---------------------+
| Python            | Rust                |
+===================+=====================+
| ``u8``            | ``u8``              |
+-------------------+---------------------+
| ``u16``           | ``u16``             |
+-------------------+---------------------+
| ``u32``           | ``u32``             |
+-------------------+---------------------+
| ``u64``           | ``u64``             |
+-------------------+---------------------+
| ``u128``          | ``u128``            |
+-------------------+---------------------+
| ``usize``         | ``usize``           |
+-------------------+---------------------+
| ``i8``            | ``i8``              |
+-------------------+---------------------+
| ``i16``           | ``i16``             |
+-------------------+---------------------+
| ``i32``           | ``i32``             |
+-------------------+---------------------+
| ``i64``           | ``i64``             |
+-------------------+---------------------+
| ``i128``          | ``i128``            |
+-------------------+---------------------+
| ``isize``         | ``isize``           |
+-------------------+---------------------+
| ``f32``           | ``f32``             |
+-------------------+---------------------+
| ``f64``           | ``f64``             |
+-------------------+---------------------+
