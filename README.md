# crabpy

A Python to Rust transpiler for type-annotated Python code.

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Usage

```bash
crabpy transpile input.py -o rust_output -n my_project
crabpy transpile src/ -o rust_project/ -n my_project
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
