Async Programming
=================

spicycrab supports async/await syntax, transpiling Python async code to Rust
using the tokio runtime.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

Async support in spicycrab comes in two levels:

1. **Basic async/await** - Works out of the box, no stubs required
2. **Tokio features** - Requires installing ``spicycrab_tokio`` stubs

The transpiler automatically:

- Adds ``tokio`` dependency to Cargo.toml when async functions are detected
- Adds ``#[tokio::main]`` attribute to async main functions
- Converts ``await expr`` to ``expr.await`` (Rust syntax)
- Filters out ``asyncio.run(main())`` since ``#[tokio::main]`` handles entry

Basic Async/Await
-----------------

Basic async functions work without any stubs. Just use ``async def`` and ``await``.

Simple async function
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   async def greet(name: str) -> str:
       return f"Hello, {name}!"

.. code-block:: rust

   async fn greet(name: String) -> String {
       format!("Hello, {}!", name)
   }

Async main function
^^^^^^^^^^^^^^^^^^^

When you define ``async def main()``, spicycrab automatically adds the
``#[tokio::main]`` attribute:

.. code-block:: python

   async def greet(name: str) -> str:
       return f"Hello, {name}!"

   async def main() -> None:
       message: str = await greet("World")
       print(message)

.. code-block:: rust

   async fn greet(name: String) -> String {
       format!("Hello, {}!", name)
   }

   #[tokio::main]
   async fn main() {
       let message: String = greet("World".to_string()).await;
       println!("{}", message);
   }

Awaiting expressions
^^^^^^^^^^^^^^^^^^^^

The ``await`` keyword is placed after the expression in Rust (postfix syntax):

.. code-block:: python

   async def fetch_data() -> str:
       result: str = await get_from_server()
       return result

.. code-block:: rust

   async fn fetch_data() -> String {
       let result: String = get_from_server().await;
       result
   }

Chained awaits
^^^^^^^^^^^^^^

.. code-block:: python

   async def process() -> str:
       data: str = await fetch()
       result: str = await transform(data)
       return result

.. code-block:: rust

   async fn process() -> String {
       let data: String = fetch().await;
       let result: String = transform(data).await;
       result
   }

Tokio Features (Requires Stubs)
-------------------------------

For advanced async features like spawning tasks, sleeping, and channels,
you need to install the tokio stubs.

Installing tokio stubs
^^^^^^^^^^^^^^^^^^^^^^

**Option 1: Install from spicycrab-stubs repository (recommended)**

Use ``cookcrab install`` to fetch and install stubs from the official repository:

.. code-block:: bash

   # Install tokio stubs
   cookcrab install tokio

   # Install a specific version
   cookcrab install tokio -v 1.49.0

This command:

1. Fetches the stub from `spicycrab-stubs <https://github.com/kushaldas/spicycrab-stubs>`_
2. Builds a wheel locally
3. Installs it in your environment

**Option 2: Generate stubs yourself**

You can also generate stubs from scratch using ``cookcrab generate``:

.. code-block:: bash

   # Generate stubs for tokio
   cookcrab generate tokio -o /tmp/stubs

   # Install the generated stubs
   cookcrab install tokio --repo /tmp/stubs

.. warning::

   Always use ``cookcrab install`` instead of ``pip install`` directly.
   This ensures compatibility with spicycrab's stub discovery system.

Using tokio imports
^^^^^^^^^^^^^^^^^^^

Once installed, import tokio features:

.. code-block:: python

   from spicycrab_tokio import spawn, sleep, Duration
   from spicycrab_tokio import mpsc_channel, MpscSender, MpscReceiver

Async Sleep
-----------

Use ``sleep`` with ``Duration`` for async delays:

.. code-block:: python

   from spicycrab_tokio import sleep, Duration

   async def delay_print(msg: str, secs: int) -> None:
       """Print a message after a delay."""
       await sleep(Duration.from_secs(secs))
       print(msg)

   async def main() -> None:
       print("Starting...")
       await delay_print("After 1 second", 1)
       await delay_print("After 2 more seconds", 2)
       print("Done!")

