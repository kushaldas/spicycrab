Multi-file Projects
===================

spicycrab can transpile entire Python packages with multiple modules.

Directory Structure
-------------------

Input Python project
^^^^^^^^^^^^^^^^^^^^

::

   myproject/
   ├── main.py
   ├── models.py
   └── utils.py

Output Rust project
^^^^^^^^^^^^^^^^^^^

::

   output/
   ├── Cargo.toml
   └── src/
       ├── main.rs
       ├── lib.rs
       ├── models.rs
       └── utils.rs

Transpiling a Directory
-----------------------

.. code-block:: bash

   crabpy transpile ./myproject -o ./output

Example Project
---------------

models.py
^^^^^^^^^

.. code-block:: python

   class User:
       def __init__(self, name: str, age: int) -> None:
           self.name: str = name
           self.age: int = age

       def greet(self) -> str:
           return f"Hello, I'm {self.name}"

utils.py
^^^^^^^^

.. code-block:: python

   def format_age(age: int) -> str:
       return f"{age} years old"

   def is_adult(age: int) -> bool:
       return age >= 18

main.py
^^^^^^^

.. code-block:: python

   from models import User
   from utils import format_age, is_adult

   def main() -> None:
       user: User = User("Alice", 25)
       print(user.greet())
       print(format_age(user.age))
       if is_adult(user.age):
           print("Is an adult")

Generated Rust
--------------

models.rs
^^^^^^^^^

.. code-block:: rust

   pub struct User {
       pub name: String,
       pub age: i64,
   }

   impl User {
       pub fn new(name: String, age: i64) -> Self {
           Self { name, age }
       }

       pub fn greet(&self) -> String {
           format!("Hello, I'm {}", self.name)
       }
   }

utils.rs
^^^^^^^^

.. code-block:: rust

   pub fn format_age(age: i64) -> String {
       format!("{} years old", age)
   }

   pub fn is_adult(age: i64) -> bool {
       age >= 18
   }

main.rs
^^^^^^^

.. code-block:: rust

   use myproject::models::User;
   use myproject::utils::{format_age, is_adult};

   pub fn main() {
       let user: User = User::new("Alice".to_string(), 25);
       println!("{}", user.greet());
       println!("{}", format_age(user.age));
       if is_adult(user.age) {
           println!("Is an adult");
       }
   }

lib.rs
^^^^^^

.. code-block:: rust

   pub mod models;
   pub mod utils;

Import Resolution
-----------------

spicycrab automatically resolves imports between local modules.

Basic import
^^^^^^^^^^^^

.. code-block:: python

   from models import User

.. code-block:: rust

   use crate::models::User;  // In lib code
   use myproject::models::User;  // In main.rs

Multiple imports
^^^^^^^^^^^^^^^^

.. code-block:: python

   from utils import format_age, is_adult

.. code-block:: rust

   use crate::utils::{format_age, is_adult};

Import with alias
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from utils import format_age as fmt

.. code-block:: rust

   use crate::utils::format_age as fmt;

Naming Conventions
------------------

spicycrab uses Python naming conventions to determine what's a class vs function:

- **Uppercase names** (``User``, ``Config``) → treated as structs
- **Lowercase names** (``format_age``, ``is_adult``) → treated as functions

Building the Project
--------------------

After transpilation:

.. code-block:: bash

   cd output
   cargo build
   cargo run

Package Name
------------

The package name in Cargo.toml is derived from the directory name:

.. code-block:: bash

   crabpy transpile ./my_project -o ./output

Creates:

.. code-block:: toml

   [package]
   name = "my_project"
