Code Quality
============

spicycrab generates Rust code that is designed to pass ``cargo clippy`` with minimal warnings.

Clippy Compatibility
--------------------

All integration tests run ``cargo clippy`` on generated code to ensure quality.

Idiomatic Patterns
^^^^^^^^^^^^^^^^^^

The transpiler automatically generates idiomatic Rust patterns to avoid common clippy warnings:

+--------------------------------+------------------------------+
| Python Pattern                 | Rust Output                  |
+================================+==============================+
| ``len(x) > 0``                 | ``!x.is_empty()``            |
+--------------------------------+------------------------------+
| ``len(x) == 0``                | ``x.is_empty()``             |
+--------------------------------+------------------------------+
| ``len(x) >= 1``                | ``!x.is_empty()``            |
+--------------------------------+------------------------------+
| ``x = x + y``                  | ``x += y``                   |
+--------------------------------+------------------------------+
| ``x = x - y``                  | ``x -= y``                   |
+--------------------------------+------------------------------+
| ``self.attr = self.attr + y``  | ``self.attr += y``           |
+--------------------------------+------------------------------+
| ``Self { value: value }``      | ``Self { value }``           |
+--------------------------------+------------------------------+
| ``println!("{}", "literal")``  | ``println!("literal")``      |
+--------------------------------+------------------------------+

Example: Length Checks
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def has_items(items: list[int]) -> bool:
       return len(items) > 0

   def is_empty(items: list[int]) -> bool:
       return len(items) == 0

.. code-block:: rust

   pub fn has_items(items: Vec<i64>) -> bool {
       !items.is_empty()
   }

   pub fn is_empty(items: Vec<i64>) -> bool {
       items.is_empty()
   }

Example: Compound Assignment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def increment(x: int) -> int:
       x = x + 1
       return x

   class Counter:
       def __init__(self, value: int) -> None:
           self.value = value

       def increment(self) -> None:
           self.value = self.value + 1

.. code-block:: rust

   pub fn increment(mut x: i64) -> i64 {
       x += 1;
       x
   }

   impl Counter {
       pub fn increment(&mut self) {
           self.value += 1;
       }
   }

Allowed Clippy Lints
--------------------

The following lints are allowed in generated code as they are either stylistic
or would require complex code analysis to fix automatically:

+-------------------------------+------------------------------------------------+
| Lint                          | Reason                                         |
+===============================+================================================+
| ``unused_variables``          | Generated code may declare variables that      |
|                               | aren't used in all code paths                  |
+-------------------------------+------------------------------------------------+
| ``unused_mut``                | Transpiler may conservatively mark variables   |
|                               | as mutable when mutation is possible           |
+-------------------------------+------------------------------------------------+
| ``clippy::vec_init_then_push``| Optimizing ``vec![] + push()`` to              |
|                               | ``vec![items]`` requires complex analysis      |
+-------------------------------+------------------------------------------------+

Running Clippy Manually
-----------------------

To run clippy on generated Rust code with the recommended settings:

.. code-block:: bash

   cargo clippy -- -D warnings -A unused_variables -A unused_mut -A clippy::vec_init_then_push

Or to see all warnings without failing:

.. code-block:: bash

   cargo clippy

Future Improvements
-------------------

The following clippy optimizations are planned for future versions:

- ``vec_init_then_push``: Detect consecutive push calls after ``vec![]`` creation
- Better mutability analysis to reduce ``unused_mut`` warnings
- Dead code elimination to reduce ``unused_variables`` warnings
