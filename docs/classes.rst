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
