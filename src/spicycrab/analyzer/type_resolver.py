"""Type resolver for spicycrab.

Resolves Python type annotations to Rust types and validates type consistency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from spicycrab.ir.nodes import (
    IRClassType,
    IRGenericType,
    IRModule,
    IRPrimitiveType,
    IRType,
    IRUnionType,
    PrimitiveType,
)

if TYPE_CHECKING:
    pass


@dataclass
class RustType:
    """Represents a resolved Rust type."""

    name: str
    generics: list[RustType] = field(default_factory=list)
    is_reference: bool = False
    is_mutable: bool = False
    lifetime: str | None = None

    def to_rust(self) -> str:
        """Convert to Rust type syntax."""
        result = self.name

        if self.generics:
            generic_strs = [g.to_rust() for g in self.generics]
            result = f"{result}<{', '.join(generic_strs)}>"

        if self.is_reference:
            lifetime_str = f"'{self.lifetime} " if self.lifetime else ""
            mut_str = "mut " if self.is_mutable else ""
            result = f"&{lifetime_str}{mut_str}{result}"

        return result


# Mapping from Python primitive types to Rust types
PRIMITIVE_MAP: dict[PrimitiveType, str] = {
    PrimitiveType.INT: "i64",
    PrimitiveType.FLOAT: "f64",
    PrimitiveType.BOOL: "bool",
    PrimitiveType.STR: "String",
    PrimitiveType.BYTES: "Vec<u8>",
    PrimitiveType.NONE: "()",
}

# Mapping from Python generic types to Rust types
GENERIC_MAP: dict[str, str] = {
    "List": "Vec",
    "list": "Vec",
    "Dict": "HashMap",
    "dict": "HashMap",
    "Set": "HashSet",
    "set": "HashSet",
    "Tuple": "",  # Special handling
    "tuple": "",
    "Optional": "Option",
    "Sequence": "Vec",
    "Mapping": "HashMap",
    "FrozenSet": "HashSet",
    "frozenset": "HashSet",
    "Iterable": "Vec",  # Simplified
    "Iterator": "Vec",  # Simplified
}


class TypeResolver:
    """Resolves IR types to Rust types."""

    def __init__(self) -> None:
        self.imports: set[str] = set()  # Track required Rust imports
        self.custom_types: dict[str, RustType] = {}  # User-defined types

    def resolve(self, ir_type: IRType | None) -> RustType:
        """Resolve an IR type to a Rust type."""
        if ir_type is None:
            return RustType(name="()")

        if isinstance(ir_type, IRPrimitiveType):
            return self._resolve_primitive(ir_type)

        if isinstance(ir_type, IRGenericType):
            return self._resolve_generic(ir_type)

        if isinstance(ir_type, IRUnionType):
            return self._resolve_union(ir_type)

        if isinstance(ir_type, IRClassType):
            return self._resolve_class(ir_type)

        # Fallback
        return RustType(name="()")

    def _resolve_primitive(self, ir_type: IRPrimitiveType) -> RustType:
        """Resolve a primitive type."""
        rust_name = PRIMITIVE_MAP.get(ir_type.kind, "()")
        return RustType(name=rust_name)

    def _resolve_generic(self, ir_type: IRGenericType) -> RustType:
        """Resolve a generic type like List[T], Dict[K, V]."""
        name = ir_type.name

        # Handle Option specially
        if name == "Optional":
            if ir_type.type_args:
                inner = self.resolve(ir_type.type_args[0])
                return RustType(name="Option", generics=[inner])
            return RustType(name="Option", generics=[RustType(name="()")])

        # Handle Tuple specially - becomes Rust tuple
        if name in ("Tuple", "tuple"):
            if ir_type.type_args:
                resolved = [self.resolve(t) for t in ir_type.type_args]
                # Rust tuple syntax is (A, B, C)
                inner = ", ".join(r.to_rust() for r in resolved)
                return RustType(name=f"({inner})")
            return RustType(name="()")

        # Standard generics
        rust_name = GENERIC_MAP.get(name, name)

        if rust_name in ("HashMap", "HashSet"):
            self.imports.add("std::collections")

        generics = [self.resolve(t) for t in ir_type.type_args]
        return RustType(name=rust_name, generics=generics)

    def _resolve_union(self, ir_type: IRUnionType) -> RustType:
        """Resolve a Union type.

        For now, we generate a simple enum. In the future, we could
        be smarter about common patterns.
        """
        # Check if this is Option (Union with None)
        none_count = sum(
            1 for v in ir_type.variants
            if isinstance(v, IRPrimitiveType) and v.kind == PrimitiveType.NONE
        )

        if none_count == 1 and len(ir_type.variants) == 2:
            # This is Optional[T]
            other = next(
                v for v in ir_type.variants
                if not (isinstance(v, IRPrimitiveType) and v.kind == PrimitiveType.NONE)
            )
            inner = self.resolve(other)
            return RustType(name="Option", generics=[inner])

        # Generate enum name based on variants
        if ir_type.generated_name:
            return RustType(name=ir_type.generated_name)

        # Fallback - create a generic union name
        return RustType(name="UnionType")

    def _resolve_class(self, ir_type: IRClassType) -> RustType:
        """Resolve a user-defined class type."""
        # Check for known types
        name = ir_type.name

        # Path types
        if name in ("Path", "PurePath", "PosixPath", "WindowsPath"):
            self.imports.add("std::path")
            return RustType(name="PathBuf")

        # Check custom types
        if name in self.custom_types:
            return self.custom_types[name]

        # Assume it's a user-defined struct
        return RustType(name=name)

    def register_class(self, name: str, rust_type: RustType | None = None) -> None:
        """Register a user-defined class type."""
        if rust_type is None:
            rust_type = RustType(name=name)
        self.custom_types[name] = rust_type

    def get_imports(self) -> list[str]:
        """Get list of required Rust use statements."""
        imports = []

        if "std::collections" in self.imports:
            imports.append("use std::collections::{HashMap, HashSet};")

        if "std::path" in self.imports:
            imports.append("use std::path::PathBuf;")

        return sorted(imports)


def resolve_types(module: IRModule) -> TypeResolver:
    """Resolve all types in a module and return the resolver."""
    resolver = TypeResolver()

    # Register all classes defined in the module
    for cls in module.classes:
        resolver.register_class(cls.name)

    return resolver
