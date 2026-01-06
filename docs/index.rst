spicycrab Documentation
========================

**spicycrab** (CLI: ``crabpy``) is a Python to Rust transpiler for type-annotated Python code.

It converts idiomatic, typed Python into idiomatic Rust, handling:

- Type annotations → Rust types
- Classes → structs with impl blocks
- Context managers → RAII (Drop trait)
- Error handling → Result types with ``?`` operator
- Standard library → Rust equivalents

Quick Example
-------------

Python input:

.. code-block:: python

   def greet(name: str) -> str:
       return f"Hello, {name}!"

   def main() -> None:
       message: str = greet("World")
       print(message)

Rust output:

.. code-block:: rust

   pub fn greet(name: String) -> String {
       format!("Hello, {}!", name)
   }

   pub fn main() {
       let message: String = greet("World".to_string());
       println!("{}", message);
   }

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   types
   functions
   classes
   control_flow
   error_handling
   stdlib
   multifile
   code_quality

.. toctree::
   :maxdepth: 2
   :caption: Reference

   cli
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
