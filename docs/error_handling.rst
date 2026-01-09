Error Handling
==============

spicycrab supports Rust-style error handling with ``Result[T, E]`` types.

Result Type
-----------

Basic Result
^^^^^^^^^^^^

.. code-block:: python

   from spicycrab.types import Result, Ok, Err

   def divide(a: int, b: int) -> Result[int, str]:
       if b == 0:
           return Err("division by zero")
       return Ok(a // b)

.. code-block:: rust

   pub fn divide(a: i64, b: i64) -> Result<i64, String> {
       if b == 0 {
           return Err("division by zero".to_string());
       }
       Ok(a / b)
   }

Ok and Err
^^^^^^^^^^

.. code-block:: python

   def parse_positive(s: str) -> Result[int, str]:
       if not s.isdigit():
           return Err("not a number")
       n: int = int(s)
       if n <= 0:
           return Err("must be positive")
       return Ok(n)

.. code-block:: rust

   pub fn parse_positive(s: String) -> Result<i64, String> {
       if !s.chars().all(|c| c.is_ascii_digit()) {
           return Err("not a number".to_string());
       }
       let n: i64 = s.parse::<i64>().unwrap();
       if n <= 0 {
           return Err("must be positive".to_string());
       }
       Ok(n)
   }

The ? Operator
--------------

When a function returns ``Result[T, E]``, calls to other Result-returning
functions automatically get the ``?`` operator for error propagation.

Automatic error propagation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def parse_number(s: str) -> Result[int, str]:
       if s.isdigit():
           return Ok(int(s))
       return Err("not a number")

   def double_parsed(s: str) -> Result[int, str]:
       value: int = parse_number(s)  # Automatically gets ?
       return Ok(value * 2)

.. code-block:: rust

   pub fn parse_number(s: String) -> Result<i64, String> {
       if s.chars().all(|c| c.is_ascii_digit()) {
           return Ok(s.parse::<i64>().unwrap());
       }
       Err("not a number".to_string())
   }

   pub fn double_parsed(s: String) -> Result<i64, String> {
       let value: i64 = parse_number(s)?;
       Ok(value * 2)
   }

Chaining fallible calls
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def step1(x: int) -> Result[int, str]:
       if x < 0:
           return Err("negative input")
       return Ok(x + 1)

   def step2(x: int) -> Result[int, str]:
       if x > 100:
           return Err("too large")
       return Ok(x * 2)

   def process(x: int) -> Result[int, str]:
       a: int = step1(x)   # Gets ?
       b: int = step2(a)   # Gets ?
       return Ok(b)

.. code-block:: rust

   pub fn process(x: i64) -> Result<i64, String> {
       let a: i64 = step1(x)?;
       let b: i64 = step2(a)?;
       Ok(b)
   }

Using ? with External Crate Stubs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When calling functions from external Rust crates via cookcrab-generated stubs,
the ``?`` operator is automatically added when **both** conditions are met:

1. Your Python function returns ``Result[T, E]``
2. The stub mapping has a ``returns`` field indicating it returns ``Result``

**How it works:**

1. **Stub Definition** (``_spicycrab.toml``): The ``returns`` field tells the
   transpiler that the function is fallible:

   .. code-block:: toml

      [[mappings.functions]]
      python = "reqwest.blocking.get"
      rust_code = "reqwest::blocking::get({arg0})"
      returns = "Result<Response, Error>"

2. **Stub Discovery**: When the emitter encounters a call to ``reqwest.blocking.get``,
   it looks up the mapping and finds ``returns = "Result<Response, Error>"``.

3. **Emitter Decision**: If the current function returns ``Result`` and the called
   function returns ``Result``, the ``?`` operator is added automatically.

**Example with reqwest:**

.. code-block:: python

   from spicycrab_reqwest.blocking import get, Response
   from spicycrab.types import Result, Ok, Err

   def fetch_url(url: str) -> Result[str, str]:
       # Because fetch_url returns Result AND reqwest.blocking.get returns Result,
       # the transpiler adds ? automatically
       response: Response = get(url)
       text: str = response.text()
       return Ok(text)

.. code-block:: rust

   use reqwest;

   pub fn fetch_url(url: String) -> Result<String, String> {
       let response: reqwest::blocking::Response = reqwest::blocking::get(url)?;
       let text: String = response.text()?;
       Ok(text)
   }

**Important**: If your function does NOT return ``Result``, the ``?`` operator
won't be added (Rust wouldn't allow it). In that case, you must explicitly
handle the error using ``Result.unwrap()`` or a try/except block:

