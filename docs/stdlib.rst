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

random
------

The ``random`` module is mapped to Rust's `rand <https://docs.rs/rand>`_ crate.

.. note::

   The ``rand`` crate uses a thread-local random number generator (``thread_rng()``)
   which is automatically seeded from the operating system. This is suitable for
   most use cases but cannot be explicitly seeded like Python's ``random.seed()``.

random.random()
^^^^^^^^^^^^^^^

Generate a random float in the range [0.0, 1.0).

.. code-block:: python

   import random

   def get_random() -> float:
       return random.random()

.. code-block:: rust

   pub fn get_random() -> f64 {
       rand::random::<f64>()
   }

random.randint()
^^^^^^^^^^^^^^^^

Generate a random integer in the inclusive range [a, b].

.. code-block:: python

   import random

   def dice_roll() -> int:
       return random.randint(1, 6)

.. code-block:: rust

   use rand::Rng;

   pub fn dice_roll() -> i64 {
       rand::thread_rng().gen_range(1..=6)
   }

random.randrange()
^^^^^^^^^^^^^^^^^^

Generate a random integer in the half-open range [a, b).

.. code-block:: python

   import random

   def random_index() -> int:
       return random.randrange(0, 10)  # 0 to 9

.. code-block:: rust

   use rand::Rng;

   pub fn random_index() -> i64 {
       rand::thread_rng().gen_range(0..10)
   }

random.uniform()
^^^^^^^^^^^^^^^^

Generate a random float in the inclusive range [a, b].

.. code-block:: python

   import random

   def random_float() -> float:
       return random.uniform(0.0, 100.0)

.. code-block:: rust

   use rand::Rng;

   pub fn random_float() -> f64 {
       rand::thread_rng().gen_range(0.0..=100.0)
   }

random.choice()
^^^^^^^^^^^^^^^

Select a random element from a non-empty sequence.

.. code-block:: python

   import random

   def pick_one(items: list[int]) -> int:
       return random.choice(items)

.. code-block:: rust

   use rand::seq::SliceRandom;

   pub fn pick_one(items: Vec<i64>) -> i64 {
       items.choose(&mut rand::thread_rng()).cloned().unwrap()
   }

random.sample()
^^^^^^^^^^^^^^^

Select k unique random elements from a sequence (without replacement).

.. code-block:: python

   import random

   def pick_three(items: list[int]) -> list[int]:
       return random.sample(items, 3)

.. code-block:: rust

   use rand::seq::SliceRandom;

   pub fn pick_three(items: Vec<i64>) -> Vec<i64> {
       items.choose_multiple(&mut rand::thread_rng(), 3)
           .cloned()
           .collect::<Vec<_>>()
   }

random.choices()
^^^^^^^^^^^^^^^^

Select k random elements from a sequence (with replacement).

.. code-block:: python

   import random

   def pick_with_replacement(items: list[int], k: int) -> list[int]:
       return random.choices(items, k)

.. code-block:: rust

   use rand::seq::SliceRandom;

   pub fn pick_with_replacement(items: Vec<i64>, k: usize) -> Vec<i64> {
       (0..k).map(|_| items.choose(&mut rand::thread_rng()).cloned().unwrap())
           .collect::<Vec<_>>()
   }

random.shuffle()
^^^^^^^^^^^^^^^^

Shuffle a sequence in place.

.. code-block:: python

   import random

   def shuffle_deck(cards: list[int]) -> None:
       random.shuffle(cards)

.. code-block:: rust

   use rand::seq::SliceRandom;

   pub fn shuffle_deck(cards: &mut Vec<i64>) {
       cards.shuffle(&mut rand::thread_rng());
   }

.. warning::

   **Known Limitation:** ``random.shuffle()`` modifies the sequence in place,
   which requires mutable access in Rust. The transpiler's mutability analysis
   may not automatically detect that a variable needs to be mutable when
   ``shuffle()`` is called on it. See :ref:`random-shuffle-limitation` below.

random.gauss()
^^^^^^^^^^^^^^

Generate a random number from a Gaussian (normal) distribution.

.. code-block:: python

   import random

   def normal_value() -> float:
       return random.gauss(0.0, 1.0)  # mean=0, stddev=1