.. code-block:: rust

   async fn delay_print(msg: String, secs: i64) {
       tokio::time::sleep(std::time::Duration::from_secs(secs as u64)).await;
       println!("{}", msg);
   }

   #[tokio::main]
   async fn main() {
       println!("Starting...");
       delay_print("After 1 second".to_string(), 1).await;
       delay_print("After 2 more seconds".to_string(), 2).await;
       println!("Done!");
   }

Duration methods
^^^^^^^^^^^^^^^^

.. code-block:: python

   from spicycrab_tokio import Duration

   # Create durations
   d1 = Duration.from_secs(5)        # 5 seconds
   d2 = Duration.from_millis(500)    # 500 milliseconds
   d3 = Duration.from_micros(1000)   # 1000 microseconds
   d4 = Duration.from_nanos(1000000) # 1000000 nanoseconds

.. code-block:: rust

   // Create durations
   let d1 = std::time::Duration::from_secs(5 as u64);
   let d2 = std::time::Duration::from_millis(500 as u64);
   let d3 = std::time::Duration::from_micros(1000 as u64);
   let d4 = std::time::Duration::from_nanos(1000000 as u64);

Spawning Tasks
--------------

Use ``spawn`` to run tasks concurrently. Spawned tasks return a ``JoinHandle``
that can be awaited to get the result.

Basic task spawning
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from spicycrab_tokio import spawn, sleep, Duration
   from spicycrab.types import Result

   async def do_work(task_id: int) -> int:
       """Simulate some async work."""
       print(f"Task {task_id} starting...")
       await sleep(Duration.from_millis(100))
       print(f"Task {task_id} finished!")
       return task_id * 10

   async def main() -> None:
       """Main function demonstrating concurrent task spawning."""
       print("Spawning tasks...")

       # Spawn multiple tasks
       handle1 = spawn(do_work(1))
       handle2 = spawn(do_work(2))
       handle3 = spawn(do_work(3))

       # Wait for all tasks to complete
       # JoinHandle yields Result<T, JoinError>
       result1: int = Result.unwrap(await handle1)
       result2: int = Result.unwrap(await handle2)
       result3: int = Result.unwrap(await handle3)

       print(f"Results: {result1}, {result2}, {result3}")
       print("All tasks completed!")

.. code-block:: rust

   async fn do_work(task_id: i64) -> i64 {
       println!("{}", format!("Task {} starting...", task_id));
       tokio::time::sleep(std::time::Duration::from_millis(100 as u64)).await;
       println!("{}", format!("Task {} finished!", task_id));
       task_id * 10
   }

   #[tokio::main]
   async fn main() {
       println!("Spawning tasks...");
       let handle1 = tokio::spawn(do_work(1));
       let handle2 = tokio::spawn(do_work(2));
       let handle3 = tokio::spawn(do_work(3));
       let result1: i64 = handle1.await.unwrap();
       let result2: i64 = handle2.await.unwrap();
       let result3: i64 = handle3.await.unwrap();
       println!("{}", format!("Results: {}, {}, {}", result1, result2, result3));
       println!("All tasks completed!");
   }

JoinHandle and Result
^^^^^^^^^^^^^^^^^^^^^

When you await a ``JoinHandle``, it returns a ``Result<T, JoinError>`` because
the spawned task could panic. Use ``Result.unwrap()`` to extract the value:

.. code-block:: python

   from spicycrab.types import Result

   handle = spawn(compute_value())
   value: int = Result.unwrap(await handle)  # unwrap the Result

Channels (mpsc)
---------------

Multi-producer single-consumer channels allow communication between tasks.

Creating a channel
^^^^^^^^^^^^^^^^^^

Use ``mpsc_channel(capacity)`` to create a bounded channel. It returns a
tuple of ``(sender, receiver)`` using tuple destructuring:

.. code-block:: python

   from spicycrab_tokio import mpsc_channel, MpscSender, MpscReceiver

   # Create channel with capacity 10
   tx, rx = mpsc_channel(10)