.. code-block:: python

   from spicycrab_reqwest.blocking import get, Response
   from spicycrab.types import Result

   def fetch_url_unsafe(url: str) -> str:
       # No Result return type, so must explicitly unwrap
       response: Response = Result.unwrap(get(url))
       return Result.unwrap(response.text())

raise → return Err
------------------

Python's ``raise`` statement becomes ``return Err(...)``.

Basic raise
^^^^^^^^^^^

.. code-block:: python

   def validate(x: int) -> Result[int, str]:
       if x < 0:
           raise ValueError("must be positive")
       return Ok(x)

.. code-block:: rust

   pub fn validate(x: i64) -> Result<i64, String> {
       if x < 0 {
           return Err("must be positive".to_string());
       }
       Ok(x)
   }

Raise with formatted message
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def check_range(x: int, max_val: int) -> Result[int, str]:
       if x > max_val:
           raise ValueError(f"value {x} exceeds maximum {max_val}")
       return Ok(x)

.. code-block:: rust

   pub fn check_range(x: i64, max_val: i64) -> Result<i64, String> {
       if x > max_val {
           return Err(format!("value {} exceeds maximum {}", x, max_val));
       }
       Ok(x)
   }

try/except → match
------------------

When try/except wraps a Result-returning call, it becomes a ``match``.

Basic try/except
^^^^^^^^^^^^^^^^

.. code-block:: python

   def safe_divide(a: int, b: int) -> int:
       try:
           result: int = divide(a, b)
           return result
       except Exception as e:
           print(f"Error: {e}")
           return 0

.. code-block:: rust

   pub fn safe_divide(a: i64, b: i64) -> i64 {
       match divide(a, b) {
           Ok(result) => {
               return result;
           }
           Err(e) => {
               println!("Error: {}", e);
               return 0;
           }
       }
   }

Complete Example
----------------

.. code-block:: python

   from spicycrab.types import Result, Ok, Err

   def read_config(path: str) -> Result[str, str]:
       if path == "":
           return Err("empty path")
       return Ok("config data")

   def parse_config(data: str) -> Result[int, str]:
       if data == "":
           return Err("empty config")
       return Ok(42)

   def load_config(path: str) -> Result[int, str]:
       data: str = read_config(path)
       value: int = parse_config(data)
       return Ok(value)

   def main() -> None:
       try:
           config: int = load_config("settings.toml")
           print(config)
       except Exception as e:
           print(f"Failed: {e}")

.. code-block:: rust

   pub fn read_config(path: String) -> Result<String, String> {
       if path == "" {
           return Err("empty path".to_string());
       }
       Ok("config data".to_string())
   }

   pub fn parse_config(data: String) -> Result<i64, String> {
       if data == "" {
           return Err("empty config".to_string());
       }
       Ok(42)
   }

   pub fn load_config(path: String) -> Result<i64, String> {
       let data: String = read_config(path)?;
       let value: i64 = parse_config(data)?;
       Ok(value)
   }

   pub fn main() {
       match load_config("settings.toml".to_string()) {
           Ok(config) => {
               println!("{}", config);
           }
           Err(e) => {
               println!("Failed: {}", e);
           }
       }
   }

Explicit Unwrap Methods
-----------------------

**IMPORTANT:** spicycrab does NOT auto-generate ``.unwrap()`` calls in Rust code
unless explicitly requested in Python. This promotes safer error handling.

To explicitly unwrap a Result or Option, use the static method syntax:

Basic unwrap
^^^^^^^^^^^^

.. code-block:: python

   from spicycrab.types import Result, Ok, Err

   def get_value() -> Result[int, str]:
       return Ok(42)

   def main() -> None:
       result: Result[int, str] = get_value()
       value: int = Result.unwrap(result)
       print(value)

.. code-block:: rust

   pub fn get_value() -> Result<i64, String> {
       Ok(42)
   }

   fn main() {
       let result: Result<i64, String> = get_value();
       let value: i64 = result.unwrap();
       println!("{}", value);
   }

unwrap_or with default
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def get_err() -> Result[int, str]:
       return Err("error")

   def main() -> None:
       result: Result[int, str] = get_err()
       value: int = Result.unwrap_or(result, 0)
       print(value)

