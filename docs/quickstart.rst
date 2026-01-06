Quickstart
==========

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
