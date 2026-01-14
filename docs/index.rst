spicycrab Documentation
========================

**spicycrab** is a Python to Rust transpiler for type-annotated Python code.

.. warning::

   **Active Development**: spicycrab and cookcrab are under active development.
   APIs, CLI options, and generated code may change frequently. Please check the
   changelog and documentation for updates when upgrading.

It provides two CLI tools:

- ``crabpy`` - Transpile Python code to Rust
- ``cookcrab`` - Generate Python stubs from Rust crates

It converts idiomatic, typed Python into idiomatic Rust, handling:

- Type annotations → Rust types
- Classes → structs with impl blocks
- Context managers → RAII (Drop trait)
- Error handling → Result types with ``?`` operator
- Async/await → tokio runtime with ``#[tokio::main]``
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
   async
   actix_web
   cookcrab
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