.. code-block:: rust

   pub fn get_err() -> Result<i64, String> {
       Err("error".to_string())
   }

   fn main() {
       let result: Result<i64, String> = get_err();
       let value: i64 = result.unwrap_or(0);
       println!("{}", value);
   }

expect with custom message
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from spicycrab.types import Result, Ok, Err

   def get_value() -> Result[int, str]:
       return Ok(100)

   def main() -> None:
       result: Result[int, str] = get_value()
       value: int = Result.expect(result, "should have value")
       print(value)

.. code-block:: rust

   pub fn get_value() -> Result<i64, String> {
       Ok(100)
   }

   fn main() {
       let result: Result<i64, String> = get_value();
       let value: i64 = result.expect("should have value");
       println!("{}", value);
   }

Checking Result status
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from spicycrab.types import Result, Ok, Err

   def get_value() -> Result[int, str]:
       return Ok(42)

   def get_err() -> Result[int, str]:
       return Err("failed")

   def main() -> None:
       ok_result: Result[int, str] = get_value()
       if Result.is_ok(ok_result):
           print("got ok")

       err_result: Result[int, str] = get_err()
       if Result.is_err(err_result):
           print("got err")

.. code-block:: rust

   pub fn get_value() -> Result<i64, String> {
       Ok(42)
   }

   pub fn get_err() -> Result<i64, String> {
       Err("failed".to_string())
   }

   fn main() {
       let ok_result: Result<i64, String> = get_value();
       if ok_result.is_ok() {
           println!("{}", "got ok");
       }

       let err_result: Result<i64, String> = get_err();
       if err_result.is_err() {
           println!("{}", "got err");
       }
   }

Supported static methods
^^^^^^^^^^^^^^^^^^^^^^^^

+--------------------------------+-----------------------------+
| Python                         | Rust                        |
+================================+=============================+
| ``Result.unwrap(x)``           | ``x.unwrap()``              |
+--------------------------------+-----------------------------+
| ``Result.expect(x, msg)``      | ``x.expect(msg)``           |
+--------------------------------+-----------------------------+
| ``Result.unwrap_or(x, default)``| ``x.unwrap_or(default)``   |
+--------------------------------+-----------------------------+
| ``Result.unwrap_err(x)``       | ``x.unwrap_err()``          |
+--------------------------------+-----------------------------+
| ``Result.is_ok(x)``            | ``x.is_ok()``               |
+--------------------------------+-----------------------------+
| ``Result.is_err(x)``           | ``x.is_err()``              |
+--------------------------------+-----------------------------+
| ``Option.unwrap(x)``           | ``x.unwrap()``              |
+--------------------------------+-----------------------------+
| ``Option.expect(x, msg)``      | ``x.expect(msg)``           |
+--------------------------------+-----------------------------+
| ``Option.unwrap_or(x, default)``| ``x.unwrap_or(default)``   |
+--------------------------------+-----------------------------+
| ``Option.is_some(x)``          | ``x.is_some()``             |
+--------------------------------+-----------------------------+
| ``Option.is_none(x)``          | ``x.is_none()``             |
+--------------------------------+-----------------------------+

String Methods for Validation
-----------------------------

Common string methods for input validation:

.. code-block:: python

   def validate_input(s: str) -> Result[str, str]:
       if not s.isalpha():
           return Err("must be alphabetic")
       return Ok(s)

   def validate_number(s: str) -> Result[str, str]:
       if not s.isdigit():
           return Err("must be numeric")
       return Ok(s)

   def validate_alnum(s: str) -> Result[str, str]:
       if not s.isalnum():
           return Err("must be alphanumeric")
       return Ok(s)

.. code-block:: rust

   pub fn validate_input(s: String) -> Result<String, String> {
       if !s.chars().all(|c| c.is_alphabetic()) {
           return Err("must be alphabetic".to_string());
       }
       Ok(s)
   }

   pub fn validate_number(s: String) -> Result<String, String> {
       if !s.chars().all(|c| c.is_ascii_digit()) {
           return Err("must be numeric".to_string());
       }
       Ok(s)
   }

   pub fn validate_alnum(s: String) -> Result<String, String> {
       if !s.chars().all(|c| c.is_alphanumeric()) {
           return Err("must be alphanumeric".to_string());
       }
       Ok(s)
   }
