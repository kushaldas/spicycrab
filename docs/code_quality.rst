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
| ``v = []; v.append(x)``        | ``let v = vec![x];``         |
+--------------------------------+------------------------------+
| Unused local assignment        | ``let _name = value;``       |
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

Generated Lint Configuration
----------------------------

Generated ``Cargo.toml`` keeps lint allowances narrow. These lints are allowed
because they are stylistic or are required by Python-compatible code generation:

* ``unused_must_use``: async channel operations can intentionally ignore
  returned ``Result`` values.
* ``clippy::unnecessary_cast``: conservative casts preserve Python int
  semantics across Rust integer widths.
* ``clippy::unnecessary_to_owned``: string ownership conversions are sometimes
  emitted before borrowing.
* ``clippy::format_in_format_args``: f-string transpilation can create nested
  ``format!`` inside ``println!``.

The emitter reduces common warnings directly:

* Consecutive ``append``/``push`` calls after an empty list declaration become a
  single ``vec![...]`` initializer.
* Single-assignment locals that are never read are emitted as underscore
  bindings, preserving initializer side effects while avoiding unused-variable
  warnings.
* Mutability analysis recognizes receiver mutations and calls such as
  ``random.shuffle(items)``.

Running Clippy Manually
-----------------------

To run clippy on generated Rust code:

.. code-block:: bash

   cargo clippy -- -D warnings

Or to see all warnings without failing:

.. code-block:: bash

   cargo clippy
