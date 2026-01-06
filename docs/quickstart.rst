Quickstart
==========

.. important::

   **Binary Executables**: If your Python file contains a ``def main() -> None:``
   function, spicycrab generates a **binary executable** (``main.rs``).
   Without a ``main()`` function, it generates a **library** (``lib.rs``).

Your First Transpilation
------------------------

Create a Python file ``hello.py``:

.. code-block:: python

   def greet(name: str) -> str:
       return f"Hello, {name}!"

   def main() -> None:
       message: str = greet("World")
       print(message)

Transpile it:

.. code-block:: bash

   crabpy transpile hello.py -o ./output

This creates:

- ``output/src/main.rs`` - Your Rust code
- ``output/Cargo.toml`` - Cargo project file

Generated Rust
--------------

.. code-block:: rust

   pub fn greet(name: String) -> String {
       format!("Hello, {}!", name)
   }

   pub fn main() {
       let message: String = greet("World".to_string());
       println!("{}", message);
   }

Build and Run
-------------

.. code-block:: bash

   cd output
   cargo run

Output::

   Hello, World!

Adding Type Annotations
-----------------------

spicycrab requires type annotations. Add them to your Python code:

.. code-block:: python

   # Before (won't transpile)
   def add(a, b):
       return a + b

   # After (will transpile)
   def add(a: int, b: int) -> int:
       return a + b

Transpiling a Directory
-----------------------

.. code-block:: bash

   crabpy transpile ./myproject -o ./rust_project

This creates a multi-file Rust project with proper module structure.

Binary vs Library
-----------------

spicycrab automatically detects whether to generate a binary or library:

**With main() → Binary executable:**

.. code-block:: python

   def add(a: int, b: int) -> int:
       return a + b

   def main() -> None:
       result: int = add(2, 3)
       print(result)

Generates ``src/main.rs``:

.. code-block:: rust

   pub fn add(a: i64, b: i64) -> i64 {
       a + b
   }

   pub fn main() {
       let result: i64 = add(2, 3);
       println!("{}", result);
   }

Run with ``cargo run``.

**Without main() → Library:**

.. code-block:: python

   def add(a: int, b: int) -> int:
       return a + b

Generates ``src/lib.rs`` with your functions as a reusable library.