.. code-block:: rust

   let (tx, mut rx) = tokio::sync::mpsc::channel(10);

.. note::

   The receiver ``rx`` is automatically marked as ``mut`` because the
   ``recv()`` method requires ``&mut self``.

Sending messages
^^^^^^^^^^^^^^^^

Use ``tx.send(value)`` to send messages. The sender can be cloned:

.. code-block:: python

   async def producer(tx: MpscSender, id: int) -> None:
       for i in range(3):
           msg: str = f"Message {i} from producer {id}"
           await tx.send(msg)

.. code-block:: rust

   async fn producer(tx: tokio::sync::mpsc::Sender<String>, id: i64) {
       for i in 0..3 {
           let msg: String = format!("Message {} from producer {}", i, id);
           tx.send(msg).await;
       }
   }

Receiving messages
^^^^^^^^^^^^^^^^^^

Use ``rx.recv()`` to receive messages. Returns ``None`` when channel closes:

.. code-block:: python

   msg = await rx.recv()
   if msg is not None:
       print(f"Received: {msg}")

.. code-block:: rust

   let msg = rx.recv().await;
   if let Some(msg) = msg {
       println!("{}", format!("Received: {}", msg));
   }

Complete channel example
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   """Communication between tasks using mpsc channels."""

   from spicycrab_tokio import spawn, mpsc_channel, sleep, Duration, MpscSender, MpscReceiver
   from spicycrab.types import Result

   async def producer(tx: MpscSender, id: int) -> None:
       """Send messages through the channel."""
       for i in range(3):
           msg: str = f"Message {i} from producer {id}"
           print(f"Sending: {msg}")
           await tx.send(msg)
           await sleep(Duration.from_millis(50))

   async def main() -> None:
       """Main function demonstrating mpsc channel communication."""
       # Create a bounded channel with capacity 10
       tx, rx = mpsc_channel(10)

       # Clone tx for second producer
       tx2: MpscSender = tx.clone()

       # Spawn producer tasks
       handle1 = spawn(producer(tx, 1))
       handle2 = spawn(producer(tx2, 2))

       # Receive messages
       count: int = 0
       while count < 6:
           msg = await rx.recv()
           if msg is not None:
               print(f"Received: {msg}")
               count = count + 1

       # Wait for producers to finish
       Result.unwrap(await handle1)
       Result.unwrap(await handle2)

       print("All messages received!")

.. code-block:: rust

   /// Send messages through the channel.
   async fn producer(tx: tokio::sync::mpsc::Sender<String>, id: i64) {
       for i in 0..3 {
           let msg: String = format!("Message {} from producer {}", i, id);
           println!("{}", format!("Sending: {}", msg));
           tx.send(msg).await;
           tokio::time::sleep(std::time::Duration::from_millis(50 as u64)).await;
       }
   }

   #[tokio::main]
   /// Main function demonstrating mpsc channel communication.
   async fn main() {
       let (tx, mut rx) = tokio::sync::mpsc::channel(10);
       let tx2: tokio::sync::mpsc::Sender<String> = tx.clone();
       let handle1 = tokio::spawn(producer(tx, 1));
       let handle2 = tokio::spawn(producer(tx2, 2));
       let mut count: i64 = 0;
       while count < 6 {
           let msg = rx.recv().await;
           if let Some(msg) = msg {
               println!("{}", format!("Received: {}", msg));
               count += 1;
           }
       }
       handle1.await.unwrap();
       handle2.await.unwrap();
       println!("All messages received!");
   }

Output:

.. code-block:: text

   Sending: Message 0 from producer 1
   Sending: Message 0 from producer 2
   Received: Message 0 from producer 1
   Received: Message 0 from producer 2
   Sending: Message 1 from producer 2
   Sending: Message 1 from producer 1
   Received: Message 1 from producer 2
   Received: Message 1 from producer 1
   Sending: Message 2 from producer 1
   Sending: Message 2 from producer 2
   Received: Message 2 from producer 1
   Received: Message 2 from producer 2
   All messages received!

