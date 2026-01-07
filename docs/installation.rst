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

Development Setup
-----------------

For contributing or development, use ``uv`` to set up the environment:

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/kushaldas/spicycrab.git
   cd spicycrab

   # Create virtual environment
   uv venv
   source .venv/bin/activate

   # Install with all development and documentation dependencies
   uv pip install -e ".[dev,docs]"

This installs:

- **dev**: pytest, pytest-cov, mypy, ruff (for testing and linting)
- **docs**: sphinx, sphinx-rtd-theme, myst-parser (for building documentation)

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
