Cookcrab: Stub Generator
========================

**cookcrab** is the companion tool to spicycrab that generates Python type stubs from Rust crates.
These stubs enable spicycrab to transpile Python code that uses Rust libraries.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

When you want to use a Rust crate (like ``clap``, ``anyhow``, or ``serde``) in your Python code
and then transpile it to Rust, you need **stub packages**. These stubs:

1. Provide Python type hints for IDE autocompletion
2. Define mappings from Python API calls to Rust code
3. Specify cargo dependencies for the generated Rust project

**Workflow:**

1. Generate stubs: ``cookcrab generate <crate_name>``
2. Install stubs: ``python3 -m pip install -e /path/to/stubs/<crate>``
3. Write Python code using the stub types
4. Transpile: ``crabpy transpile mycode.py``

Installation
------------

cookcrab is included with spicycrab:

.. code-block:: bash

   python3 -m pip install spicycrab

   # Verify installation
   cookcrab --help

Commands
--------

generate
^^^^^^^^

Generate Python stubs from a Rust crate.

**From crates.io (recommended):**

.. code-block:: bash

   # Generate stubs for the latest version
   cookcrab generate clap -o /tmp/stubs

   # Generate stubs for a specific version
   cookcrab generate clap --version 4.5.0 -o /tmp/stubs

**From a local crate:**

.. code-block:: bash

   cookcrab generate /path/to/my_crate --local -o /tmp/stubs

**Output structure:**

::

   /tmp/stubs/
   └── clap/
       ├── pyproject.toml
       ├── README.md
       └── spicycrab_clap/
           ├── __init__.py      # Python type stubs
           └── _spicycrab.toml  # Transpilation mappings

install
^^^^^^^

Install a stub package from the spicycrab-stubs repository.

.. code-block:: bash

   # Install from official stubs repository
   cookcrab install clap

   # Install a specific version
   cookcrab install clap --version 4.5.0

.. note::

   Always use ``cookcrab install`` rather than ``python3 -m pip install`` directly.
   The stubs index ensures compatibility with spicycrab.

search
^^^^^^

Search for available stub packages.

.. code-block:: bash

   cookcrab search clap
   cookcrab search serde

validate
^^^^^^^^

Validate a stub package structure.

.. code-block:: bash

   cookcrab validate /tmp/stubs/clap

build
^^^^^

Build a wheel from a stub package.

.. code-block:: bash

   cookcrab build /tmp/stubs/clap

Generating Stubs
----------------

Basic Example: anyhow
^^^^^^^^^^^^^^^^^^^^^

Let's generate stubs for the ``anyhow`` error handling crate:

.. code-block:: bash

   # Generate stubs
   cookcrab generate anyhow -o /tmp/stubs

   # Install the generated stubs
   python3 -m pip install -e /tmp/stubs/anyhow

Now you can write Python code using anyhow types:

