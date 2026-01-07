Installation
============

Requirements
------------

- Python 3.10 or higher
- Rust toolchain (for compiling generated code)

Install from PyPI
-----------------

.. code-block:: bash

   python3 -m pip install spicycrab

Install from Source
-------------------

.. code-block:: bash

   git clone https://github.com/example/spicycrab.git
   cd spicycrab
   python3 -m pip install -e .

Install with Development Dependencies
-------------------------------------

.. code-block:: bash

   python3 -m pip install -e ".[dev]"

Verify Installation
-------------------

spicycrab provides two CLI tools:

.. code-block:: bash

   # Transpiler CLI
   crabpy --version

   # Stub generator CLI
   cookcrab --version

Rust Toolchain
--------------

To compile the generated Rust code, install Rust:

.. code-block:: bash

   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

Verify with:

.. code-block:: bash

   cargo --version
   rustc --version