Shared State with Arc
---------------------

When multiple async tasks need to share data, use ``Arc`` (Atomically Reference
Counted pointer). Arc allows multiple tasks to safely share ownership of data.

Arc basics
^^^^^^^^^^

Import Arc from spicycrab_tokio:

.. code-block:: python

   from spicycrab_tokio import Arc

Create shared data with ``Arc.new()``:

.. code-block:: python

   # Create shared config wrapped in Arc
   config: Arc[str] = Arc.new("shared configuration data")

Clone Arc for each task (increments reference count):

.. code-block:: python

   config1: Arc[str] = Arc.clone(config)
   config2: Arc[str] = Arc.clone(config)

Check reference count:

.. code-block:: python

   count: int = Arc.strong_count(config)

Sharing data between tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^

A common pattern is to clone Arc for each spawned task:

.. code-block:: python

   from spicycrab_tokio import spawn, sleep, Duration, Arc
   from spicycrab.types import Result

   async def print_config(config: Arc[str], task_id: int) -> None:
       """A worker task that reads shared config data."""
       print(f"Task {task_id}: Starting with config")
       await sleep(Duration.from_millis(50))
       count: int = Arc.strong_count(config)
       print(f"Task {task_id}: Done. Strong count = {count}")

   async def main() -> None:
       """Main function demonstrating Arc usage."""
       config: Arc[str] = Arc.new("shared configuration data")
       print(f"Initial strong count: {Arc.strong_count(config)}")

       # Clone for each task
       config1: Arc[str] = Arc.clone(config)
       config2: Arc[str] = Arc.clone(config)
       config3: Arc[str] = Arc.clone(config)

       print(f"After cloning: strong count = {Arc.strong_count(config)}")

       # Spawn tasks that share the config
       handle1 = spawn(print_config(config1, 1))
       handle2 = spawn(print_config(config2, 2))
       handle3 = spawn(print_config(config3, 3))

       # Wait for all tasks to complete
       Result.unwrap(await handle1)
       Result.unwrap(await handle2)
       Result.unwrap(await handle3)

       print(f"After tasks complete: strong count = {Arc.strong_count(config)}")
       print("All tasks completed!")

.. code-block:: rust

   /// A worker task that reads shared config data.
   pub async fn print_config(config: std::sync::Arc<String>, task_id: i64) {
       println!("{}", format!("Task {}: Starting with config", task_id));
       tokio::time::sleep(std::time::Duration::from_millis(50 as u64)).await;
       let count: i64 = std::sync::Arc::strong_count(&config) as i64;
       println!("{}", format!("Task {}: Done. Strong count = {}", task_id, count));
   }

   #[tokio::main]
   /// Main function demonstrating Arc usage.
   pub async fn main() {
       let config: std::sync::Arc<String> =
           std::sync::Arc::new("shared configuration data".to_string());
       println!("{}", format!("Initial strong count: {}",
           std::sync::Arc::strong_count(&config) as i64));
       let config1: std::sync::Arc<String> = std::sync::Arc::clone(&config);
       let config2: std::sync::Arc<String> = std::sync::Arc::clone(&config);
       let config3: std::sync::Arc<String> = std::sync::Arc::clone(&config);
       println!("{}", format!("After cloning: strong count = {}",
           std::sync::Arc::strong_count(&config) as i64));
       let handle1 = tokio::spawn(print_config(config1, 1));
       let handle2 = tokio::spawn(print_config(config2, 2));
       let handle3 = tokio::spawn(print_config(config3, 3));
       handle1.await.unwrap();
       handle2.await.unwrap();
       handle3.await.unwrap();
       println!("{}", format!("After tasks complete: strong count = {}",
           std::sync::Arc::strong_count(&config) as i64));
       println!("All tasks completed!");
   }

Output:

.. code-block:: text

   Initial strong count: 1
   After cloning: strong count = 4
   Task 1: Starting with config
   Task 2: Starting with config
   Task 3: Starting with config
   Task 3: Done. Strong count = 4
   Task 1: Done. Strong count = 3
   Task 2: Done. Strong count = 2
   After tasks complete: strong count = 1
   All tasks completed!