.. code-block:: rust

   use rand_distr::{Distribution, Normal};

   pub fn normal_value() -> f64 {
       Normal::new(0.0, 1.0).unwrap().sample(&mut rand::thread_rng())
   }

Supported random functions
^^^^^^^^^^^^^^^^^^^^^^^^^^

+-----------------------------+------------------------------------------------+
| Python                      | Rust                                           |
+=============================+================================================+
| ``random.random()``         | ``rand::random::<f64>()``                      |
+-----------------------------+------------------------------------------------+
| ``random.randint(a, b)``    | ``thread_rng().gen_range(a..=b)``              |
+-----------------------------+------------------------------------------------+
| ``random.randrange(a, b)``  | ``thread_rng().gen_range(a..b)``               |
+-----------------------------+------------------------------------------------+
| ``random.uniform(a, b)``    | ``thread_rng().gen_range(a..=b)``              |
+-----------------------------+------------------------------------------------+
| ``random.choice(seq)``      | ``seq.choose(&mut rng).cloned().unwrap()``     |
+-----------------------------+------------------------------------------------+
| ``random.shuffle(seq)``     | ``seq.shuffle(&mut rng)``                      |
+-----------------------------+------------------------------------------------+
| ``random.sample(seq, k)``   | ``seq.choose_multiple(&mut rng, k)``           |
+-----------------------------+------------------------------------------------+
| ``random.choices(seq, k)``  | Loop with ``choose()``                         |
+-----------------------------+------------------------------------------------+
| ``random.gauss(mu, sigma)`` | ``rand_distr::Normal::new(mu, sigma)``         |
+-----------------------------+------------------------------------------------+

.. _random-shuffle-limitation:

Known Limitations
^^^^^^^^^^^^^^^^^

**random.shuffle() and Mutability**

In Python, ``random.shuffle()`` modifies a list in place:

.. code-block:: python

   items = [1, 2, 3, 4, 5]
   random.shuffle(items)  # items is now shuffled

In Rust, this requires the variable to be declared as mutable (``let mut``).
The spicycrab transpiler performs mutability analysis to detect when variables
need to be mutable, but it currently does not detect that calling
``random.shuffle()`` on a variable requires mutability.

**Workaround:** If you encounter a compilation error like:

.. code-block:: text

   error[E0596]: cannot borrow `items` as mutable, as it is not declared as mutable

You have two options:

1. **Manual fix:** Edit the generated Rust code to add ``mut``:

   .. code-block:: rust

      // Change this:
      let items: Vec<i64> = vec![1, 2, 3, 4, 5];
      // To this:
      let mut items: Vec<i64> = vec![1, 2, 3, 4, 5];

2. **Use sample instead:** If you don't need in-place shuffling, use
   ``random.sample()`` with the full length to get a shuffled copy:

   .. code-block:: python

      # Instead of:
      random.shuffle(items)

      # Use:
      shuffled: list[int] = random.sample(items, len(items))

**random.seed() Not Supported**

Python's ``random.seed()`` allows setting a seed for reproducible random sequences.
Rust's ``thread_rng()`` is automatically seeded by the OS and cannot be manually
seeded. The transpiler emits a comment noting this limitation:

.. code-block:: rust

   /* random.seed() - thread_rng cannot be seeded; use StdRng::seed_from_u64() for reproducibility */

For reproducible random sequences in Rust, you would need to use ``StdRng`` instead
of ``thread_rng()``, which requires manual code modification after transpilation.

logging
-------

The ``logging`` module is mapped to Rust's `log <https://docs.rs/log>`_ crate
with `env_logger <https://docs.rs/env_logger>`_ for initialization.

.. note::

   In Rust, logging levels are controlled via the ``RUST_LOG`` environment variable.
   For example, ``RUST_LOG=debug ./my_program`` enables debug logging.

Basic Logging
^^^^^^^^^^^^^

The logging functions map directly to Rust's ``log`` macros:

.. code-block:: python

   import logging

   def example() -> None:
       logging.debug("Debug message")
       logging.info("Info message")
       logging.warning("Warning message")
       logging.error("Error message")
       logging.critical("Critical message")

.. code-block:: rust

   pub fn example() {
       log::debug!("{}", "Debug message");
       log::info!("{}", "Info message");
       log::warn!("{}", "Warning message");
       log::error!("{}", "Error message");
       log::error!("{}", "Critical message");  // No critical level in Rust
   }

