Classes
=======

Basic Classes
-------------

Simple class
^^^^^^^^^^^^

.. code-block:: python

   class Point:
       def __init__(self, x: int, y: int) -> None:
           self.x: int = x
           self.y: int = y

.. code-block:: rust

   pub struct Point {
       pub x: i64,
       pub y: i64,
   }

   impl Point {
       pub fn new(x: i64, y: i64) -> Self {
           Self { x, y }
       }
   }

Methods
-------

Instance methods
^^^^^^^^^^^^^^^^

.. code-block:: python

   class Counter:
       def __init__(self, value: int) -> None:
           self.value: int = value

       def increment(self) -> None:
           self.value = self.value + 1

       def get(self) -> int:
           return self.value

.. code-block:: rust

   pub struct Counter {
       pub value: i64,
   }

   impl Counter {
       pub fn new(value: i64) -> Self {
           Self { value }
       }

       pub fn increment(&mut self) {
           self.value = self.value + 1;
       }

       pub fn get(&self) -> i64 {
           self.value
       }
   }

Method with parameters
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   class Calculator:
       def __init__(self, value: int) -> None:
           self.value: int = value

       def add(self, n: int) -> int:
           return self.value + n

       def multiply(self, n: int) -> int:
           return self.value * n

.. code-block:: rust

   pub struct Calculator {
       pub value: i64,
   }

   impl Calculator {
       pub fn new(value: i64) -> Self {
           Self { value }
       }

       pub fn add(&self, n: i64) -> i64 {
           self.value + n
       }

       pub fn multiply(&self, n: i64) -> i64 {
           self.value * n
       }
   }

Dataclasses
-----------

Basic dataclass
^^^^^^^^^^^^^^^

.. code-block:: python

   from dataclasses import dataclass

   @dataclass
   class User:
       name: str
       age: int

.. code-block:: rust

   #[derive(Clone, Debug)]
   pub struct User {
       pub name: String,
       pub age: i64,
   }

   impl User {
       pub fn new(name: String, age: i64) -> Self {
           Self { name, age }
       }
   }

Dataclass with defaults
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from dataclasses import dataclass

   @dataclass
   class Config:
       host: str = "localhost"
       port: int = 8080

.. code-block:: rust

   #[derive(Clone, Debug)]
   pub struct Config {
       pub host: String,
       pub port: i64,
   }

   impl Config {
       pub fn new(host: Option<String>, port: Option<i64>) -> Self {
           Self {
               host: host.unwrap_or("localhost".to_string()),
               port: port.unwrap_or(8080),
           }
       }
   }

Using Classes
-------------

Creating instances
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def main() -> None:
       p: Point = Point(10, 20)
       print(p.x)

.. code-block:: rust

   pub fn main() {
       let p: Point = Point::new(10, 20);
       println!("{}", p.x);
   }

Calling methods
^^^^^^^^^^^^^^^

.. code-block:: python

   def main() -> None:
       c: Counter = Counter(0)
       c.increment()
       c.increment()
       print(c.get())

.. code-block:: rust

   pub fn main() {
       let mut c: Counter = Counter::new(0);
       c.increment();
       c.increment();
       println!("{}", c.get());
   }

Class with Collections
----------------------

.. code-block:: python

   class Stack:
       def __init__(self) -> None:
           self.items: list[int] = []

       def push(self, item: int) -> None:
           self.items.append(item)

       def pop(self) -> int:
           return self.items.pop()

       def is_empty(self) -> bool:
           return len(self.items) == 0

.. code-block:: rust

   pub struct Stack {
       pub items: Vec<i64>,
   }

   impl Stack {
       pub fn new() -> Self {
           Self { items: vec![] }
       }

       pub fn push(&mut self, item: i64) {
           self.items.push(item);
       }

       pub fn pop(&mut self) -> i64 {
           self.items.pop().unwrap()
       }

       pub fn is_empty(&self) -> bool {
           self.items.len() == 0
       }
   }

Passthrough Rust Attributes
---------------------------

spicycrab supports **passthrough Rust attributes** via special comments.
Comments starting with ``# #[`` are recognized as Rust attributes and
emitted verbatim in the generated code.

This allows you to add Rust-specific attributes like ``#[derive(...)]``,
``#[serde(...)]``, ``#[inline]``, or framework-specific attributes like
``#[get(...)]`` for actix-web.

Basic syntax
^^^^^^^^^^^^

.. code-block:: python

   # #[derive(Serialize, Deserialize)]
   # #[serde(rename_all = "camelCase")]
   @dataclass
   class EntityDetails:
       entity_id: str
       entity_type: str
       has_trustmark: bool

.. code-block:: rust

   #[derive(Serialize, Deserialize)]
   #[serde(rename_all = "camelCase")]
   pub struct EntityDetails {
       pub entity_id: String,
       pub entity_type: String,
       pub has_trustmark: bool,
   }

Function attributes
^^^^^^^^^^^^^^^^^^^

Attributes can also be applied to functions:

.. code-block:: python

   # #[inline]
   def fast_function(x: int) -> int:
       return x * 2

   # #[get("/.well-known/openid-federation")]
   async def openid_federation() -> str:
       return "entity-statement-jwt"

.. code-block:: rust

   #[inline]
   pub fn fast_function(x: i64) -> i64 {
       x * 2
   }

   #[get("/.well-known/openid-federation")]
   pub async fn openid_federation() -> String {
       "entity-statement-jwt".to_string()
   }

Test attributes
^^^^^^^^^^^^^^^

Use passthrough attributes for test functions:

.. code-block:: python

   # #[tokio::test]
   async def test_something() -> None:
       result: int = add(1, 2)
       assert result == 3

.. code-block:: rust

   #[tokio::test]
   pub async fn test_something() {
       let result: i64 = add(1, 2);
       assert_eq!(result, 3);
   }

Multiple attributes
^^^^^^^^^^^^^^^^^^^

Stack multiple attributes on consecutive lines:

.. code-block:: python

   # #[derive(Serialize, Deserialize, Debug, Clone)]
   # #[serde(rename_all = "camelCase")]
   # #[serde(deny_unknown_fields)]
   @dataclass
   class ApiResponse:
       status_code: int
       message: str

.. code-block:: rust

   #[derive(Serialize, Deserialize, Debug, Clone)]
   #[serde(rename_all = "camelCase")]
   #[serde(deny_unknown_fields)]
   pub struct ApiResponse {
       pub status_code: i64,
       pub message: String,
   }

Rules
^^^^^

1. Comments must start with ``# #[`` (space after ``#`` is required)
2. Multiple attributes can be stacked on consecutive lines
3. Attributes are extracted from lines immediately preceding the function/class
4. Python decorators (``@dataclass``, ``@staticmethod``, etc.) are skipped when looking for attributes
5. If a ``#[derive(...)]`` is provided via passthrough, the default ``#[derive(Debug, Clone)]`` is not added
6. For ``async def main()``, if a ``#[...::main]`` attribute is provided, auto-generation of ``#[tokio::main]`` is skipped
