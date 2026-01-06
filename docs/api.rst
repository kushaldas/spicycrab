Python API
==========

spicycrab can be used programmatically from Python.

Quick Example
-------------

.. code-block:: python

   from spicycrab.parser.python_ast import PythonParser
   from spicycrab.codegen.emitter import RustEmitter

   source = '''
   def add(a: int, b: int) -> int:
       return a + b
   '''

   parser = PythonParser()
   ir = parser.parse(source)

   emitter = RustEmitter()
   rust_code = emitter.emit_module(ir)
   print(rust_code)

Parser Module
-------------

PythonParser
^^^^^^^^^^^^

Parse Python source code into IR.

.. code-block:: python

   from spicycrab.parser.python_ast import PythonParser

   parser = PythonParser()

   # Parse from string
   ir = parser.parse(source_code)

   # Parse from file
   ir = parser.parse_file("path/to/file.py")

TypeParser
^^^^^^^^^^

Parse type annotations.

.. code-block:: python

   from spicycrab.parser.type_parser import TypeParser

   type_parser = TypeParser()

   # Parse a type annotation string
   ir_type = type_parser.parse("list[int]")
   # Returns IRGenericType(name="list", args=[IRType(name="int")])

IR Module
---------

The intermediate representation uses dataclasses.

IRModule
^^^^^^^^

Top-level module containing functions and classes.

.. code-block:: python

   from spicycrab.ir.nodes import IRModule

   module = IRModule(
       name="example",
       functions=[...],
       classes=[...],
       imports=[...]
   )

IRFunction
^^^^^^^^^^

Function definition.

.. code-block:: python

   from spicycrab.ir.nodes import IRFunction, IRType, IRParameter

   func = IRFunction(
       name="add",
       params=[
           IRParameter(name="a", type=IRType(name="int")),
           IRParameter(name="b", type=IRType(name="int")),
       ],
       return_type=IRType(name="int"),
       body=[...]
   )

IRClass
^^^^^^^

Class definition.

.. code-block:: python

   from spicycrab.ir.nodes import IRClass, IRField

   cls = IRClass(
       name="Point",
       fields=[
           IRField(name="x", type=IRType(name="int")),
           IRField(name="y", type=IRType(name="int")),
       ],
       methods=[...],
       is_dataclass=False
   )

Statement Types
^^^^^^^^^^^^^^^

- ``IRAssign`` - Variable assignment
- ``IRReturn`` - Return statement
- ``IRIf`` - If/elif/else
- ``IRFor`` - For loop
- ``IRWhile`` - While loop
- ``IRExprStmt`` - Expression statement
- ``IRRaise`` - Raise exception

Expression Types
^^^^^^^^^^^^^^^^

- ``IRBinOp`` - Binary operation
- ``IRUnaryOp`` - Unary operation
- ``IRCall`` - Function call
- ``IRAttribute`` - Attribute access
- ``IRSubscript`` - Index/subscript
- ``IRName`` - Variable reference
- ``IRConstant`` - Literal value
- ``IRList`` - List literal
- ``IRDict`` - Dict literal

Code Generation
---------------

RustEmitter
^^^^^^^^^^^

Generate Rust code from IR.

.. code-block:: python

   from spicycrab.codegen.emitter import RustEmitter

   emitter = RustEmitter()

   # Emit a module
   rust_code = emitter.emit_module(ir_module)

   # Emit with local module context (for imports)
   rust_code = emitter.emit_module(
       ir_module,
       local_modules={"models", "utils"},
       crate_name="myproject"
   )

CargoGenerator
^^^^^^^^^^^^^^

Generate Cargo.toml.

.. code-block:: python

   from spicycrab.codegen.cargo import CargoGenerator

   cargo = CargoGenerator(name="my_project")

   # Add dependencies based on features used
   cargo.add_serde()  # For JSON support

   # Generate Cargo.toml content
   toml_content = cargo.generate()

Type Resolution
---------------

TypeResolver
^^^^^^^^^^^^

Resolve Python types to Rust types.

.. code-block:: python

   from spicycrab.analyzer.type_resolver import TypeResolver

   resolver = TypeResolver()

   # Resolve a type
   rust_type = resolver.resolve("list[int]")
   # Returns "Vec<i64>"

   rust_type = resolver.resolve("dict[str, float]")
   # Returns "HashMap<String, f64>"

Complete Example
----------------

.. code-block:: python

   from pathlib import Path
   from spicycrab.parser.python_ast import PythonParser
   from spicycrab.codegen.emitter import RustEmitter
   from spicycrab.codegen.cargo import CargoGenerator

   # Parse Python file
   parser = PythonParser()
   ir = parser.parse_file("example.py")

   # Generate Rust code
   emitter = RustEmitter()
   rust_code = emitter.emit_module(ir)

   # Generate Cargo.toml
   cargo = CargoGenerator(name="example")
   cargo_toml = cargo.generate()

   # Write output
   output_dir = Path("output")
   output_dir.mkdir(exist_ok=True)
   (output_dir / "src").mkdir(exist_ok=True)

   (output_dir / "Cargo.toml").write_text(cargo_toml)
   (output_dir / "src" / "main.rs").write_text(rust_code)

spicycrab.types Module
----------------------

Types for writing transpilable Python code.

Result Type
^^^^^^^^^^^

.. code-block:: python

   from spicycrab.types import Result, Ok, Err

   def divide(a: int, b: int) -> Result[int, str]:
       if b == 0:
           return Err("division by zero")
       return Ok(a // b)

Option Type
^^^^^^^^^^^

.. code-block:: python

   from spicycrab.types import Option, Some

   def find(items: list[int], target: int) -> Option[int]:
       for i, item in enumerate(items):
           if item == target:
               return Some(i)
       return None
