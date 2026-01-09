"""Type annotation parser for spicycrab.

Parses Python type annotations (from the `typing` module and built-in types)
and converts them to IR type representations.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from spicycrab.ir.nodes import (
    IRClassType,
    IRFunctionType,
    IRGenericType,
    IRPrimitiveType,
    IRType,
    IRUnionType,
    PrimitiveType,
)
from spicycrab.utils.errors import TypeAnnotationError

if TYPE_CHECKING:
    pass


# Mapping from Python type names to our primitive types
PRIMITIVE_TYPE_MAP: dict[str, PrimitiveType] = {
    "int": PrimitiveType.INT,
    "float": PrimitiveType.FLOAT,
    "str": PrimitiveType.STR,
    "bool": PrimitiveType.BOOL,
    "bytes": PrimitiveType.BYTES,
    "None": PrimitiveType.NONE,
    "NoneType": PrimitiveType.NONE,
}

# Special types that map to specific Rust types
SPECIAL_TYPE_MAP: set[str] = {
    "Any",  # typing.Any -> serde_json::Value
}

# Generic types from typing module
GENERIC_TYPES: set[str] = {
    "List",
    "list",
    "Dict",
    "dict",
    "Set",
    "set",
    "Tuple",
    "tuple",
    "Optional",
    "Result",  # Rust-style Result[T, E]
    "Sequence",
    "Mapping",
    "Iterable",
    "Iterator",
    "Callable",
    "FrozenSet",
    "frozenset",
}


class TypeParser:
    """Parser for Python type annotations."""

    def __init__(self, filename: str | None = None) -> None:
        self.filename = filename

    def parse(self, node: ast.expr | None, name: str | None = None) -> IRType:
        """Parse a type annotation AST node into an IRType.

        Args:
            node: The AST node representing the type annotation
            name: Optional name of the annotated item (for error messages)

        Returns:
            The parsed IRType

        Raises:
            TypeAnnotationError: If the type annotation is invalid or missing
        """
        if node is None:
            raise TypeAnnotationError(
                "Missing type annotation",
                name=name,
                filename=self.filename,
            )

        line = getattr(node, "lineno", None)

        if isinstance(node, ast.Constant):
            # Handle None literal
            if node.value is None:
                return IRPrimitiveType(kind=PrimitiveType.NONE)
            raise TypeAnnotationError(
                f"Unexpected constant in type annotation: {node.value}",
                name=name,
                filename=self.filename,
                line=line,
            )

        if isinstance(node, ast.Name):
            return self._parse_name(node.id, name, line)

        if isinstance(node, ast.Subscript):
            return self._parse_subscript(node, name, line)

        if isinstance(node, ast.Attribute):
            return self._parse_attribute(node, name, line)

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # Python 3.10+ union syntax: X | Y
            return self._parse_union([node.left, node.right], name, line)

        if isinstance(node, ast.Tuple):
            # Tuple of types (for Union)
            return self._parse_tuple_type(node.elts, name, line)

        raise TypeAnnotationError(
            f"Unsupported type annotation syntax: {ast.dump(node)}",
            name=name,
            filename=self.filename,
            line=line,
        )

    def _parse_name(self, type_name: str, name: str | None, line: int | None) -> IRType:
        """Parse a simple type name."""
        # Check if it's a primitive
        if type_name in PRIMITIVE_TYPE_MAP:
            return IRPrimitiveType(kind=PRIMITIVE_TYPE_MAP[type_name])

        # Check if it's a special type (Any -> Value)
        if type_name in SPECIAL_TYPE_MAP:
            return IRClassType(name=type_name)

        # Check if it's a generic without parameters (e.g., just 'list')
        if type_name in GENERIC_TYPES:
            # Return as generic with no type args (will need inference)
            return IRGenericType(name=type_name)

        # Assume it's a class type
        return IRClassType(name=type_name)

    def _parse_subscript(self, node: ast.Subscript, name: str | None, line: int | None) -> IRType:
        """Parse a subscripted type like List[int] or Dict[str, int]."""
        # Get the base type name
        if isinstance(node.value, ast.Name):
            base_name = node.value.id
        elif isinstance(node.value, ast.Attribute):
            # Handle typing.List, etc.
            base_name = node.value.attr
        else:
            raise TypeAnnotationError(
                f"Unsupported generic base: {ast.dump(node.value)}",
                name=name,
                filename=self.filename,
                line=line,
            )

        # Get type arguments
        type_args = self._parse_type_args(node.slice, name, line)

        # Handle special cases
        if base_name == "Optional":
            if len(type_args) != 1:
                raise TypeAnnotationError(
                    "Optional requires exactly one type argument",
                    name=name,
                    filename=self.filename,
                    line=line,
                )
            # Optional[X] is Union[X, None]
            return IRGenericType(name="Optional", type_args=type_args)

        if base_name == "Union":
            return IRUnionType(variants=type_args)

        if base_name == "Callable":
            return self._parse_callable(type_args, name, line)

        if base_name in GENERIC_TYPES:
            return IRGenericType(name=base_name, type_args=type_args)

        # User-defined generic class or crate type with type args (e.g., Arc[str])
        # Return as IRGenericType to preserve type arguments
        return IRGenericType(name=base_name, type_args=type_args)

    def _parse_type_args(self, slice_node: ast.expr, name: str | None, line: int | None) -> list[IRType]:
        """Parse type arguments from a subscript slice."""
        if isinstance(slice_node, ast.Tuple):
            return [self.parse(elt, name) for elt in slice_node.elts]
        else:
            return [self.parse(slice_node, name)]

    def _parse_attribute(self, node: ast.Attribute, name: str | None, line: int | None) -> IRType:
        """Parse a dotted type name like typing.List."""
        # Get the full dotted name
        parts = []
        current: ast.expr = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        parts.reverse()

        # Check if it's from typing module
        if parts[0] == "typing" and len(parts) == 2:
            return self._parse_name(parts[1], name, line)

        # Otherwise treat as class from module
        return IRClassType(name=parts[-1], module=".".join(parts[:-1]))

    def _parse_union(self, elements: list[ast.expr], name: str | None, line: int | None) -> IRType:
        """Parse a union type (X | Y syntax or Union[X, Y])."""
        variants: list[IRType] = []

        for elt in elements:
            if isinstance(elt, ast.BinOp) and isinstance(elt.op, ast.BitOr):
                # Flatten nested unions
                union_type = self._parse_union([elt.left, elt.right], name, line)
                if isinstance(union_type, IRUnionType):
                    variants.extend(union_type.variants)
                else:
                    variants.append(union_type)
            else:
                variants.append(self.parse(elt, name))

        # Check if this is actually Optional (Union with None)
        none_types = [v for v in variants if isinstance(v, IRPrimitiveType) and v.kind == PrimitiveType.NONE]
        other_types = [v for v in variants if not (isinstance(v, IRPrimitiveType) and v.kind == PrimitiveType.NONE)]

        if len(none_types) == 1 and len(other_types) == 1:
            # This is Optional[X]
            return IRGenericType(name="Optional", type_args=other_types)

        return IRUnionType(variants=variants)

    def _parse_tuple_type(self, elements: list[ast.expr], name: str | None, line: int | None) -> IRType:
        """Parse a tuple of types (used in Union, Tuple, etc.)."""
        type_args = [self.parse(elt, name) for elt in elements]
        return IRGenericType(name="Tuple", type_args=type_args)

    def _parse_callable(self, type_args: list[IRType], name: str | None, line: int | None) -> IRType:
        """Parse a Callable type annotation."""
        if len(type_args) < 2:
            raise TypeAnnotationError(
                "Callable requires at least parameter types and return type",
                name=name,
                filename=self.filename,
                line=line,
            )

        # Last arg is return type, first is param types (may be a list)
        param_types = type_args[:-1]
        return_type = type_args[-1]

        return IRFunctionType(param_types=param_types, return_type=return_type)


def parse_type_annotation(
    node: ast.expr | None,
    name: str | None = None,
    filename: str | None = None,
) -> IRType:
    """Convenience function to parse a type annotation.

    Args:
        node: The AST node representing the type annotation
        name: Optional name of the annotated item (for error messages)
        filename: Optional filename for error messages

    Returns:
        The parsed IRType
    """
    parser = TypeParser(filename=filename)
    return parser.parse(node, name)
