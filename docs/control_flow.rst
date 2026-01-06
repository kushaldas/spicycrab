Control Flow
============

Conditionals
------------

if statement
^^^^^^^^^^^^

.. code-block:: python

   def check_positive(n: int) -> bool:
       if n > 0:
           return True
       return False

.. code-block:: rust

   pub fn check_positive(n: i64) -> bool {
       if n > 0 {
           return true;
       }
       false
   }

if-else
^^^^^^^

.. code-block:: python

   def max_value(a: int, b: int) -> int:
       if a > b:
           return a
       else:
           return b

.. code-block:: rust

   pub fn max_value(a: i64, b: i64) -> i64 {
       if a > b {
           return a;
       } else {
           return b;
       }
   }

if-elif-else
^^^^^^^^^^^^

.. code-block:: python

   def grade(score: int) -> str:
       if score >= 90:
           return "A"
       elif score >= 80:
           return "B"
       elif score >= 70:
           return "C"
       else:
           return "F"

.. code-block:: rust

   pub fn grade(score: i64) -> String {
       if score >= 90 {
           return "A".to_string();
       } else if score >= 80 {
           return "B".to_string();
       } else if score >= 70 {
           return "C".to_string();
       } else {
           return "F".to_string();
       }
   }

Nested if
^^^^^^^^^

.. code-block:: python

   def classify(x: int, y: int) -> str:
       if x > 0:
           if y > 0:
               return "first quadrant"
           else:
               return "fourth quadrant"
       else:
           return "left side"

.. code-block:: rust

   pub fn classify(x: i64, y: i64) -> String {
       if x > 0 {
           if y > 0 {
               return "first quadrant".to_string();
           } else {
               return "fourth quadrant".to_string();
           }
       } else {
           return "left side".to_string();
       }
   }

Loops
-----

for loop with range
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def sum_to_n(n: int) -> int:
       total: int = 0
       for i in range(n):
           total = total + i
       return total

.. code-block:: rust

   pub fn sum_to_n(n: i64) -> i64 {
       let mut total: i64 = 0;
       for i in 0..n {
           total = total + i;
       }
       total
   }

for loop with start and end
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def sum_range(start: int, end: int) -> int:
       total: int = 0
       for i in range(start, end):
           total = total + i
       return total

.. code-block:: rust

   pub fn sum_range(start: i64, end: i64) -> i64 {
       let mut total: i64 = 0;
       for i in start..end {
           total = total + i;
       }
       total
   }

for loop over list
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def sum_list(items: list[int]) -> int:
       total: int = 0
       for item in items:
           total = total + item
       return total

.. code-block:: rust

   pub fn sum_list(items: Vec<i64>) -> i64 {
       let mut total: i64 = 0;
       for item in items {
           total = total + item;
       }
       total
   }

while loop
^^^^^^^^^^

.. code-block:: python

   def countdown(n: int) -> None:
       while n > 0:
           print(n)
           n = n - 1

.. code-block:: rust

   pub fn countdown(n: i64) {
       let mut n = n;
       while n > 0 {
           println!("{}", n);
           n = n - 1;
       }
   }

Loop Control
------------

break
^^^^^

.. code-block:: python

   def find_first_negative(items: list[int]) -> int:
       for item in items:
           if item < 0:
               return item
       return 0

.. code-block:: rust

   pub fn find_first_negative(items: Vec<i64>) -> i64 {
       for item in items {
           if item < 0 {
               return item;
           }
       }
       0
   }

continue
^^^^^^^^

.. code-block:: python

   def sum_positive(items: list[int]) -> int:
       total: int = 0
       for item in items:
           if item < 0:
               continue
           total = total + item
       return total

.. code-block:: rust

   pub fn sum_positive(items: Vec<i64>) -> i64 {
       let mut total: i64 = 0;
       for item in items {
           if item < 0 {
               continue;
           }
           total = total + item;
       }
       total
   }

Comparison Operators
--------------------

.. code-block:: python

   def compare(a: int, b: int) -> None:
       if a == b:
           print("equal")
       if a != b:
           print("not equal")
       if a < b:
           print("less than")
       if a <= b:
           print("less or equal")
       if a > b:
           print("greater than")
       if a >= b:
           print("greater or equal")

.. code-block:: rust

   pub fn compare(a: i64, b: i64) {
       if a == b {
           println!("equal");
       }
       if a != b {
           println!("not equal");
       }
       if a < b {
           println!("less than");
       }
       if a <= b {
           println!("less or equal");
       }
       if a > b {
           println!("greater than");
       }
       if a >= b {
           println!("greater or equal");
       }
   }

Logical Operators
-----------------

.. code-block:: python

   def check(x: int) -> bool:
       if x > 0 and x < 100:
           return True
       if x < -100 or x > 100:
           return False
       if not x == 0:
           return True
       return False

.. code-block:: rust

   pub fn check(x: i64) -> bool {
       if x > 0 && x < 100 {
           return true;
       }
       if x < -100 || x > 100 {
           return false;
       }
       if !(x == 0) {
           return true;
       }
       false
   }