Arc with Mutex for shared mutable state
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For shared *mutable* state, combine Arc with Mutex. The tokio stubs provide
``Mutex`` for async-aware mutual exclusion:

.. code-block:: python

   from spicycrab_tokio import spawn, sleep, Duration, Arc, Mutex
   from spicycrab.types import Result

   async def increment_counter(counter: Arc[Mutex[int]], task_id: int, times: int) -> None:
       """Increment the shared counter multiple times."""
       for i in range(times):
           # Lock the mutex to get exclusive access
           # In Rust: let mut guard = counter.lock().await;
           # Then: *guard += 1;
           print(f"Task {task_id}: incrementing (iteration {i + 1})")
           await sleep(Duration.from_millis(10))

   async def main() -> None:
       """Main function demonstrating Arc<Mutex<T>> usage."""
       # Create a shared counter protected by a mutex, wrapped in Arc
       counter: Arc[Mutex[int]] = Arc.new(Mutex.new(0))

       print("Starting concurrent counter increments...")
       print(f"Initial strong count: {Arc.strong_count(counter)}")

       # Clone the Arc for each task
       counter1: Arc[Mutex[int]] = Arc.clone(counter)
       counter2: Arc[Mutex[int]] = Arc.clone(counter)
       counter3: Arc[Mutex[int]] = Arc.clone(counter)

       print(f"After cloning: strong count = {Arc.strong_count(counter)}")

       # Spawn tasks that all increment the same counter
       handle1 = spawn(increment_counter(counter1, 1, 3))
       handle2 = spawn(increment_counter(counter2, 2, 3))
       handle3 = spawn(increment_counter(counter3, 3, 3))

       # Wait for all tasks to complete
       Result.unwrap(await handle1)
       Result.unwrap(await handle2)
       Result.unwrap(await handle3)

       print(f"After tasks complete: strong count = {Arc.strong_count(counter)}")
       print("All increments completed!")

.. code-block:: rust

   /// Increment the shared counter multiple times.
   pub async fn increment_counter(
       counter: std::sync::Arc<tokio::sync::Mutex<i64>>,
       task_id: i64,
       times: i64
   ) {
       for i in 0..times {
           println!("{}", format!("Task {}: incrementing (iteration {})",
               task_id, i + 1));
           tokio::time::sleep(std::time::Duration::from_millis(10 as u64)).await;
       }
   }

   #[tokio::main]
   /// Main function demonstrating Arc<Mutex<T>> usage.
   pub async fn main() {
       let counter: std::sync::Arc<tokio::sync::Mutex<i64>> =
           std::sync::Arc::new(tokio::sync::Mutex::new(0));
       println!("Starting concurrent counter increments...");
       println!("{}", format!("Initial strong count: {}",
           std::sync::Arc::strong_count(&counter) as i64));
       let counter1 = std::sync::Arc::clone(&counter);
       let counter2 = std::sync::Arc::clone(&counter);
       let counter3 = std::sync::Arc::clone(&counter);
       println!("{}", format!("After cloning: strong count = {}",
           std::sync::Arc::strong_count(&counter) as i64));
       let handle1 = tokio::spawn(increment_counter(counter1, 1, 3));
       let handle2 = tokio::spawn(increment_counter(counter2, 2, 3));
       let handle3 = tokio::spawn(increment_counter(counter3, 3, 3));
       handle1.await.unwrap();
       handle2.await.unwrap();
       handle3.await.unwrap();
       println!("{}", format!("After tasks complete: strong count = {}",
           std::sync::Arc::strong_count(&counter) as i64));
       println!("All increments completed!");
   }

.. note::

   ``tokio::sync::Mutex`` is used (not ``std::sync::Mutex``) because it is
   async-aware and safe to hold across ``.await`` points.

Arc methods
^^^^^^^^^^^

