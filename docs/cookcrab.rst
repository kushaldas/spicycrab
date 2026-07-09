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

1. Install stubs: ``cookcrab install <crate_name>``
2. Write Python code using the stub types
3. Transpile: ``crabpy transpile mycode.py``

Or generate your own stubs:

1. Generate stubs: ``cookcrab generate <crate_name> -o /tmp/stubs``
2. Install the generated stub package from the local output directory
3. Write Python code using the stub types
4. Transpile: ``crabpy transpile mycode.py``

Cargo dependency emission
-------------------------

Each stub package can define Cargo dependencies in its ``_spicycrab.toml``:

.. code-block:: toml

   [cargo.dependencies]
   tunnelbana-core = { path = "/home/me/code/tunnelbana/crates/tunnelbana-core" }
   async-trait = "0.1"

When generating ``Cargo.toml``, spicycrab includes dependencies only for stub
packages imported by the Python input. If several stub packages are installed,
unused stubs do not add unused Cargo dependencies to the generated project.

Table dependency specs are preserved, so hand-written stubs can use local
``path`` dependencies, ``default-features = false``, explicit ``features``, or
other standard Cargo dependency fields. User feature overrides from
``[tool.spicycrab.features]`` in ``pyproject.toml`` or ``[features]`` in
``spicycrab.toml`` are still merged into the selected stub dependencies.

.. warning::

   Use ``cookcrab install`` for stubs from the official repository.
   Use local editable installs only for stubs you have just generated with
   ``cookcrab generate``.

Installation
------------

cookcrab is included with spicycrab:

.. code-block:: bash

   python3 -m pip install spicycrab

   # Verify installation
   cookcrab --help

Commands
--------

install (recommended)
^^^^^^^^^^^^^^^^^^^^^

Install a stub package from the `spicycrab-stubs <https://github.com/kushaldas/spicycrab-stubs>`_ repository.
This is the recommended way to get stubs for common crates.

**Basic usage:**

.. code-block:: bash

   # Install from official stubs repository
   cookcrab install anyhow
   cookcrab install tokio
   cookcrab install clap

**Install a specific version:**

.. code-block:: bash

   cookcrab install tokio -v 1.52.3
   cookcrab install anyhow -v 1.0.103

**Install from a custom repository:**

.. code-block:: bash

   # Install from a local or custom git repository with stubs/<crate> layout
   cookcrab install mycrate --repo /path/to/my-stubs
   cookcrab install mycrate --repo https://github.com/user/custom-stubs.git

The ``--repo`` option is for a stubs repository, not the raw output directory
from ``cookcrab generate``. For raw generated output, install the generated
package path with ``python3 -m pip install -e``.

**What happens during install:**

1. Sparse checkout of the stub from the repository
2. Build a wheel locally
3. Install using uv pip (or pip if uv not available)

.. warning::

   For stubs from the official repository, use ``cookcrab install`` rather than
   installing packages directly. This ensures:

   - Stubs come from the trusted spicycrab-stubs repository
   - Proper wheel building and installation
   - Compatibility with spicycrab's stub discovery system

**Available stubs:**

The official repository includes stubs for:

- ``actix-web`` and ``actix-web-lab`` - Web services
- ``anyhow`` - Error handling
- ``base64`` - Base64 encoding and decoding
- ``chrono`` - Date and time handling
- ``clap`` and ``clap_builder`` - Command line argument parsing
- ``config`` - Configuration loading
- ``env_logger``, ``fern``, and ``log`` - Logging
- ``grindvakt`` - Shared HTTP, key, MAC, and PKCE primitives
- ``josekit`` - JOSE/JWT/JWE/JWS operations
- ``lazy_static`` - Lazy static initialization
- ``native-tls``, ``rustls``, and ``rustls-pemfile`` - TLS support
- ``oidfed_metadata_policy`` - OpenID federation metadata policy
- ``redis`` - Redis client
- ``reqwest`` and ``ureq`` - HTTP clients
- ``serde`` and ``serde_json`` - Serialization
- ``sha2`` - SHA-2 hashing
- ``tokio`` - Async runtime (spawn, sleep, channels)
- ``toml`` - TOML parsing
- ``tunnelbana-core`` and ``tunnelbana-plugins`` - Tunnelbana plugin APIs

Check for available stubs:

.. code-block:: bash

   cookcrab search <pattern>

search
^^^^^^

Search for available stub packages.

.. code-block:: bash

   cookcrab search clap
   cookcrab search serde

generate
^^^^^^^^

Generate Python stubs from a Rust crate. Use this when a stub isn't available
in the official repository.

