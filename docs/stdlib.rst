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

The ``datetime`` module is mapped to Rust's `chrono <https://docs.rs/chrono>`_ crate.

.. note::

   Python's ``time`` module (e.g., ``time.time()``, ``time.sleep()``) maps to
   ``std::time``, while the ``datetime`` module uses the ``chrono`` crate.
   This allows you to use both modules in the same project without conflicts.

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

From timestamp
^^^^^^^^^^^^^^

.. code-block:: python

   import datetime

   def from_ts(ts: float):
       return datetime.datetime.fromtimestamp(ts)

.. code-block:: rust

   pub fn from_ts(ts: f64) -> chrono::DateTime<chrono::Local> {
       chrono::Local.timestamp_opt(ts as i64, ((ts.fract()) * 1_000_000_000.0) as u32).unwrap()
   }

timedelta
^^^^^^^^^

The ``datetime.timedelta`` class maps to ``chrono::Duration``:

.. code-block:: python

   import datetime

   def get_duration():
       return datetime.timedelta(days=1, hours=2, minutes=30)

.. code-block:: rust

   pub fn get_duration() -> chrono::Duration {
       chrono::Duration::days(1) + chrono::Duration::hours(2) + chrono::Duration::minutes(30)
   }

Supported datetime class methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following ``datetime`` module class methods are supported:

+------------------------------------+--------------------------------------------+
| Python                             | Rust                                       |
+====================================+============================================+
| ``datetime.datetime.now()``        | ``chrono::Local::now()``                   |
+------------------------------------+--------------------------------------------+
| ``datetime.datetime.utcnow()``     | ``chrono::Utc::now()``                     |
+------------------------------------+--------------------------------------------+
| ``datetime.datetime.fromtimestamp``| ``chrono::Local.timestamp_opt(...)``       |
+------------------------------------+--------------------------------------------+
| ``datetime.date.today()``          | ``chrono::Local::now().date_naive()``      |
+------------------------------------+--------------------------------------------+
| ``datetime.timedelta(...)``        | ``chrono::Duration::...()``                |
+------------------------------------+--------------------------------------------+

Instance Methods with Type Annotations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Instance methods like ``dt.year``, ``dt.month``, ``dt.isoformat()`` are
supported when **explicit type annotations** are provided.

**Example with type annotations:**

.. code-block:: python

   import datetime

   def get_year() -> int:
       # Type annotation enables instance method resolution
       dt: datetime.datetime = datetime.datetime.now()
       return dt.year  # ✅ Works: transpiles to dt.year() as i64

.. code-block:: rust

   pub fn get_year() -> i64 {
       let dt: chrono::DateTime<chrono::Local> = chrono::Local::now();
       dt.year() as i64
   }

**Without type annotations (not recommended):**

.. code-block:: python

   import datetime

   def get_year() -> int:
       dt = datetime.datetime.now()  # No type annotation
       return dt.year  # ❌ Not transpiled correctly

   # The transpiler doesn't know that `dt` is a datetime object,
   # so it cannot apply the correct Rust mapping.

**Supported instance methods:**

+----------------------------+----------------------------------------+
| Python                     | Rust                                   |
+============================+========================================+
| ``dt.year``                | ``dt.year() as i64``                   |
+----------------------------+----------------------------------------+
| ``dt.month``               | ``dt.month() as i64``                  |
+----------------------------+----------------------------------------+
| ``dt.day``                 | ``dt.day() as i64``                    |
+----------------------------+----------------------------------------+
| ``dt.hour``                | ``dt.hour() as i64``                   |
+----------------------------+----------------------------------------+
| ``dt.minute``              | ``dt.minute() as i64``                 |
+----------------------------+----------------------------------------+
| ``dt.second``              | ``dt.second() as i64``                 |
+----------------------------+----------------------------------------+
| ``dt.weekday()``           | ``dt.weekday().num_days_from_monday()``|
+----------------------------+----------------------------------------+
| ``dt.isoformat()``         | ``dt.format(...).to_string()``         |
+----------------------------+----------------------------------------+

**Best practice:** Always use explicit type annotations for datetime variables
to ensure correct transpilation of instance methods.

glob
----

