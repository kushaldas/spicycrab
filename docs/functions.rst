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