Logger Initialization
^^^^^^^^^^^^^^^^^^^^^

Use ``logging.basicConfig()`` to initialize the logger:

.. code-block:: python

   import logging

   def main() -> None:
       logging.basicConfig()
       logging.info("Application started")

.. code-block:: rust

   pub fn main() {
       env_logger::init();
       log::info!("{}", "Application started");
   }

.. warning::

   Unlike Python's ``basicConfig()``, Rust's ``env_logger::init()`` can only be
   called once. Multiple calls will panic. Ensure initialization happens at program
   start, typically in ``main()``.

Format String Logging
^^^^^^^^^^^^^^^^^^^^^

Python format strings are converted to Rust format strings:

.. code-block:: python

   import logging

   def log_user(name: str, age: int) -> None:
       logging.info(f"User {name} is {age} years old")

.. code-block:: rust

   pub fn log_user(name: String, age: i64) {
       log::info!("{}", format!("User {} is {} years old", name, age));
   }

Logging Levels
^^^^^^^^^^^^^^

Python logging levels map to Rust's ``log::LevelFilter``:

+------------------------+-----------------------------+
| Python                 | Rust                        |
+========================+=============================+
| ``logging.DEBUG``      | ``log::LevelFilter::Debug`` |
+------------------------+-----------------------------+
| ``logging.INFO``       | ``log::LevelFilter::Info``  |
+------------------------+-----------------------------+
| ``logging.WARNING``    | ``log::LevelFilter::Warn``  |
+------------------------+-----------------------------+
| ``logging.ERROR``      | ``log::LevelFilter::Error`` |
+------------------------+-----------------------------+
| ``logging.CRITICAL``   | ``log::LevelFilter::Error`` |
+------------------------+-----------------------------+

.. note::

   Rust's ``log`` crate does not have a ``CRITICAL`` level. Both ``logging.critical()``
   and ``logging.CRITICAL`` map to ``log::error!`` / ``log::LevelFilter::Error``.

Supported logging functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

+----------------------------+-------------------------------+
| Python                     | Rust                          |
+============================+===============================+
| ``logging.debug(msg)``     | ``log::debug!("{}", msg)``    |
+----------------------------+-------------------------------+
| ``logging.info(msg)``      | ``log::info!("{}", msg)``     |
+----------------------------+-------------------------------+
| ``logging.warning(msg)``   | ``log::warn!("{}", msg)``     |
+----------------------------+-------------------------------+
| ``logging.warn(msg)``      | ``log::warn!("{}", msg)``     |
+----------------------------+-------------------------------+
| ``logging.error(msg)``     | ``log::error!("{}", msg)``    |
+----------------------------+-------------------------------+
| ``logging.critical(msg)``  | ``log::error!("{}", msg)``    |
+----------------------------+-------------------------------+
| ``logging.exception(msg)`` | ``log::error!("{}", msg)``    |
+----------------------------+-------------------------------+
| ``logging.basicConfig()``  | ``env_logger::init()``        |
+----------------------------+-------------------------------+

Known Limitations
^^^^^^^^^^^^^^^^^

**Logger Configuration**

Python's ``logging`` module provides extensive configuration options through
``basicConfig()`` (format, level, handlers, etc.). In Rust, ``env_logger``
configuration is done via environment variables or builder pattern. The transpiler
uses simple ``env_logger::init()`` which respects the ``RUST_LOG`` environment
variable.

**Named Loggers**

Python supports named loggers with ``logging.getLogger("name")``. Rust's ``log``
crate uses module paths as logger names automatically. Named logger creation is
not currently transpiled.

**Custom Handlers**

Python's ``logging.FileHandler``, ``StreamHandler``, etc. are not supported.
In Rust, these would require using ``env_logger``'s builder pattern or other
logging backends like ``fern`` or ``tracing``.

Rust Standard Library (rust_std)
---------------------------------

spicycrab provides direct mappings to Rust's standard library types through
the ``rust_std`` namespace. These are useful when you need direct access to
Rust-specific functionality that doesn't have a Python equivalent.

.. note::

   The ``rust_std`` module names are designed to avoid conflicts with Python's
   stdlib modules. For example, ``rust_std.time`` maps to Rust's ``std::time``
   (Duration, Instant), while Python's ``time`` module maps to ``chrono``.