.. code-block:: python

   from spicycrab_anyhow import Result, Error

   def divide(a: int, b: int) -> Result[int, Error]:
       if b == 0:
           return Result.Err(Error.msg("Division by zero"))
       return Result.Ok(a // b)

   def main() -> None:
       result: Result[int, Error] = divide(10, 2)
       print(f"Result: {result}")

Transpile:

.. code-block:: bash

   crabpy transpile divide.py -o rust_divide -n divide

Generated Rust:

.. code-block:: rust

   use anyhow;

   pub fn divide(a: i64, b: i64) -> anyhow::Result<i64> {
       if b == 0 {
           return Err(anyhow::anyhow!("Division by zero"));
       }
       Ok(a / b)
   }

   pub fn main() {
       let result: anyhow::Result<i64> = divide(10, 2);
       println!("{}", format!("Result: {:?}", result));
   }

Complex Example: clap
^^^^^^^^^^^^^^^^^^^^^

The ``clap`` crate demonstrates handling re-exports. clap re-exports from ``clap_builder``,
so cookcrab automatically generates stubs for both:

.. code-block:: bash

   # Generate stubs (automatically handles re-exports)
   cookcrab generate clap -o /tmp/stubs

   # Install both clap and clap_builder stubs
   python3 -m pip install -e /tmp/stubs/clap_builder
   python3 -m pip install -e /tmp/stubs/clap

Write a CLI application:

.. code-block:: python

   from spicycrab_clap import Command, Arg, ArgMatches, ArgAction

   def main() -> None:
       matches: ArgMatches = (
           Command.new("myapp")
           .about("My CLI application")
           .arg(
               Arg.new("name")
               .help("Your name")
               .required(True)
           )
           .arg(
               Arg.new("verbose")
               .short('v')
               .long("verbose")
               .help("Enable verbose output")
               .action(ArgAction.SetTrue)
           )
           .get_matches()
       )

       name: str = matches.get_one("name").unwrap().clone()
       verbose: bool = matches.get_flag("verbose")

       if verbose:
           print(f"Hello, {name}! (verbose mode)")
       else:
           print(f"Hello, {name}!")

   if __name__ == "__main__":
       main()

Transpile and run:

.. code-block:: bash

   crabpy transpile myapp.py -o rust_myapp -n myapp
   cd rust_myapp
   cargo build --release
   ./target/release/myapp --help
   ./target/release/myapp "World" -v

Using Stubs
-----------

Import Conventions
^^^^^^^^^^^^^^^^^^

Stub packages follow the naming convention ``spicycrab_<crate_name>``:

.. code-block:: python

   # For the 'clap' crate
   from spicycrab_clap import Command, Arg, ArgMatches

   # For the 'anyhow' crate
   from spicycrab_anyhow import Result, Error

   # For the 'serde' crate
   from spicycrab_serde import Serialize, Deserialize

Type Annotations
^^^^^^^^^^^^^^^^

Stub types are used in type annotations to enable proper transpilation:

.. code-block:: python

   from spicycrab_clap import ArgMatches

   def process_args(matches: ArgMatches) -> None:
       # ArgMatches methods are available
       name_opt = matches.get_one("name")
       if name_opt.is_some():
           name: str = name_opt.unwrap().clone()
           print(f"Name: {name}")

Option and Result Types
^^^^^^^^^^^^^^^^^^^^^^^

Many Rust methods return ``Option`` or ``Result`` types. Stubs provide Python equivalents:

.. code-block:: python

   from spicycrab_clap import ArgMatches

   def get_config(matches: ArgMatches) -> None:
       # get_one returns Option[str]
       config_opt = matches.get_one("config")

       # Check if value exists
       if config_opt.is_some():
           config: str = config_opt.unwrap().clone()
           print(f"Config: {config}")
       else:
           print("No config specified")

Method Chaining
^^^^^^^^^^^^^^^

Stubs support Rust's builder pattern with method chaining:

.. code-block:: python

   from spicycrab_clap import Command, Arg

   cmd = (
       Command.new("app")
       .version("1.0.0")
       .author("Developer")
       .about("My application")
       .arg(
           Arg.new("input")
           .help("Input file")
           .required(True)
       )
       .arg(
           Arg.new("output")
           .short('o')
           .long("output")
           .help("Output file")
       )
   )

Stub Package Structure
----------------------

A stub package contains:

**pyproject.toml**

.. code-block:: toml

   [project]
   name = "spicycrab-clap"
   version = "4.5.54"
   dependencies = ["spicycrab-clap-builder>=4.5.0"]

   [project.entry-points."spicycrab.stubs"]
   clap = "spicycrab_clap"

**spicycrab_clap/__init__.py**

Python type stubs with classes and methods:

.. code-block:: python

   from typing import TypeVar, Generic

   T = TypeVar('T')
   E = TypeVar('E')

   class Command:
       @staticmethod
       def new(name: str) -> "Command": ...

       def about(self, about: str) -> "Command": ...
       def arg(self, arg: "Arg") -> "Command": ...
       def get_matches(self) -> "ArgMatches": ...

   class Arg:
       @staticmethod
       def new(name: str) -> "Arg": ...

       def short(self, short: str) -> "Arg": ...
       def long(self, long: str) -> "Arg": ...
       def help(self, help: str) -> "Arg": ...

   class ArgMatches:
       def get_one(self, name: str) -> "Option[str]": ...
       def get_flag(self, name: str) -> bool: ...

**spicycrab_clap/_spicycrab.toml**

Transpilation mappings:

.. code-block:: toml

   [package]
   name = "clap"
   rust_crate = "clap"
   rust_version = "4.5"
   python_module = "spicycrab_clap"

   [cargo.dependencies.clap]
   version = "4.5"
   features = ["derive"]

   [[mappings.functions]]
   python = "clap.Command.new"
   rust_code = "clap::Command::new({arg0})"
   rust_imports = ["clap::Command"]

   [[mappings.methods]]
   python = "Command.arg"
   rust_code = "{self}.arg({arg0})"

   [[mappings.types]]
   python = "Command"
   rust = "clap::Command"

   [[mappings.types]]
   python = "ArgMatches"
   rust = "clap::ArgMatches"

Advanced Topics
---------------

Re-exports
^^^^^^^^^^

Many Rust crates re-export types from other crates. cookcrab handles this automatically:

.. code-block:: bash

   $ cookcrab generate clap -o /tmp/stubs
   ...
   Detected re-exports from other crates:
     pub use clap_builder::*

   This crate re-exports from other crates. Will generate stubs for source crates.

   Generating stubs for source crate: clap_builder...

The generated ``spicycrab_clap`` package will depend on ``spicycrab_clap_builder``.

Custom Stub Modifications
^^^^^^^^^^^^^^^^^^^^^^^^^

After generating stubs, you may need to customize them:

1. **Edit __init__.py** - Add missing methods or fix type signatures
2. **Edit _spicycrab.toml** - Add custom mappings or fix Rust code generation

Example: Adding a custom mapping:

.. code-block:: toml

   # In _spicycrab.toml

   [[mappings.functions]]
   python = "clap.crate_name"
   rust_code = "env!(\"CARGO_PKG_NAME\")"
   rust_imports = []

Validating Stubs
^^^^^^^^^^^^^^^^

Always validate your stubs before use:

.. code-block:: bash

   cookcrab validate /tmp/stubs/clap

This checks:

- Required files exist (pyproject.toml, __init__.py, _spicycrab.toml)
- TOML files parse correctly
- Entry points are configured

Contributing Stubs
^^^^^^^^^^^^^^^^^^

To contribute stubs to the official repository:

1. Generate stubs: ``cookcrab generate <crate> -o ./stubs``
2. Review and customize the generated stubs
3. Validate: ``cookcrab validate ./stubs/<crate>``
4. Submit a pull request to `spicycrab-stubs <https://github.com/example/spicycrab-stubs>`_

Troubleshooting
---------------

Stub not discovered
^^^^^^^^^^^^^^^^^^^

If spicycrab doesn't find your stub package:

1. Ensure it's installed: ``pip list | grep spicycrab``
2. Check entry points in pyproject.toml
3. Clear the stub cache:

.. code-block:: python

   from spicycrab.codegen.stub_discovery import clear_stub_cache
   clear_stub_cache()

Type mapping not applied
^^^^^^^^^^^^^^^^^^^^^^^^

If types aren't being converted correctly:

1. Check _spicycrab.toml has the type mapping
2. Verify the Python import matches the stub module name
3. Check for typos in type names

Method not found
^^^^^^^^^^^^^^^^

If a method call isn't being transpiled:

1. Check the method exists in __init__.py
2. Add a method mapping to _spicycrab.toml:

.. code-block:: toml

   [[mappings.methods]]
   python = "TypeName.method_name"
   rust_code = "{self}.method_name({arg0})"

Cargo dependency issues
^^^^^^^^^^^^^^^^^^^^^^^

If the generated Rust code has dependency errors:

1. Check [cargo.dependencies] in _spicycrab.toml
2. Ensure version numbers are correct
3. Add required features:

.. code-block:: toml

   [cargo.dependencies.serde]
   version = "1.0"
   features = ["derive"]
