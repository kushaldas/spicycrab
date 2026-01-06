Standard Library
================

spicycrab maps common Python standard library modules to Rust equivalents.

os and pathlib
--------------

Path creation
^^^^^^^^^^^^^

.. code-block:: python

   from pathlib import Path

   def get_path() -> Path:
       return Path("/home/user")

.. code-block:: rust

   pub fn get_path() -> PathBuf {
       PathBuf::from("/home/user")
   }

Path joining
^^^^^^^^^^^^

.. code-block:: python

   from pathlib import Path

   def join_paths(base: Path, name: str) -> Path:
       return base / name

.. code-block:: rust

   pub fn join_paths(base: PathBuf, name: String) -> PathBuf {
       base.join(name)
   }

File reading
^^^^^^^^^^^^

.. code-block:: python

   from pathlib import Path

   def read_file(path: Path) -> str:
       return path.read_text()

.. code-block:: rust

   pub fn read_file(path: PathBuf) -> String {
       std::fs::read_to_string(&path).unwrap()
   }

File writing
^^^^^^^^^^^^

.. code-block:: python

   from pathlib import Path

   def write_file(path: Path, content: str) -> None:
       path.write_text(content)

.. code-block:: rust

   pub fn write_file(path: PathBuf, content: String) {
       std::fs::write(&path, content).unwrap();
   }

Path checks
^^^^^^^^^^^

.. code-block:: python

   from pathlib import Path

   def check_path(path: Path) -> bool:
       return path.exists()

   def is_file(path: Path) -> bool:
       return path.is_file()

   def is_dir(path: Path) -> bool:
       return path.is_dir()

.. code-block:: rust

   pub fn check_path(path: PathBuf) -> bool {
       path.exists()
   }

   pub fn is_file(path: PathBuf) -> bool {
       path.is_file()
   }

   pub fn is_dir(path: PathBuf) -> bool {
       path.is_dir()
   }

os.getcwd and os.chdir
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import os

   def current_dir() -> str:
       return os.getcwd()

.. code-block:: rust

   pub fn current_dir() -> String {
       std::env::current_dir().unwrap().to_string_lossy().to_string()
   }

Environment variables
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import os

   def get_home() -> str:
       return os.environ.get("HOME", "")

.. code-block:: rust

   pub fn get_home() -> String {
       std::env::var("HOME").unwrap_or(String::new())
   }

sys
---

Command line arguments
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import sys

   def get_args() -> list[str]:
       return sys.argv

.. code-block:: rust

   pub fn get_args() -> Vec<String> {
       std::env::args().collect()
   }

Platform detection
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import sys

   def get_platform() -> str:
       return sys.platform

.. code-block:: rust

   pub fn get_platform() -> String {
       std::env::consts::OS.to_string()
   }

Process exit
^^^^^^^^^^^^

.. code-block:: python

   import sys

   def quit_program() -> None:
       sys.exit(0)

.. code-block:: rust

   pub fn quit_program() {
       std::process::exit(0);
   }

json
----

Parsing JSON
^^^^^^^^^^^^

.. code-block:: python

   import json

   def parse_json(text: str) -> dict[str, str]:
       return json.loads(text)

.. code-block:: rust

   pub fn parse_json(text: String) -> HashMap<String, String> {
       serde_json::from_str(&text).unwrap()
   }

Serializing JSON
^^^^^^^^^^^^^^^^

.. code-block:: python

   import json

   def to_json(data: dict[str, int]) -> str:
       return json.dumps(data)

.. code-block:: rust

   pub fn to_json(data: HashMap<String, i64>) -> String {
       serde_json::to_string(&data).unwrap()
   }

collections
-----------

Using list as Vec
^^^^^^^^^^^^^^^^^

.. code-block:: python

   def create_list() -> list[int]:
       items: list[int] = []
       items.append(1)
       items.append(2)
       items.append(3)
       return items

.. code-block:: rust

   pub fn create_list() -> Vec<i64> {
       let mut items: Vec<i64> = vec![];
       items.push(1);
       items.push(2);
       items.push(3);
       items
   }

Using dict as HashMap
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def create_dict() -> dict[str, int]:
       ages: dict[str, int] = {}
       ages["Alice"] = 30
       ages["Bob"] = 25
       return ages

.. code-block:: rust

   pub fn create_dict() -> HashMap<String, i64> {
       let mut ages: HashMap<String, i64> = HashMap::new();
       ages.insert("Alice".to_string(), 30);
       ages.insert("Bob".to_string(), 25);
       ages
   }

Using set as HashSet
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   def create_set() -> set[int]:
       numbers: set[int] = set()
       numbers.add(1)
       numbers.add(2)
       numbers.add(1)  # Duplicate
       return numbers

.. code-block:: rust

   pub fn create_set() -> HashSet<i64> {
       let mut numbers: HashSet<i64> = HashSet::new();
       numbers.insert(1);
       numbers.insert(2);
       numbers.insert(1);
       numbers
   }

time
----

Current time
^^^^^^^^^^^^

.. code-block:: python

   import time

   def get_timestamp() -> float:
       return time.time()

.. code-block:: rust

   pub fn get_timestamp() -> f64 {
       std::time::SystemTime::now()
           .duration_since(std::time::UNIX_EPOCH)
           .unwrap()
           .as_secs_f64()
   }

Sleep
^^^^^

.. code-block:: python

   import time

   def wait(seconds: float) -> None:
       time.sleep(seconds)

.. code-block:: rust

   pub fn wait(seconds: f64) {
       std::thread::sleep(std::time::Duration::from_secs_f64(seconds));
   }

datetime
--------

Current local time
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import datetime

   def now():
       return datetime.datetime.now()

.. code-block:: rust

   // Uses chrono crate
   pub fn now() -> chrono::DateTime<chrono::Local> {
       chrono::Local::now()
   }

Current UTC time
^^^^^^^^^^^^^^^^

.. code-block:: python

   import datetime

   def utc_now():
       return datetime.datetime.utcnow()

.. code-block:: rust

   pub fn utc_now() -> chrono::DateTime<chrono::Utc> {
       chrono::Utc::now()
   }

Today's date
^^^^^^^^^^^^

.. code-block:: python

   import datetime

   def today():
       return datetime.date.today()

.. code-block:: rust

   pub fn today() -> chrono::NaiveDate {
       chrono::Local::now().date_naive()
   }

Generated Dependencies
----------------------

When using stdlib features, spicycrab adds appropriate dependencies to Cargo.toml:

.. code-block:: toml

   [dependencies]
   serde = { version = "1.0", features = ["derive"] }
   serde_json = "1.0"
   chrono = "0.4"  # Added when using datetime module

Standard imports are also added:

.. code-block:: rust

   use std::collections::{HashMap, HashSet};
   use std::path::PathBuf;