The ``glob`` module is mapped to Rust's `glob <https://docs.rs/glob>`_ crate.

glob.glob()
^^^^^^^^^^^

.. code-block:: python

   import glob

   def find_configs() -> list[str]:
       return glob.glob("*.toml")

.. code-block:: rust

   pub fn find_configs() -> Vec<String> {
       glob::glob(&"*.toml".to_string())
           .unwrap()
           .filter_map(|p| p.ok())
           .map(|p| p.to_string_lossy().to_string())
           .collect::<Vec<_>>()
   }

glob.escape()
^^^^^^^^^^^^^

.. code-block:: python

   import glob

   def escape_pattern(pattern: str) -> str:
       return glob.escape(pattern)

.. code-block:: rust

   pub fn escape_pattern(pattern: String) -> String {
       pattern
           .replace("[", "[[]")
           .replace("]", "[]]")
           .replace("*", "[*]")
           .replace("?", "[?]")
   }

Supported glob functions
^^^^^^^^^^^^^^^^^^^^^^^^

+----------------------+-----------------------------------------------+
| Python               | Rust                                          |
+======================+===============================================+
| ``glob.glob(pat)``   | ``glob::glob(...).filter_map(...).collect()`` |
+----------------------+-----------------------------------------------+
| ``glob.iglob(pat)``  | Same as glob.glob (collected to Vec)          |
+----------------------+-----------------------------------------------+
| ``glob.escape(s)``   | String replacement for ``[ ] * ?``            |
+----------------------+-----------------------------------------------+

tempfile
--------

The ``tempfile`` module is mapped to Rust's `tempfile <https://docs.rs/tempfile>`_ crate.

tempfile.gettempdir()
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import tempfile

   def get_temp() -> str:
       return tempfile.gettempdir()

.. code-block:: rust

   pub fn get_temp() -> String {
       std::env::temp_dir().to_string_lossy().to_string()
   }

tempfile.mkdtemp()
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import tempfile

   def make_temp_dir() -> str:
       return tempfile.mkdtemp()

.. code-block:: rust

   pub fn make_temp_dir() -> String {
       let d = tempfile::tempdir().unwrap();
       let p = d.path().to_string_lossy().to_string();
       let _ = d.keep();  // Persist the directory
       p
   }

tempfile.TemporaryDirectory()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import tempfile

   def use_temp_dir() -> None:
       tmpdir = tempfile.TemporaryDirectory()
       # Directory is cleaned up when tmpdir goes out of scope

.. code-block:: rust

   pub fn use_temp_dir() {
       let tmpdir = tempfile::tempdir().unwrap();
       // Directory is cleaned up when tmpdir is dropped
   }

Context manager support
^^^^^^^^^^^^^^^^^^^^^^^

The ``with`` statement works correctly with tempfile:

.. code-block:: python

   import tempfile

   def use_temp_dir() -> None:
       with tempfile.TemporaryDirectory() as tmpdir:
           # tmpdir is the path (string), not the directory object
           print(tmpdir)
       # Directory is automatically cleaned up here

.. code-block:: rust

   pub fn use_temp_dir() {
       {
           let _temp_ctx = tempfile::tempdir().unwrap();
           let tmpdir = _temp_ctx.path().to_string_lossy().to_string();
           println!("{}", tmpdir);
       } // _temp_ctx dropped here, directory cleaned up
   }

Supported tempfile functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+--------------------------------+----------------------------------------------+
| Python                         | Rust                                         |
+================================+==============================================+
| ``tempfile.gettempdir()``      | ``std::env::temp_dir()``                     |
+--------------------------------+----------------------------------------------+
| ``tempfile.mkdtemp()``         | ``tempfile::tempdir()`` with ``keep()``      |
+--------------------------------+----------------------------------------------+
| ``tempfile.TemporaryDirectory``| ``tempfile::tempdir()``                      |
+--------------------------------+----------------------------------------------+
| ``tempfile.NamedTemporaryFile``| ``tempfile::NamedTempFile::new()``           |
+--------------------------------+----------------------------------------------+

subprocess
----------

The ``subprocess`` module is mapped to Rust's ``std::process``.

subprocess.call()
^^^^^^^^^^^^^^^^^