**From crates.io (recommended):**

.. code-block:: bash

   # Generate stubs for the latest version
   cookcrab generate clap -o /tmp/stubs

   # Generate stubs for a specific version
   cookcrab generate clap -v 4.6.1 -o /tmp/stubs

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

**After generating, install with:**

.. code-block:: bash

   python3 -m pip install -e /tmp/stubs/clap_builder
   python3 -m pip install -e /tmp/stubs/clap

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

Quick Start Examples
--------------------

Example 1: Using anyhow for error handling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install the anyhow stubs:

.. code-block:: bash

   cookcrab install anyhow

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

Example 2: Using clap for CLI argument parsing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install the clap stubs (automatically installs clap_builder dependency):

.. code-block:: bash

   cookcrab install clap

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

Example 3: Using tokio for async programming
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install the tokio stubs:

.. code-block:: bash

   cookcrab install tokio

Write async code:

.. code-block:: python

   from spicycrab_tokio import spawn, sleep, Duration
   from spicycrab.types import Result

   async def do_work(task_id: int) -> int:
       """Simulate async work."""
       print(f"Task {task_id} starting...")
       await sleep(Duration.from_millis(100))
       print(f"Task {task_id} finished!")
       return task_id * 10

   async def main() -> None:
       # Spawn concurrent tasks
       handle1 = spawn(do_work(1))
       handle2 = spawn(do_work(2))

       # Wait for results
       result1: int = Result.unwrap(await handle1)
       result2: int = Result.unwrap(await handle2)

       print(f"Results: {result1}, {result2}")

Transpile and run:

.. code-block:: bash

   crabpy transpile async_example.py -o rust_async -n async_example
   cd rust_async
   cargo build --release
   ./target/release/async_example

Generated Rust code uses tokio with ``#[tokio::main]``:

.. code-block:: rust

   #[tokio::main]
   async fn main() {
       let handle1 = tokio::spawn(do_work(1));
       let handle2 = tokio::spawn(do_work(2));
       let result1: i64 = handle1.await.unwrap();
       let result2: i64 = handle2.await.unwrap();
       println!("{}", format!("Results: {}, {}", result1, result2));
   }

For more async examples, see the :doc:`async` chapter.

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
   version = "4.6.1"
   dependencies = ["spicycrab-clap_builder"]

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
   rust_version = "4.6.1"
   python_module = "spicycrab_clap"

   [cargo.dependencies.clap]
   version = "4.6.1"
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
Mappings in the re-exporting package are rewritten to use the public crate path:
function mappings, method imports, and type mappings all refer to ``clap::...``
rather than leaking ``clap_builder::...`` into generated user code.

Method Mapping Resolution
^^^^^^^^^^^^^^^^^^^^^^^^^

Method mappings are scoped by the stub crate inferred from imports and receiver
types. This matters when multiple crates expose the same Rust type name. For
example, both ``reqwest`` and ``ureq`` expose a ``RequestBuilder``, but
``reqwest::RequestBuilder::send`` takes no body argument while
``ureq::RequestBuilder::send`` can take a body.

Use explicit imports and type annotations when the receiver type cannot be
inferred from the surrounding expression:

.. code-block:: python

   from spicycrab_reqwest import Client, Response

   async def fetch(url: str) -> str:
       client: Client = Client.new()
       response: Response = await client.get(url).send()
       return await response.text()

The ``Client`` annotation tells spicycrab to resolve the chained
``RequestBuilder.send`` mapping from the ``reqwest`` stub package.

Custom Stub Modifications
^^^^^^^^^^^^^^^^^^^^^^^^^

After generating stubs, you may need to customize them:

1. **Edit __init__.py** - Add missing methods or fix type signatures
2. **Edit _spicycrab.toml** - Add custom mappings or fix Rust code generation

When a generated stub needs a repeatable package-specific fix, prefer fixing
``cookcrab`` itself and adding a generator regression test. Keep hand-written
stub edits for APIs that cannot be represented accurately by the generator.

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

``cookcrab validate`` accepts one stub package path at a time. To validate a
repository of generated stubs:

