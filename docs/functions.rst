Functions
=========

Basic Functions
---------------

Simple function
^^^^^^^^^^^^^^^

.. code-block:: python

   def square(x: int) -> int:
       return x * x

.. code-block:: rust

   pub fn square(x: i64) -> i64 {
       x * x
   }

Multiple parameters
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def add(a: int, b: int) -> int:
       return a + b

.. code-block:: rust

   pub fn add(a: i64, b: i64) -> i64 {
       a + b
   }

No return value
^^^^^^^^^^^^^^^

.. code-block:: python

   def log(message: str) -> None:
       print(message)

.. code-block:: rust

   pub fn log(message: String) {
       println!("{}", message);
   }

Default Arguments
-----------------

.. code-block:: python

   def greet(name: str, greeting: str = "Hello") -> str:
       return f"{greeting}, {name}!"

.. code-block:: rust

   pub fn greet(name: String, greeting: Option<String>) -> String {
       let greeting = greeting.unwrap_or("Hello".to_string());
       format!("{}, {}!", greeting, name)
   }

String Parameters
-----------------

Strings as input
^^^^^^^^^^^^^^^^

.. code-block:: python

   def count_chars(s: str) -> int:
       return len(s)

.. code-block:: rust

   pub fn count_chars(s: String) -> i64 {
       s.len() as i64
   }

Local Variables
---------------

Immutable by default
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def compute() -> int:
       x: int = 10
       y: int = 20
       return x + y

.. code-block:: rust

   pub fn compute() -> i64 {
       let x: i64 = 10;
       let y: i64 = 20;
       x + y
   }

Mutable variables
^^^^^^^^^^^^^^^^^

.. code-block:: python

   def increment() -> int:
       x: int = 0
       x = x + 1
       x = x + 1
       return x

.. code-block:: rust

   pub fn increment() -> i64 {
       let mut x: i64 = 0;
       x = x + 1;
       x = x + 1;
       x
   }

Forward declarations
^^^^^^^^^^^^^^^^^^^^

Variables can be declared with a type annotation but no initial value.
This creates an uninitialized variable that must be assigned before use:

.. code-block:: python

   def process(flag: bool) -> str:
       result: str
       if flag:
           result = "yes"
       else:
           result = "no"
       return result

.. code-block:: rust

   pub fn process(flag: bool) -> String {
       let result: String;
       if flag {
           result = "yes".to_string();
       } else {
           result = "no".to_string();
       }
       result
   }

This is useful when a variable's value depends on conditional logic,
similar to Rust's deferred initialization pattern.

Return Statements
-----------------

Early return
^^^^^^^^^^^^

.. code-block:: python

   def absolute(x: int) -> int:
       if x < 0:
           return -x
       return x

.. code-block:: rust

   pub fn absolute(x: i64) -> i64 {
       if x < 0 {
           return -x;
       }
       x
   }

Multiple return points
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def classify(n: int) -> str:
       if n < 0:
           return "negative"
       if n == 0:
           return "zero"
       return "positive"

.. code-block:: rust

   pub fn classify(n: i64) -> String {
       if n < 0 {
           return "negative".to_string();
       }
       if n == 0 {
           return "zero".to_string();
       }
       "positive".to_string()
   }

Calling Functions
-----------------

.. code-block:: python

   def double(x: int) -> int:
       return x * 2

   def quadruple(x: int) -> int:
       return double(double(x))

.. code-block:: rust

   pub fn double(x: i64) -> i64 {
       x * 2
   }

   pub fn quadruple(x: i64) -> i64 {
       double(double(x))
   }

Built-in Functions
------------------

len()
^^^^^

.. code-block:: python

   def list_length(items: list[int]) -> int:
       return len(items)

.. code-block:: rust

   pub fn list_length(items: Vec<i64>) -> i64 {
       items.len() as i64
   }

print()
^^^^^^^

.. code-block:: python

   def show(value: int) -> None:
       print(value)

.. code-block:: rust

   pub fn show(value: i64) {
       println!("{}", value);
   }

range()
^^^^^^^