.. code-block:: python

   import subprocess

   def run_command() -> int:
       args: list[str] = ["-l"]
       return subprocess.call("ls", args)

.. code-block:: rust

   pub fn run_command() -> i64 {
       std::process::Command::new("ls")
           .args(&args)
           .status()
           .unwrap()
           .code()
           .unwrap_or(-1) as i64
   }

subprocess.check_output()
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import subprocess

   def get_output() -> str:
       args: list[str] = ["hello"]
       return subprocess.check_output("echo", args)

.. code-block:: rust

   pub fn get_output() -> String {
       String::from_utf8_lossy(
           &std::process::Command::new("echo")
               .args(&args)
               .output()
               .unwrap()
               .stdout
       ).to_string()
   }

subprocess.getoutput()
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import subprocess

   def shell_output() -> str:
       return subprocess.getoutput("echo hello")

.. code-block:: rust

   pub fn shell_output() -> String {
       String::from_utf8_lossy(
           &std::process::Command::new("sh")
               .arg("-c")
               .arg("echo hello")
               .output()
               .unwrap()
               .stdout
       ).to_string()
   }

Supported subprocess functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+----------------------------------+------------------------------------------------+
| Python                           | Rust                                           |
+==================================+================================================+
| ``subprocess.run(cmd, args)``    | ``Command::new(cmd).args(args).status()``      |
+----------------------------------+------------------------------------------------+
| ``subprocess.call(cmd, args)``   | ``Command::new(cmd).args(args).status()``      |
+----------------------------------+------------------------------------------------+
| ``subprocess.check_call(...)``   | Same, but panics on non-zero exit              |
+----------------------------------+------------------------------------------------+
| ``subprocess.check_output(...)`` | ``Command::new(...).output().stdout``          |
+----------------------------------+------------------------------------------------+
| ``subprocess.getoutput(cmd)``    | ``Command::new("sh").arg("-c").arg(cmd)``      |
+----------------------------------+------------------------------------------------+
| ``subprocess.getstatusoutput()`` | Returns ``(exit_code, output)`` tuple          |
+----------------------------------+------------------------------------------------+

shutil
------

The ``shutil`` module is mapped to Rust's ``std::fs`` and the ``which`` crate.

shutil.copy()
^^^^^^^^^^^^^

.. code-block:: python

   import shutil

   def copy_file(src: str, dst: str) -> None:
       shutil.copy(src, dst)

.. code-block:: rust

   pub fn copy_file(src: String, dst: String) {
       std::fs::copy(&src, &dst).unwrap();
   }

shutil.rmtree()
^^^^^^^^^^^^^^^

.. code-block:: python

   import shutil

   def remove_dir(path: str) -> None:
       shutil.rmtree(path)

.. code-block:: rust

   pub fn remove_dir(path: String) {
       std::fs::remove_dir_all(&path).unwrap();
   }

shutil.which()
^^^^^^^^^^^^^^

.. code-block:: python

   import shutil

   def find_program(name: str) -> str:
       return shutil.which(name)

.. code-block:: rust

   pub fn find_program(name: String) -> String {
       which::which(name)
           .ok()
           .map(|p| p.to_string_lossy().to_string())
           .unwrap_or_default()
   }

Supported shutil functions
^^^^^^^^^^^^^^^^^^^^^^^^^^

+-----------------------------+------------------------------------------------+
| Python                      | Rust                                           |
+=============================+================================================+
| ``shutil.copy(src, dst)``   | ``std::fs::copy(src, dst)``                    |
+-----------------------------+------------------------------------------------+
| ``shutil.copy2(src, dst)``  | ``std::fs::copy(src, dst)``                    |
+-----------------------------+------------------------------------------------+
| ``shutil.copyfile(...)``    | ``std::fs::copy(...)``                         |
+-----------------------------+------------------------------------------------+
| ``shutil.rmtree(path)``     | ``std::fs::remove_dir_all(path)``              |
+-----------------------------+------------------------------------------------+
| ``shutil.move(src, dst)``   | ``std::fs::rename(src, dst)``                  |
+-----------------------------+------------------------------------------------+
| ``shutil.which(cmd)``       | ``which::which(cmd)``                          |
+-----------------------------+------------------------------------------------+

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
