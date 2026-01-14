"""Intermediate Representation (IR) node definitions for spicycrab.

The IR serves as a language-agnostic intermediate layer between Python AST
and Rust code generation. All type information is explicit at this level.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class IRNode(ABC):
    """Base class for all IR nodes."""

    @abstractmethod
    def accept(self, visitor: IRVisitor) -> Any:
        """Accept a visitor for traversal."""
        pass


class IRVisitor(ABC):
    """Base visitor for IR traversal."""

    pass


# =============================================================================
# Type System
# =============================================================================


class PrimitiveType(Enum):
    """Primitive types that map directly to Rust."""

    INT = auto()  # i64
    FLOAT = auto()  # f64
    BOOL = auto()  # bool
    STR = auto()  # String
    BYTES = auto()  # Vec<u8>
    NONE = auto()  # ()


@dataclass
class IRType(IRNode):
    """Base class for type representations."""

    def accept(self, visitor: IRVisitor) -> Any:
        return None


@dataclass
class IRPrimitiveType(IRType):
    """A primitive type (int, float, str, bool, None)."""

    kind: PrimitiveType


@dataclass
class IRGenericType(IRType):
    """A generic type like List[T], Dict[K, V], Optional[T]."""

    name: str  # "List", "Dict", "Set", "Optional", "Tuple"
    type_args: list[IRType] = field(default_factory=list)


@dataclass
class IRUnionType(IRType):
    """A Union type that will become a Rust enum."""

    variants: list[IRType] = field(default_factory=list)
    generated_name: str | None = None  # Name for the generated enum


@dataclass
class IRFunctionType(IRType):
    """A callable/function type."""

    param_types: list[IRType] = field(default_factory=list)
    return_type: IRType | None = None


@dataclass
class IRClassType(IRType):
    """A user-defined class type."""

    name: str
    module: str | None = None


# =============================================================================
# Expressions
# =============================================================================


class BinaryOp(Enum):
    """Binary operators."""

    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    FLOOR_DIV = "//"
    MOD = "%"
    POW = "**"
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    AND = "and"
    OR = "or"
    BIT_AND = "&"
    BIT_OR = "|"
    BIT_XOR = "^"
    LSHIFT = "<<"
    RSHIFT = ">>"
    IN = "in"
    NOT_IN = "not in"
    IS = "is"
    IS_NOT = "is not"


class UnaryOp(Enum):
    """Unary operators."""

    NEG = "-"
    POS = "+"
    NOT = "not"
    BIT_NOT = "~"


@dataclass(kw_only=True)
class IRExpression(IRNode):
    """Base class for all expressions."""

    type: IRType | None = field(default=None, kw_only=True)
    line: int | None = field(default=None, kw_only=True)

    def accept(self, visitor: IRVisitor) -> Any:
        return None


@dataclass
class IRLiteral(IRExpression):
    """A literal value (int, float, str, bool, None)."""

    value: int | float | str | bool | None = None


@dataclass
class IRName(IRExpression):
    """A variable or name reference."""

    name: str = ""
    is_mutable: bool = False  # Whether this variable needs `mut`


@dataclass
class IRBinaryOp(IRExpression):
    """A binary operation."""

    op: BinaryOp = BinaryOp.ADD
    left: IRExpression | None = None
    right: IRExpression | None = None


@dataclass
class IRUnaryOp(IRExpression):
    """A unary operation."""

    op: UnaryOp = UnaryOp.NEG
    operand: IRExpression | None = None


@dataclass
class IRCall(IRExpression):
    """A function or method call."""

    func: IRExpression | None = None
    args: list[IRExpression] = field(default_factory=list)
    kwargs: dict[str, IRExpression] = field(default_factory=dict)


@dataclass
class IRMethodCall(IRExpression):
    """A method call on an object."""

    obj: IRExpression | None = None
    method: str = ""
    args: list[IRExpression] = field(default_factory=list)
    kwargs: dict[str, IRExpression] = field(default_factory=dict)


@dataclass
class IRAttribute(IRExpression):
    """Attribute access (obj.attr)."""

    obj: IRExpression | None = None
    attr: str = ""


@dataclass
class IRSubscript(IRExpression):
    """Subscript access (obj[key])."""

    obj: IRExpression | None = None
    index: IRExpression | None = None


@dataclass
class IRSlice(IRExpression):
    """Slice expression for ranges (e.g., s[0:n], s[:n], s[n:])."""

    lower: IRExpression | None = None  # Start index (None means from beginning)
    upper: IRExpression | None = None  # End index (None means to end)
    step: IRExpression | None = None  # Step (rarely used, usually None)


@dataclass
class IRList(IRExpression):
    """A list literal."""

    elements: list[IRExpression] = field(default_factory=list)


@dataclass
class IRDict(IRExpression):
    """A dict literal."""

    keys: list[IRExpression] = field(default_factory=list)
    values: list[IRExpression] = field(default_factory=list)


@dataclass
class IRSet(IRExpression):
    """A set literal."""

    elements: list[IRExpression] = field(default_factory=list)


@dataclass
class IRTuple(IRExpression):
    """A tuple literal."""

    elements: list[IRExpression] = field(default_factory=list)


@dataclass
class IRIfExp(IRExpression):
    """A ternary/conditional expression (x if cond else y)."""

    condition: IRExpression | None = None
    then_expr: IRExpression | None = None
    else_expr: IRExpression | None = None


@dataclass
class IRListComp(IRExpression):
    """A list comprehension."""

    element: IRExpression | None = None
    target: str = ""
    iter: IRExpression | None = None
    conditions: list[IRExpression] = field(default_factory=list)


@dataclass
class IRFormattedValue(IRExpression):
    """A formatted value in an f-string with optional format spec.

    Example: f"{value:x}" has value=IRName("value"), format_spec="x"
    """

    value: IRExpression | None = None
    format_spec: str = ""  # e.g., "x", ".2f", ">10s"


@dataclass
class IRFString(IRExpression):
    """An f-string (formatted string literal).

    Parts is a list of either:
    - IRLiteral (string parts)
    - IRFormattedValue (formatted values with optional format specs)
    - IRExpression (formatted values without format specs)
    """

    parts: list[IRExpression] = field(default_factory=list)


@dataclass
class IRAwait(IRExpression):
    """An await expression for async code."""

    value: IRExpression | None = None


# =============================================================================
# Statements
# =============================================================================


@dataclass(kw_only=True)
class IRStatement(IRNode):
    """Base class for all statements."""

    line: int | None = field(default=None, kw_only=True)

    def accept(self, visitor: IRVisitor) -> Any:
        return None


@dataclass
class IRAssign(IRStatement):
    """Assignment statement to a variable."""

    target: str = ""
    value: IRExpression | None = None
    type_annotation: IRType | None = None
    is_declaration: bool = False  # First assignment (let vs reassignment)
    is_mutable: bool = False


@dataclass
class IRAttrAssign(IRStatement):
    """Assignment to an attribute (obj.attr = value)."""

    obj: IRExpression | None = None
    attr: str = ""
    value: IRExpression | None = None
    type_annotation: IRType | None = None  # For annotated: self.x: int = value


@dataclass
class IRTupleUnpack(IRStatement):
    """Tuple unpacking assignment: (a, b) = expr or a, b = expr.

    Used for patterns like:
        tx, rx = mpsc_channel(10)  -> let (tx, rx) = mpsc_channel(10);
    """

    targets: list[str] = field(default_factory=list)  # Variable names to unpack into
    value: IRExpression | None = None
    type_annotations: list[IRType | None] = field(default_factory=list)  # Optional types for each target
    is_declaration: bool = True  # Tuple unpacking is typically a declaration
    is_mutable: list[bool] = field(default_factory=list)  # Per-target mutability


@dataclass
class IRReturn(IRStatement):
    """Return statement."""

    value: IRExpression | None = None


@dataclass
class IRIf(IRStatement):
    """If statement."""

    condition: IRExpression | None = None
    then_body: list[IRStatement] = field(default_factory=list)
    elif_clauses: list[tuple[IRExpression, list[IRStatement]]] = field(default_factory=list)
    else_body: list[IRStatement] = field(default_factory=list)


@dataclass
class IRWhile(IRStatement):
    """While loop."""

    condition: IRExpression | None = None
    body: list[IRStatement] = field(default_factory=list)


@dataclass
class IRFor(IRStatement):
    """For loop."""

    target: str = ""
    iter: IRExpression | None = None
    body: list[IRStatement] = field(default_factory=list)
    target_type: IRType | None = None


@dataclass
class IRBreak(IRStatement):
    """Break statement."""

    pass


@dataclass
class IRContinue(IRStatement):
    """Continue statement."""

    pass


@dataclass
class IRExprStmt(IRStatement):
    """Expression statement (expression used as statement)."""

    expr: IRExpression | None = None


@dataclass
class IRWith(IRStatement):
    """With statement (context manager)."""

    context: IRExpression | None = None
    target: str | None = None  # The 'as' target
    body: list[IRStatement] = field(default_factory=list)


@dataclass
class IRTry(IRStatement):
    """Try/except/finally statement."""

    body: list[IRStatement] = field(default_factory=list)
    handlers: list[IRExceptHandler] = field(default_factory=list)
    finally_body: list[IRStatement] = field(default_factory=list)


@dataclass
class IRExceptHandler:
    """An except clause."""

    exc_type: str | None = None  # Exception type name
    name: str | None = None  # Bound name (as e)
    body: list[IRStatement] = field(default_factory=list)


@dataclass
class IRRaise(IRStatement):
    """Raise statement."""

    exc: IRExpression | None = None


@dataclass
class IRPass(IRStatement):
    """Pass statement (no-op)."""

    pass


# =============================================================================
# Definitions (Functions, Classes)
# =============================================================================


@dataclass
class IRParameter:
    """A function parameter."""

    name: str
    type: IRType
    default: IRExpression | None = None
    is_args: bool = False  # *args
    is_kwargs: bool = False  # **kwargs


@dataclass
class IRFunction(IRNode):
    """A function definition."""

    name: str
    params: list[IRParameter] = field(default_factory=list)
    return_type: IRType | None = None
    body: list[IRStatement] = field(default_factory=list)
    is_method: bool = False
    is_static: bool = False
    is_classmethod: bool = False
    is_async: bool = False  # True for async functions
    modifies_self: bool = False  # True if method assigns to self.* (needs &mut self)
    docstring: str | None = None
    line: int | None = None
    rust_attributes: list[str] = field(default_factory=list)  # Passthrough # #[...] comments

    def accept(self, visitor: IRVisitor) -> Any:
        return None


@dataclass
class IRClass(IRNode):
    """A class definition."""

    name: str
    bases: list[str] = field(default_factory=list)
    fields: list[tuple[str, IRType]] = field(default_factory=list)  # Instance fields
    methods: list[IRFunction] = field(default_factory=list)
    is_dataclass: bool = False
    docstring: str | None = None
    line: int | None = None
    rust_attributes: list[str] = field(default_factory=list)  # Passthrough # #[...] comments

    # Context manager methods if present
    has_enter: bool = False
    has_exit: bool = False

    def accept(self, visitor: IRVisitor) -> Any:
        return None


@dataclass
class IRImport(IRNode):
    """An import statement."""

    module: str
    names: list[tuple[str, str | None]] = field(default_factory=list)  # (name, alias)
    line: int | None = None

    def accept(self, visitor: IRVisitor) -> Any:
        return None


@dataclass
class IRModule(IRNode):
    """A complete module (file)."""

    name: str
    imports: list[IRImport] = field(default_factory=list)
    functions: list[IRFunction] = field(default_factory=list)
    classes: list[IRClass] = field(default_factory=list)
    statements: list[IRStatement] = field(default_factory=list)  # Top-level statements
    docstring: str | None = None

    def accept(self, visitor: IRVisitor) -> Any:
        return None