The following Arc methods are available:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Python
     - Rust
   * - ``Arc.new(value)``
     - ``std::sync::Arc::new(value)``
   * - ``Arc.clone(arc)``
     - ``std::sync::Arc::clone(&arc)``
   * - ``Arc.strong_count(arc)``
     - ``std::sync::Arc::strong_count(&arc) as i64``
   * - ``Arc.weak_count(arc)``
     - ``std::sync::Arc::weak_count(&arc) as i64``

Async Patterns
--------------

Sequential vs Concurrent
^^^^^^^^^^^^^^^^^^^^^^^^

**Sequential** - awaits happen one after another:

.. code-block:: python

   async def sequential() -> None:
       result1: str = await fetch("url1")  # Wait for this first
       result2: str = await fetch("url2")  # Then wait for this

**Concurrent** - tasks run at the same time:

.. code-block:: python

   async def concurrent() -> None:
       handle1 = spawn(fetch("url1"))  # Start both
       handle2 = spawn(fetch("url2"))  # immediately
       result1: str = Result.unwrap(await handle1)  # Wait for results
       result2: str = Result.unwrap(await handle2)

Fan-out/fan-in pattern
^^^^^^^^^^^^^^^^^^^^^^

Spawn multiple workers and collect results:

.. code-block:: python

   async def process_all(items: list[str]) -> list[str]:
       handles: list = []
       for item in items:
           h = spawn(process(item))
           handles.append(h)

       results: list[str] = []
       for h in handles:
           r: str = Result.unwrap(await h)
           results.append(r)
       return results

Producer-consumer pattern
^^^^^^^^^^^^^^^^^^^^^^^^^

Use channels to decouple producers from consumers:

.. code-block:: python

   async def producer(tx: MpscSender, data: list[str]) -> None:
       for item in data:
           await tx.send(item)

   async def consumer(rx: MpscReceiver) -> None:
       while True:
           msg = await rx.recv()
           if msg is None:
               break  # Channel closed
           await process(msg)

   async def main() -> None:
       tx, rx = mpsc_channel(100)

       # Start consumer
       consumer_handle = spawn(consumer(rx))

       # Produce items
       await producer(tx, ["a", "b", "c"])

       # Wait for consumer
       Result.unwrap(await consumer_handle)

Async with Control Flow
-----------------------

Async in loops
^^^^^^^^^^^^^^

.. code-block:: python

   async def poll_until_ready() -> str:
       while True:
           result: str = await check_status()
           if result == "ready":
               return result
           await sleep(Duration.from_secs(1))

.. code-block:: rust

   async fn poll_until_ready() -> String {
       loop {
           let result: String = check_status().await;
           if result == "ready".to_string() {
               return result;
           }
           tokio::time::sleep(std::time::Duration::from_secs(1 as u64)).await;
       }
   }

Async in conditionals
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   async def fetch_with_fallback(primary: str, backup: str) -> str:
       result = await try_fetch(primary)
       if result is None:
           result = await try_fetch(backup)
       return result

Best Practices
--------------

1. **Use type annotations** - Always annotate async function parameters and return types
2. **Prefer spawn for parallelism** - Don't await sequentially when tasks can run concurrently
3. **Handle JoinHandle Results** - Use ``Result.unwrap()`` or proper error handling
4. **Size channels appropriately** - Too small causes backpressure, too large wastes memory
5. **Clone senders, not receivers** - Senders can be cloned for multiple producers

Limitations
-----------

- **async closures** - Not yet supported
- **select/join macros** - ``tokio::select!`` and ``tokio::join!`` are not yet available
- **async generators** - Python async generators are not supported
- **async context managers** - ``async with`` is not yet implemented

Generated Cargo.toml
--------------------

When async functions are detected, spicycrab automatically adds tokio:

.. code-block:: toml

   [dependencies]
   tokio = { version = "1", features = ["full"] }

   [lints.rust]
   unused_must_use = "allow"

   [lints.clippy]
   unnecessary_cast = "allow"

The ``unused_must_use`` lint is allowed because channel operations return
Results that may be intentionally ignored.