rust_std.thread
^^^^^^^^^^^^^^^

Threading primitives from Rust's ``std::thread`` module.

**Spawning threads:**

.. code-block:: python

   from rust_std.thread import spawn, sleep
   from rust_std.time import Duration

   def worker() -> None:
       print("Worker thread running")

   def main() -> None:
       handle = spawn(worker)
       handle.join()

.. code-block:: rust

   pub fn worker() {
       println!("Worker thread running");
   }

   pub fn main() {
       let handle = std::thread::spawn(worker);
       handle.join().unwrap();
   }

**Thread sleep:**

.. code-block:: python

   from rust_std.thread import sleep
   from rust_std.time import Duration

   def wait_a_bit() -> None:
       sleep(Duration.from_secs(2))

.. code-block:: rust

   pub fn wait_a_bit() {
       std::thread::sleep(std::time::Duration::from_secs(2));
   }

**Thread utilities:**

+--------------------------------------+-----------------------------------------------+
| Python                               | Rust                                          |
+======================================+===============================================+
| ``rust_std.thread.spawn(f)``         | ``std::thread::spawn(f)``                     |
+--------------------------------------+-----------------------------------------------+
| ``rust_std.thread.sleep(d)``         | ``std::thread::sleep(d)``                     |
+--------------------------------------+-----------------------------------------------+
| ``rust_std.thread.current()``        | ``std::thread::current()``                    |
+--------------------------------------+-----------------------------------------------+
| ``rust_std.thread.yield_now()``      | ``std::thread::yield_now()``                  |
+--------------------------------------+-----------------------------------------------+
| ``rust_std.thread.park()``           | ``std::thread::park()``                       |
+--------------------------------------+-----------------------------------------------+
| ``rust_std.thread.Builder()``        | ``std::thread::Builder::new()``               |
+--------------------------------------+-----------------------------------------------+
| ``handle.join()``                    | ``handle.join().unwrap()``                    |
+--------------------------------------+-----------------------------------------------+
| ``handle.is_finished()``             | ``handle.is_finished()``                      |
+--------------------------------------+-----------------------------------------------+

rust_std.time
^^^^^^^^^^^^^

Time and duration types from Rust's ``std::time`` module.

**Duration creation:**

.. code-block:: python

   from rust_std.time import Duration

   def get_durations() -> None:
       one_second = Duration.from_secs(1)
       half_second = Duration.from_millis(500)
       one_micro = Duration.from_micros(1)
       one_nano = Duration.from_nanos(1)

.. code-block:: rust

   pub fn get_durations() {
       let one_second = std::time::Duration::from_secs(1);
       let half_second = std::time::Duration::from_millis(500);
       let one_micro = std::time::Duration::from_micros(1);
       let one_nano = std::time::Duration::from_nanos(1);
   }

**Measuring elapsed time with Instant:**

.. code-block:: python

   from rust_std.time import Instant

   def measure_time() -> None:
       start = Instant.now()
       # ... do some work ...
       elapsed = start.elapsed()
       print(f"Elapsed: {elapsed.as_millis()} ms")

.. code-block:: rust

   pub fn measure_time() {
       let start = std::time::Instant::now();
       // ... do some work ...
       let elapsed = start.elapsed();
       println!("Elapsed: {} ms", elapsed.as_millis());
   }

**System time and UNIX epoch:**

.. code-block:: python

   from rust_std.time import SystemTime, UNIX_EPOCH

   def get_timestamp() -> int:
       now = SystemTime.now()
       since_epoch = now.duration_since(UNIX_EPOCH)
       return since_epoch.as_secs()

.. code-block:: rust

   pub fn get_timestamp() -> u64 {
       let now = std::time::SystemTime::now();
       let since_epoch = now.duration_since(std::time::UNIX_EPOCH).unwrap();
       since_epoch.as_secs()
   }

**Duration methods:**