.. code-block:: python

   def sum_range(n: int) -> int:
       total: int = 0
       for i in range(n):
           total = total + i
       return total

.. code-block:: rust

   pub fn sum_range(n: i64) -> i64 {
       let mut total: i64 = 0;
       for i in 0..n {
           total = total + i;
       }
       total
   }

F-Strings
---------

Python f-strings are transpiled to Rust's ``format!`` macro.

Basic f-strings
^^^^^^^^^^^^^^^

.. code-block:: python

   def greet(name: str) -> str:
       return f"Hello, {name}!"

   def show_info(name: str, age: int) -> None:
       print(f"{name} is {age} years old")

.. code-block:: rust

   pub fn greet(name: String) -> String {
       format!("Hello, {}!", name)
   }

   pub fn show_info(name: String, age: i64) {
       println!("{} is {} years old", name, age);
   }

Format Specifiers
^^^^^^^^^^^^^^^^^

Python format specifiers are preserved in the Rust output. This is useful
for controlling how values are formatted (hex, padding, precision, etc.).

**Hexadecimal formatting:**

.. code-block:: python

   def to_hex(value: int) -> str:
       return f"{value:x}"

   def to_hex_upper(value: int) -> str:
       return f"{value:X}"

   def to_hex_padded(value: int) -> str:
       return f"{value:08x}"

.. code-block:: rust

   pub fn to_hex(value: i64) -> String {
       format!("{:x}", value)
   }

   pub fn to_hex_upper(value: i64) -> String {
       format!("{:X}", value)
   }

   pub fn to_hex_padded(value: i64) -> String {
       format!("{:08x}", value)
   }

**Float precision:**

.. code-block:: python

   def format_price(amount: float) -> str:
       return f"${amount:.2f}"

   def format_scientific(value: float) -> str:
       return f"{value:.4e}"

.. code-block:: rust

   pub fn format_price(amount: f64) -> String {
       format!("${:.2f}", amount)
   }

   pub fn format_scientific(value: f64) -> String {
       format!("{:.4e}", value)
   }

**Width and alignment:**

.. code-block:: python

   def pad_right(s: str) -> str:
       return f"{s:<10}"

   def pad_left(s: str) -> str:
       return f"{s:>10}"

   def center(s: str) -> str:
       return f"{s:^10}"

.. code-block:: rust

   pub fn pad_right(s: String) -> String {
       format!("{:<10}", s)
   }

   pub fn pad_left(s: String) -> String {
       format!("{:>10}", s)
   }

   pub fn center(s: String) -> String {
       format!("{:^10}", s)
   }

**Common format specifiers:**

+-------------------+---------------------+----------------------------------+
| Specifier         | Example             | Description                      |
+===================+=====================+==================================+
| ``:x``            | ``f"{255:x}"``      | Lowercase hexadecimal            |
+-------------------+---------------------+----------------------------------+
| ``:X``            | ``f"{255:X}"``      | Uppercase hexadecimal            |
+-------------------+---------------------+----------------------------------+
| ``:08x``          | ``f"{255:08x}"``    | Hex padded to 8 chars with zeros |
+-------------------+---------------------+----------------------------------+
| ``:.2f``          | ``f"{3.14159:.2f}"``| Float with 2 decimal places      |
+-------------------+---------------------+----------------------------------+
| ``:>10``          | ``f"{s:>10}"``      | Right-align in 10 chars          |
+-------------------+---------------------+----------------------------------+
| ``:<10``          | ``f"{s:<10}"``      | Left-align in 10 chars           |
+-------------------+---------------------+----------------------------------+
| ``:^10``          | ``f"{s:^10}"``      | Center in 10 chars               |
+-------------------+---------------------+----------------------------------+
| ``:b``            | ``f"{10:b}"``       | Binary format                    |
+-------------------+---------------------+----------------------------------+
| ``:o``            | ``f"{64:o}"``       | Octal format                     |
+-------------------+---------------------+----------------------------------+

.. note::

   Format specifiers in Rust's ``format!`` macro are similar but not identical
   to Python's. Most common specifiers work the same way.
