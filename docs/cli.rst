Command Line Interface
======================

spicycrab provides the ``crabpy`` CLI for transpiling Python to Rust.

Basic Usage
-----------

.. code-block:: bash

   crabpy [COMMAND] [OPTIONS]

Commands
--------

transpile
^^^^^^^^^

Transpile Python code to Rust.

**Single file:**

.. code-block:: bash

   crabpy transpile file.py -o ./output

**Directory:**

.. code-block:: bash

   crabpy transpile ./myproject -o ./rust_project

**Options:**

``-o, --output``
   Output directory (required)

``-v, --verbose``
   Show verbose output

**Examples:**

.. code-block:: bash

   # Transpile a single file
   crabpy transpile hello.py -o ./output

   # Transpile with verbose output
   crabpy transpile hello.py -o ./output -v

   # Transpile an entire project
   crabpy transpile ./src/myapp -o ./rust_app

parse
^^^^^

Parse Python code and show the IR (intermediate representation).

.. code-block:: bash

   crabpy parse file.py

**Options:**

``-v, --verbose``
   Show detailed IR output

**Examples:**

.. code-block:: bash

   # Parse and show IR
   crabpy parse hello.py

   # Parse with verbose output
   crabpy parse hello.py -v

test
^^^^

Test transpilation by compiling and optionally running the generated Rust.

.. code-block:: bash

   crabpy test file.py

**Options:**

``--run``
   Run the compiled binary after building

**Examples:**

.. code-block:: bash

   # Test that transpiled code compiles
   crabpy test hello.py

   # Test and run
   crabpy test hello.py --run

Output Structure
----------------

Single File
^^^^^^^^^^^

.. code-block:: bash

   crabpy transpile hello.py -o ./output

Creates::

   output/
   ├── Cargo.toml
   └── src/
       └── main.rs

Multi-file Project
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   crabpy transpile ./myproject -o ./output

Creates::

   output/
   ├── Cargo.toml
   └── src/
       ├── main.rs      # Entry point
       ├── lib.rs       # Module declarations
       ├── module1.rs   # Each .py becomes .rs
       └── module2.rs

Examples
--------

Hello World
^^^^^^^^^^^

**Input (hello.py):**

.. code-block:: python

   def main() -> None:
       print("Hello, World!")

**Command:**

.. code-block:: bash

   crabpy transpile hello.py -o ./output
   cd output
   cargo run

**Output:**

::

   Hello, World!

Calculator
^^^^^^^^^^

**Input (calc.py):**

.. code-block:: python

   def add(a: int, b: int) -> int:
       return a + b

   def main() -> None:
       result: int = add(2, 3)
       print(result)

**Command:**

.. code-block:: bash

   crabpy transpile calc.py -o ./output
   cd output
   cargo run

**Output:**

::

   5

Error Messages
--------------

Missing type annotation
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   $ crabpy transpile untyped.py -o ./output
   Error: Missing type annotation for parameter 'x' in function 'foo'

Unsupported feature
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   $ crabpy transpile async_code.py -o ./output
   Error: async/await is not yet supported

Exit Codes
----------

- ``0`` - Success
- ``1`` - Transpilation error
- ``2`` - Invalid arguments