.. code-block:: bash

   for stub in ./stubs/*; do
       [ -d "$stub" ] && cookcrab validate "$stub"
   done

This checks:

- Required files exist (pyproject.toml, __init__.py, _spicycrab.toml)
- TOML files parse correctly
- Entry points are configured

Contributing Stubs
^^^^^^^^^^^^^^^^^^

To contribute stubs to the official repository:

1. Fork the `spicycrab-stubs <https://github.com/kushaldas/spicycrab-stubs>`_ repository
2. Generate stubs: ``cookcrab generate <crate> -o ./stubs``
3. Review the generated stubs and fix generator gaps where possible
4. Validate: ``cookcrab validate ./stubs/<crate>``
5. Test: ``cookcrab install <crate> --repo ./`` and run examples
6. Transpile the examples, run ``cargo check``, and run ``cargo build``
7. Submit a pull request

Crate Features
--------------

Rust crates often have optional features that enable additional functionality.
spicycrab supports specifying which features to enable for each crate.

How Features Work
^^^^^^^^^^^^^^^^^

1. **cookcrab** extracts available features when generating stubs
2. **spicycrab** reads your project config to determine which features to enable
3. The generated ``Cargo.toml`` includes the specified features

Feature Information in Stubs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When cookcrab generates stubs, it extracts feature information from the crate's
``Cargo.toml`` and stores it in ``_spicycrab.toml``:

.. code-block:: toml

   # _spicycrab.toml (generated by cookcrab)
   [cargo.features]
   available = ["blocking", "json", "cookies", "gzip", "rustls-tls", "native-tls"]
   default = ["charset", "default-tls", "http2", "system-proxy"]

- **available**: All features the crate provides
- **default**: Features enabled by default (when no features specified)

Specifying Features
^^^^^^^^^^^^^^^^^^^

You can specify which features to enable in your project configuration.
spicycrab looks for configuration in two places (in order):

**Option 1: pyproject.toml**

.. code-block:: toml

   # pyproject.toml
   [tool.spicycrab.features]
   reqwest = ["blocking", "json"]
   tokio = ["full"]
   serde = ["derive"]

**Option 2: spicycrab.toml**

.. code-block:: toml

   # spicycrab.toml
   [features]
   reqwest = ["blocking", "json"]
   tokio = ["full"]
   serde = ["derive"]

Feature Behavior
^^^^^^^^^^^^^^^^

- **User config present**: Uses the features you specified
- **No config**: Uses the crate's default features
- **Empty list ``[]``**: Disables all features (including defaults)

Example: Using reqwest with blocking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Generate and install reqwest stubs:

.. code-block:: bash

   cookcrab generate reqwest -o /tmp/stubs
   python3 -m pip install -e /tmp/stubs/reqwest

2. Create your Python code:

.. code-block:: python

   # myapp.py
   from spicycrab_reqwest import blocking

   def main() -> None:
       response = blocking.get("https://httpbin.org/get")
       print(response.text())

3. Configure features in your project:

.. code-block:: toml

   # pyproject.toml (in the same directory as myapp.py)
   [tool.spicycrab.features]
   reqwest = ["blocking"]

4. Transpile:

.. code-block:: bash

   crabpy transpile myapp.py -o rust_myapp

5. The generated ``Cargo.toml`` will include:

.. code-block:: toml

   [dependencies]
   reqwest = { version = "0.13.4", features = ["blocking"] }

Disabling Default Features
^^^^^^^^^^^^^^^^^^^^^^^^^^

To use a crate without its default features, specify an empty list:

.. code-block:: toml

   # pyproject.toml
   [tool.spicycrab.features]
   reqwest = []  # No features, not even defaults

Or specify only the features you need:

.. code-block:: toml

   # pyproject.toml
   [tool.spicycrab.features]
   reqwest = ["rustls-tls"]  # Only rustls-tls, no default features

Viewing Available Features
^^^^^^^^^^^^^^^^^^^^^^^^^^

To see what features a crate provides, check the generated ``_spicycrab.toml``:

.. code-block:: bash

   # After generating stubs
   cat /tmp/stubs/reqwest/spicycrab_reqwest/_spicycrab.toml | grep -A2 "cargo.features"

Or check the crate's documentation on `crates.io <https://crates.io>`_ or `docs.rs <https://docs.rs>`_.

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

Wrong method mapping selected
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If generated Rust uses a mapping from the wrong crate, check for shared type
names across installed stub packages. The most common shape is a builder type
such as ``RequestBuilder`` that exists in more than one HTTP client crate.

1. Import the type from the intended stub module.
2. Add a type annotation for variables used in method chains.
3. Make sure the stub package has a ``[[mappings.types]]`` entry for that type.

.. code-block:: python

   from spicycrab_reqwest import Client, Response

   async def fetch(url: str) -> str:
       client: Client = Client.new()
       response: Response = await client.get(url).send()
       return await response.text()

Here, the ``Client`` annotation lets spicycrab keep the chain scoped to the
``reqwest`` stub package, so ``send()`` is emitted with the reqwest signature.

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