+--------------------------------------+-----------------------------------------------+
| Python                               | Rust                                          |
+======================================+===============================================+
| ``Duration.from_secs(n)``            | ``std::time::Duration::from_secs(n)``         |
+--------------------------------------+-----------------------------------------------+
| ``Duration.from_millis(n)``          | ``std::time::Duration::from_millis(n)``       |
+--------------------------------------+-----------------------------------------------+
| ``Duration.from_micros(n)``          | ``std::time::Duration::from_micros(n)``       |
+--------------------------------------+-----------------------------------------------+
| ``Duration.from_nanos(n)``           | ``std::time::Duration::from_nanos(n)``        |
+--------------------------------------+-----------------------------------------------+
| ``Duration.ZERO``                    | ``std::time::Duration::ZERO``                 |
+--------------------------------------+-----------------------------------------------+
| ``Duration.MAX``                     | ``std::time::Duration::MAX``                  |
+--------------------------------------+-----------------------------------------------+
| ``d.as_secs()``                      | ``d.as_secs()``                               |
+--------------------------------------+-----------------------------------------------+
| ``d.as_millis()``                    | ``d.as_millis()``                             |
+--------------------------------------+-----------------------------------------------+
| ``d.as_nanos()``                     | ``d.as_nanos()``                              |
+--------------------------------------+-----------------------------------------------+
| ``d.is_zero()``                      | ``d.is_zero()``                               |
+--------------------------------------+-----------------------------------------------+

**Instant methods:**

+--------------------------------------+-----------------------------------------------+
| Python                               | Rust                                          |
+======================================+===============================================+
| ``Instant.now()``                    | ``std::time::Instant::now()``                 |
+--------------------------------------+-----------------------------------------------+
| ``i.elapsed()``                      | ``i.elapsed()``                               |
+--------------------------------------+-----------------------------------------------+
| ``i.duration_since(earlier)``        | ``i.duration_since(earlier)``                 |
+--------------------------------------+-----------------------------------------------+

**SystemTime methods:**

+--------------------------------------+-----------------------------------------------+
| Python                               | Rust                                          |
+======================================+===============================================+
| ``SystemTime.now()``                 | ``std::time::SystemTime::now()``              |
+--------------------------------------+-----------------------------------------------+
| ``UNIX_EPOCH``                       | ``std::time::UNIX_EPOCH``                     |
+--------------------------------------+-----------------------------------------------+
| ``s.elapsed()``                      | ``s.elapsed()?``                              |
+--------------------------------------+-----------------------------------------------+
| ``s.duration_since(earlier)``        | ``s.duration_since(earlier)?``                |
+--------------------------------------+-----------------------------------------------+

rust_std.fs
^^^^^^^^^^^

File system operations from Rust's ``std::fs`` module.

**File operations:**

.. code-block:: python

   from rust_std.fs import File, read_to_string, write

   def read_file(path: str) -> str:
       return read_to_string(path)

   def write_file(path: str, content: str) -> None:
       write(path, content)

.. code-block:: rust

   pub fn read_file(path: String) -> String {
       std::fs::read_to_string(path).unwrap()
   }

   pub fn write_file(path: String, content: String) {
       std::fs::write(path, content).unwrap();
   }

rust_std.io
^^^^^^^^^^^

I/O operations from Rust's ``std::io`` module.

**Standard streams:**

.. code-block:: python

   from rust_std.io import stdin, stdout, stderr

   def get_streams():
       input_stream = stdin()
       output_stream = stdout()
       error_stream = stderr()

.. code-block:: rust

   pub fn get_streams() {
       let input_stream = std::io::stdin();
       let output_stream = std::io::stdout();
       let error_stream = std::io::stderr();
   }

rust_std.path
^^^^^^^^^^^^^

Path manipulation from Rust's ``std::path`` module.

**Path creation:**

.. code-block:: python

   from rust_std.path import Path, PathBuf

   def make_path(s: str) -> PathBuf:
       return PathBuf.from(s)

.. code-block:: rust

   pub fn make_path(s: String) -> PathBuf {
       std::path::PathBuf::from(s)
   }

Generated Dependencies
----------------------

When using stdlib features, spicycrab adds appropriate dependencies to Cargo.toml:

.. code-block:: toml

   [dependencies]
   serde = { version = "1.0", features = ["derive"] }
   serde_json = "1.0"
   chrono = "0.4"      # Added when using datetime module
   rand = "0.8"        # Added when using random module
   log = "0.4"         # Added when using logging module
   env_logger = "0.11" # Added when using logging module

Standard imports are also added:

.. code-block:: rust

   use std::collections::{HashMap, HashSet};
   use std::path::PathBuf;
