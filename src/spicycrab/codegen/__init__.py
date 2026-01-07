"""Code generation module for spicycrab - IR to Rust code emission."""

from spicycrab.codegen.cargo import generate_cargo_toml
from spicycrab.codegen.emitter import RustEmitter, emit_module

__all__ = ["RustEmitter", "emit_module", "generate_cargo_toml"]
