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
