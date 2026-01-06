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
crabpy input.py -o output.rs
crabpy src/ -o rust_project/
```

## Requirements

- Python 3.10+
- All Python code must have type annotations
