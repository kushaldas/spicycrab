Command Line Interface
======================

spicycrab provides two CLI tools:

- ``crabpy`` - Transpile Python to Rust
- ``cookcrab`` - Generate Python stubs from Rust crates

crabpy
------

The ``crabpy`` CLI transpiles Python code to Rust.

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
^^^^^^^^^^

- ``0`` - Success
- ``1`` - Transpilation error
- ``2`` - Invalid arguments

cookcrab
--------

The ``cookcrab`` CLI generates Python stubs from Rust crates.

Basic Usage
^^^^^^^^^^^

.. code-block:: bash

   cookcrab [COMMAND] [OPTIONS]

Commands
^^^^^^^^

generate
""""""""

Generate Python stubs from a Rust crate.

.. code-block:: bash

   cookcrab generate <CRATE> [OPTIONS]

**Options:**

``-o, --output``
   Output directory (default: current directory)

``--version``
   Crate version (default: latest)

``--local``
   Treat CRATE as a local path instead of crates.io name

**Examples:**

.. code-block:: bash

   # Generate stubs for latest clap
   cookcrab generate clap -o /tmp/stubs

   # Generate stubs for specific version
   cookcrab generate anyhow --version 1.0.80 -o /tmp/stubs

   # Generate from local crate
   cookcrab generate /path/to/mycrate --local -o /tmp/stubs

install
"""""""

Install a stub package from the spicycrab-stubs repository.

.. code-block:: bash

   cookcrab install <CRATE> [OPTIONS]

**Options:**

``--version``
   Stub version to install

**Examples:**

.. code-block:: bash

   cookcrab install clap
   cookcrab install serde --version 1.0.0

search
""""""

Search for available stub packages.

.. code-block:: bash

   cookcrab search <QUERY>

**Examples:**

.. code-block:: bash

   cookcrab search clap
   cookcrab search serde

validate
""""""""

Validate a stub package structure.

.. code-block:: bash

   cookcrab validate <PATH>

**Examples:**

.. code-block:: bash

   cookcrab validate /tmp/stubs/clap

build
"""""

Build a wheel from a stub package.

.. code-block:: bash

   cookcrab build <PATH>

**Examples:**

.. code-block:: bash

   cookcrab build /tmp/stubs/clap

Workflow Example
^^^^^^^^^^^^^^^^

Complete workflow to use a Rust crate in Python and transpile:

.. code-block:: bash

   # 1. Generate stubs
   cookcrab generate clap -o /tmp/stubs

   # 2. Install stubs (handles dependencies automatically)
   python3 -m pip install -e /tmp/stubs/clap_builder
   python3 -m pip install -e /tmp/stubs/clap

   # 3. Write Python code using stub types
   cat > myapp.py << 'EOF'
   from spicycrab_clap import Command, Arg, ArgMatches

   def main() -> None:
       matches: ArgMatches = (
           Command.new("myapp")
           .arg(Arg.new("name").required(True))
           .get_matches()
       )
       name: str = matches.get_one("name").unwrap().clone()
       print(f"Hello, {name}!")
   EOF

   # 4. Transpile to Rust
   crabpy transpile myapp.py -o rust_myapp -n myapp

   # 5. Build and run
   cd rust_myapp
   cargo build --release
   ./target/release/myapp World

Exit Codes
^^^^^^^^^^

- ``0`` - Success
- ``1`` - Error (parse error, download error, validation error)
- ``2`` - Invalid arguments
