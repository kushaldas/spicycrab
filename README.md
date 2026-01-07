# spicycrab

A Python to Rust transpiler for type-annotated Python code.

> **Note**: spicycrab and cookcrab are under active development. APIs, CLI options, and generated code may change frequently.

## Features

- **crabpy** - Transpile Python code to Rust
- **cookcrab** - Generate Python stubs from Rust crates

## Installation

```bash
python3 -m pip install spicycrab
```

## Development Setup

```bash
# Clone the repository
git clone https://github.com/kushaldas/spicycrab.git
cd spicycrab

# Create virtual environment
uv venv
source .venv/bin/activate

# Install with all development and documentation dependencies
uv pip install -e ".[dev,docs]"

# Verify installation
crabpy --version
cookcrab --version
```

## Quick Start

### Transpile Python to Rust

```bash
crabpy transpile input.py -o rust_output -n my_project
crabpy transpile src/ -o rust_project/ -n my_project
```

### Use Rust Crates in Python

```bash
# Generate stubs for a Rust crate
cookcrab generate clap -o /tmp/stubs

# Install the stubs
python3 -m pip install -e /tmp/stubs/clap_builder
python3 -m pip install -e /tmp/stubs/clap

# Write Python code using Rust crate types
cat > myapp.py << 'EOF'
from spicycrab_clap import Command, Arg, ArgMatches

def main() -> None:
    matches: ArgMatches = (
        Command.new("myapp")
        .arg(Arg.new("name").required(True))
        .get_matches()
    )
    name: str = matches.get_one("name").unwrap().clone()
    print(f"Hello, {name}!")
EOF

# Transpile to Rust
crabpy transpile myapp.py -o rust_myapp -n myapp

# Build and run
cd rust_myapp && cargo build --release
./target/release/myapp World
```

## Requirements

- Python 3.10+
- All Python code must have type annotations

## Supported Python Features

### String Methods

The transpiler supports common Python string methods with automatic Rust equivalents:

| Python | Rust |
|--------|------|
| `s.upper()` | `s.to_uppercase()` |
| `s.lower()` | `s.to_lowercase()` |
| `s.strip()` | `s.trim().to_string()` |
| `s.replace(a, b)` | `s.replace(a, b)` |
| `s.startswith(x)` | `s.starts_with(x)` |
| `s.endswith(x)` | `s.ends_with(x)` |
| `s.split(sep)` | `s.split(sep).collect::<Vec<_>>()` |
| `s.join(iter)` | `iter.join(&s)` |
| `s.isdigit()` | `s.chars().all(\|c\| c.is_ascii_digit())` |
| `s.find(x) >= 0` | `s.contains(x)` |
| `s.find(x) == -1` | `!s.contains(x)` |

### Index Operations

Integer variables used for indexing are automatically cast to `usize`:

```python
# Python
values: list[int] = [1, 2, 3]
i: int = 0
while i < len(values):
    print(values[i])
    i = i + 1
```

```rust
// Generated Rust
let values: Vec<i64> = vec![1, 2, 3];
let mut i: i64 = 0;
while (i as usize) < values.len() {
    println!("{}", values[i as usize]);
    i += 1;
}
```

### Membership Operators

The `in` and `not in` operators are supported:

```python
if x in container:      # -> container.contains(&x)
if x not in container:  # -> !container.contains(&x)
```

### Error Handling

Functions returning `Result[T, E]` automatically get `?` operator propagation:

```python
def might_fail() -> Result[int, str]:
    return Ok(42)

def caller() -> Result[int, str]:
    value: int = might_fail()  # Automatically gets ? operator
    return Ok(value + 1)
```
