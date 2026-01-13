"""Python AST parsing and visitor for spicycrab.

This module provides the primary interface for parsing Python source code
and extracting typed AST information.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from spicycrab.ir.nodes import (
    BinaryOp,
    IRAssign,
    IRAttrAssign,
    IRAttribute,
    IRAwait,
    IRBinaryOp,
    IRBreak,
    IRCall,
    IRClass,
    IRContinue,
    IRDict,
    IRExceptHandler,
    IRExpression,
    IRExprStmt,
    IRFor,
    IRFString,
    IRFunction,
    IRIf,
    IRIfExp,
    IRImport,
    IRList,
    IRListComp,
    IRLiteral,
    IRMethodCall,
    IRModule,
    IRName,
    IRParameter,
    IRPass,
    IRPrimitiveType,
    IRRaise,
    IRReturn,
    IRSet,
    IRStatement,
    IRSubscript,
    IRTry,
    IRTuple,
    IRTupleUnpack,
    IRType,
    IRUnaryOp,
    IRWhile,
    IRWith,
    PrimitiveType,
    UnaryOp,
)
from spicycrab.parser.type_parser import TypeParser
from spicycrab.utils.errors import ParseError, TypeAnnotationError, UnsupportedFeatureError

# Mapping from Python AST binary operators to IR operators
BINOP_MAP: dict[type, BinaryOp] = {
    ast.Add: BinaryOp.ADD,
    ast.Sub: BinaryOp.SUB,
    ast.Mult: BinaryOp.MUL,
    ast.Div: BinaryOp.DIV,
    ast.FloorDiv: BinaryOp.FLOOR_DIV,
    ast.Mod: BinaryOp.MOD,
    ast.Pow: BinaryOp.POW,
    ast.BitAnd: BinaryOp.BIT_AND,
    ast.BitOr: BinaryOp.BIT_OR,
    ast.BitXor: BinaryOp.BIT_XOR,
    ast.LShift: BinaryOp.LSHIFT,
    ast.RShift: BinaryOp.RSHIFT,
}

CMPOP_MAP: dict[type, BinaryOp] = {
    ast.Eq: BinaryOp.EQ,
    ast.NotEq: BinaryOp.NE,
    ast.Lt: BinaryOp.LT,
    ast.LtE: BinaryOp.LE,
    ast.Gt: BinaryOp.GT,
    ast.GtE: BinaryOp.GE,
    ast.In: BinaryOp.IN,
    ast.NotIn: BinaryOp.NOT_IN,
    ast.Is: BinaryOp.IS,
    ast.IsNot: BinaryOp.IS_NOT,
}

BOOLOP_MAP: dict[type, BinaryOp] = {
    ast.And: BinaryOp.AND,
    ast.Or: BinaryOp.OR,
}

UNARYOP_MAP: dict[type, UnaryOp] = {
    ast.UAdd: UnaryOp.POS,
    ast.USub: UnaryOp.NEG,
    ast.Not: UnaryOp.NOT,
    ast.Invert: UnaryOp.BIT_NOT,
}


@dataclass
class SymbolInfo:
    """Information about a symbol in the symbol table."""

    name: str
    type: IRType | None = None
    is_mutable: bool = False
    is_parameter: bool = False
    line: int | None = None


@dataclass
class Scope:
    """A scope in the symbol table."""

    symbols: dict[str, SymbolInfo] = field(default_factory=dict)
    parent: Scope | None = None

    def lookup(self, name: str) -> SymbolInfo | None:
        """Look up a symbol in this scope or parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def define(self, info: SymbolInfo) -> None:
        """Define a symbol in this scope."""
        self.symbols[info.name] = info


class PythonASTVisitor(ast.NodeVisitor):
    """Visitor that converts Python AST to crabpy IR.

    This visitor traverses a Python AST and builds an intermediate
    representation suitable for Rust code generation.
    """

    def __init__(self, filename: str | None = None, source_lines: list[str] | None = None) -> None:
        self.filename = filename
        self.source_lines = source_lines or []
        self.type_parser = TypeParser(filename=filename)
        self.current_scope: Scope = Scope()
        self.scope_stack: list[Scope] = []

    def _extract_rust_attributes(self, node_lineno: int) -> list[str]:
        """Extract passthrough Rust attributes from comments preceding a node.

        Comments starting with '# #[' are treated as Rust attribute passthrough.
        The '# ' prefix is stripped, leaving the raw Rust attribute.

        Example:
            # #[derive(Serialize, Deserialize)]
            # #[serde(rename_all = "camelCase")]
            @dataclass
            class Foo:
                pass

        Returns: ['#[derive(Serialize, Deserialize)]', '#[serde(rename_all = "camelCase")]']
        """
        if not self.source_lines:
            return []

        attrs: list[str] = []
        line_idx = node_lineno - 2  # 0-indexed, look at line before the node

        while line_idx >= 0:
            line = self.source_lines[line_idx].strip()
            if line.startswith("# #["):
                # Strip "# " prefix, keep the #[...]
                attrs.insert(0, line[2:])  # "# #[derive...]" -> "#[derive...]"
                line_idx -= 1
            elif line.startswith("#") or line == "" or line.startswith("@"):
                # Skip regular comments, blank lines, and Python decorators
                line_idx -= 1
            else:
                # Hit non-comment/non-decorator code, stop
                break

        return attrs

    def _push_scope(self) -> None:
        """Push a new scope onto the stack."""
        self.scope_stack.append(self.current_scope)
        self.current_scope = Scope(parent=self.current_scope)

    def _pop_scope(self) -> None:
        """Pop the current scope from the stack."""
        if self.scope_stack:
            self.current_scope = self.scope_stack.pop()

    def _error(self, message: str, node: ast.AST | None = None) -> ParseError:
        """Create a parse error with location info."""
        line = getattr(node, "lineno", None) if node else None
        return ParseError(message, filename=self.filename, line=line)

    def _unsupported(
        self, feature: str, node: ast.AST | None = None, suggestion: str | None = None
    ) -> UnsupportedFeatureError:
        """Create an unsupported feature error."""
        line = getattr(node, "lineno", None) if node else None
        return UnsupportedFeatureError(feature, filename=self.filename, line=line, suggestion=suggestion)

    def visit_Module(self, node: ast.Module) -> IRModule:
        """Visit a module (top-level file)."""
        imports: list[IRImport] = []
        functions: list[IRFunction] = []
        classes: list[IRClass] = []
        statements: list[IRStatement] = []
        docstring: str | None = None

        for i, child in enumerate(node.body):
            # Check for module docstring
            if i == 0 and isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
                if isinstance(child.value.value, str):
                    docstring = child.value.value
                    continue

            if isinstance(child, ast.Import):
                imports.append(self._visit_import(child))
            elif isinstance(child, ast.ImportFrom):
                imports.append(self._visit_import_from(child))
            elif isinstance(child, ast.FunctionDef):
                functions.append(self.visit_FunctionDef(child))
            elif isinstance(child, ast.AsyncFunctionDef):
                functions.append(self.visit_AsyncFunctionDef(child))
            elif isinstance(child, ast.ClassDef):
                classes.append(self.visit_ClassDef(child))
            else:
                stmt = self._visit_statement(child)
                if stmt:
                    statements.append(stmt)

        module_name = Path(self.filename).stem if self.filename else "module"
        return IRModule(
            name=module_name,
            imports=imports,
            functions=functions,
            classes=classes,
            statements=statements,
            docstring=docstring,
        )

    def _visit_import(self, node: ast.Import) -> IRImport:
        """Visit an import statement."""
        names = [(alias.name, alias.asname) for alias in node.names]
        return IRImport(
            module=names[0][0] if len(names) == 1 else "",
            names=names,
            line=node.lineno,
        )

    def _visit_import_from(self, node: ast.ImportFrom) -> IRImport:
        """Visit a from...import statement."""
        module = node.module or ""
        names = [(alias.name, alias.asname) for alias in node.names]
        return IRImport(module=module, names=names, line=node.lineno)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> IRFunction:
        """Visit a function definition."""
        self._push_scope()

        # Extract passthrough Rust attributes from preceding comments
        rust_attrs = self._extract_rust_attributes(node.lineno)

        # Parse parameters with type annotations
        params = self._parse_parameters(node.args, node)

        # Parse return type
        return_type: IRType | None = None
        if node.returns:
            return_type = self.type_parser.parse(node.returns, f"{node.name} return")

        # Parse body
        body: list[IRStatement] = []
        docstring: str | None = None

        for i, stmt in enumerate(node.body):
            # Check for docstring
            if i == 0 and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if isinstance(stmt.value.value, str):
                    docstring = stmt.value.value
                    continue

            ir_stmt = self._visit_statement(stmt)
            if ir_stmt:
                body.append(ir_stmt)

        # Analyze mutability - mark variables that are reassigned as mutable
        self._analyze_mutability(body)

        self._pop_scope()

        return IRFunction(
            name=node.name,
            params=params,
            return_type=return_type,
            body=body,
            docstring=docstring,
            line=node.lineno,
            rust_attributes=rust_attrs,
        )

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> IRFunction:
        """Visit an async function definition."""
        self._push_scope()

        # Extract passthrough Rust attributes from preceding comments
        rust_attrs = self._extract_rust_attributes(node.lineno)

        # Parse parameters with type annotations
        params = self._parse_parameters(node.args, node)

        # Parse return type
        return_type: IRType | None = None
        if node.returns:
            return_type = self.type_parser.parse(node.returns, f"{node.name} return")

        # Parse body
        body: list[IRStatement] = []
        docstring: str | None = None

        for i, stmt in enumerate(node.body):
            # Check for docstring
            if i == 0 and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if isinstance(stmt.value.value, str):
                    docstring = stmt.value.value
                    continue

            ir_stmt = self._visit_statement(stmt)
            if ir_stmt:
                body.append(ir_stmt)

        # Analyze mutability - mark variables that are reassigned as mutable
        self._analyze_mutability(body)

        self._pop_scope()

        return IRFunction(
            name=node.name,
            params=params,
            return_type=return_type,
            body=body,
            is_async=True,  # Mark as async
            docstring=docstring,
            line=node.lineno,
            rust_attributes=rust_attrs,
        )

    def _analyze_mutability(self, body: list[IRStatement]) -> None:
        """Analyze statements to detect mutable variables and mark their declarations."""
        # First pass: find all variable assignments
        declarations: dict[str, IRAssign] = {}  # name -> declaration statement
        tuple_declarations: dict[str, IRTupleUnpack] = {}  # name -> tuple unpack statement
        tuple_target_index: dict[str, int] = {}  # name -> index in tuple
        reassigned: set[str] = set()  # names that are reassigned or mutated

        # Methods that mutate their receiver
        mutating_methods = {
            "append",
            "push",
            "extend",
            "insert",
            "pop",
            "remove",
            "clear",
            "sort",
            "reverse",
            "increment",
            "decrement",
            "update",
            "add",
            "discard",
            # Async channel methods that require &mut self
            "recv",
            "recv_many",
            "try_recv",
        }
        # Methods starting with these prefixes are also considered mutating
        mutating_prefixes = ("set_", "remove_", "add_")

        def scan_statements(stmts: list[IRStatement]) -> None:
            for stmt in stmts:
                if isinstance(stmt, IRAssign):
                    if stmt.is_declaration:
                        declarations[stmt.target] = stmt
                    else:
                        # This is a reassignment
                        reassigned.add(stmt.target)
                    # Also check for mutating calls in the assignment value
                    if stmt.value:
                        self._check_mutating_call(stmt.value, reassigned, mutating_methods, mutating_prefixes)
                elif isinstance(stmt, IRTupleUnpack):
                    # Track tuple unpacking declarations
                    for i, target in enumerate(stmt.targets):
                        tuple_declarations[target] = stmt
                        tuple_target_index[target] = i

                # Check for method calls that mutate their receiver
                if isinstance(stmt, IRExprStmt):
                    self._check_mutating_call(stmt.expr, reassigned, mutating_methods, mutating_prefixes)

                # Recurse into nested blocks
                if isinstance(stmt, IRIf):
                    scan_statements(stmt.then_body)
                    scan_statements(stmt.else_body)
                elif isinstance(stmt, IRFor):
                    scan_statements(stmt.body)
                elif isinstance(stmt, IRWhile):
                    scan_statements(stmt.body)
                elif isinstance(stmt, IRWith):
                    scan_statements(stmt.body)
                elif isinstance(stmt, IRTry):
                    scan_statements(stmt.body)
                    scan_statements(stmt.finally_body)
                    for handler in stmt.handlers:
                        scan_statements(handler.body)

        scan_statements(body)

        # Mark declarations of reassigned variables as mutable
        for name in reassigned:
            if name in declarations:
                declarations[name].is_mutable = True
            elif name in tuple_declarations:
                # Mark the specific target in tuple unpacking as mutable
                stmt = tuple_declarations[name]
                idx = tuple_target_index[name]
                # Initialize is_mutable list if needed
                while len(stmt.is_mutable) < len(stmt.targets):
                    stmt.is_mutable.append(False)
                stmt.is_mutable[idx] = True

    def _check_mutating_call(
        self,
        expr: IRExpression,
        reassigned: set[str],
        mutating_methods: set[str],
        mutating_prefixes: tuple[str, ...] = ("set_", "remove_", "add_"),
    ) -> None:
        """Check if expression contains a mutating method call and mark the target as reassigned."""
        if isinstance(expr, IRMethodCall):
            # Check for exact method name match or prefix match
            is_mutating = expr.method in mutating_methods or any(
                expr.method.startswith(prefix) for prefix in mutating_prefixes
            )
            if is_mutating:
                # Get the receiver name
                if isinstance(expr.obj, IRName):
                    reassigned.add(expr.obj.name)
        elif isinstance(expr, IRCall):
            # Check args for nested method calls
            for arg in expr.args:
                self._check_mutating_call(arg, reassigned, mutating_methods, mutating_prefixes)
        elif isinstance(expr, IRAwait):
            # Check the awaited expression (e.g., await rx.recv())
            if expr.value:
                self._check_mutating_call(expr.value, reassigned, mutating_methods, mutating_prefixes)

    def _parse_parameters(self, args: ast.arguments, func_node: ast.FunctionDef) -> list[IRParameter]:
        """Parse function parameters with their type annotations."""
        params: list[IRParameter] = []

        # Regular positional/keyword args
        num_defaults = len(args.defaults)
        num_args = len(args.args)
        default_offset = num_args - num_defaults

        for i, arg in enumerate(args.args):
            # Skip 'self' for methods
            if arg.arg == "self":
                continue

            if arg.annotation is None:
                raise TypeAnnotationError(
                    "Missing type annotation for parameter",
                    name=arg.arg,
                    filename=self.filename,
                    line=arg.lineno,
                )

            param_type = self.type_parser.parse(arg.annotation, arg.arg)

            # Get default value if any
            default: IRExpression | None = None
            default_idx = i - default_offset
            if default_idx >= 0 and default_idx < num_defaults:
                default = self._visit_expression(args.defaults[default_idx])

            params.append(
                IRParameter(
                    name=arg.arg,
                    type=param_type,
                    default=default,
                )
            )

            # Add to scope
            self.current_scope.define(
                SymbolInfo(
                    name=arg.arg,
                    type=param_type,
                    is_parameter=True,
                    line=arg.lineno,
                )
            )

        # *args
        if args.vararg:
            if args.vararg.annotation is None:
                raise TypeAnnotationError(
                    "Missing type annotation for *args",
                    name=args.vararg.arg,
                    filename=self.filename,
                    line=args.vararg.lineno,
                )
            params.append(
                IRParameter(
                    name=args.vararg.arg,
                    type=self.type_parser.parse(args.vararg.annotation, args.vararg.arg),
                    is_args=True,
                )
            )

        # **kwargs
        if args.kwarg:
            if args.kwarg.annotation is None:
                raise TypeAnnotationError(
                    "Missing type annotation for **kwargs",
                    name=args.kwarg.arg,
                    filename=self.filename,
                    line=args.kwarg.lineno,
                )
            params.append(
                IRParameter(
                    name=args.kwarg.arg,
                    type=self.type_parser.parse(args.kwarg.annotation, args.kwarg.arg),
                    is_kwargs=True,
                )
            )

        return params

    def visit_ClassDef(self, node: ast.ClassDef) -> IRClass:
        """Visit a class definition."""
        self._push_scope()

        # Extract passthrough Rust attributes from preceding comments
        rust_attrs = self._extract_rust_attributes(node.lineno)

        # Check for dataclass decorator
        is_dataclass = any(
            (isinstance(d, ast.Name) and d.id == "dataclass")
            or (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass")
            for d in node.decorator_list
        )

        # Parse base classes
        bases: list[str] = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)

        # Parse class body
        fields: list[tuple[str, IRType]] = []
        methods: list[IRFunction] = []
        docstring: str | None = None
        has_enter = False
        has_exit = False
        init_method: ast.FunctionDef | None = None

        for i, item in enumerate(node.body):
            # Check for docstring
            if i == 0 and isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant):
                if isinstance(item.value.value, str):
                    docstring = item.value.value
                    continue

            if isinstance(item, ast.AnnAssign):
                # Class field with annotation (dataclass style)
                if isinstance(item.target, ast.Name):
                    if item.annotation is None:
                        raise TypeAnnotationError(
                            "Missing type annotation for class field",
                            name=item.target.id,
                            filename=self.filename,
                            line=item.lineno,
                        )
                    field_type = self.type_parser.parse(item.annotation, item.target.id)
                    fields.append((item.target.id, field_type))

            elif isinstance(item, ast.FunctionDef):
                # Save __init__ for field extraction
                if item.name == "__init__":
                    init_method = item

                method = self.visit_FunctionDef(item)
                method.is_method = True

                # Detect if method modifies self (needs &mut self)
                if item.name != "__init__":
                    method.modifies_self = self._method_modifies_self(item)

                methods.append(method)

                if item.name == "__enter__":
                    has_enter = True
                elif item.name == "__exit__":
                    has_exit = True

        # For non-dataclass classes, extract fields from __init__
        if not is_dataclass and init_method and not fields:
            fields = self._extract_fields_from_init(init_method)

        self._pop_scope()

        return IRClass(
            name=node.name,
            bases=bases,
            fields=fields,
            methods=methods,
            is_dataclass=is_dataclass,
            docstring=docstring,
            has_enter=has_enter,
            has_exit=has_exit,
            line=node.lineno,
            rust_attributes=rust_attrs,
        )

    def _extract_fields_from_init(self, init_method: ast.FunctionDef) -> list[tuple[str, IRType]]:
        """Extract fields from __init__ method's self.x = x assignments."""
        fields: list[tuple[str, IRType]] = []
        param_types: dict[str, IRType] = {}

        # Build a map of parameter names to their types
        for arg in init_method.args.args:
            if arg.arg == "self":
                continue
            if arg.annotation:
                param_types[arg.arg] = self.type_parser.parse(arg.annotation, arg.arg)

        # Look for self.x = x or self.x = value patterns in __init__ body
        for stmt in init_method.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        field_name = target.attr
                        # Try to get type from corresponding parameter
                        if isinstance(stmt.value, ast.Name) and stmt.value.id in param_types:
                            fields.append((field_name, param_types[stmt.value.id]))
                        elif field_name in param_types:
                            fields.append((field_name, param_types[field_name]))
                        else:
                            # Infer type from literal value
                            inferred = self._infer_type_from_value(stmt.value)
                            fields.append((field_name, inferred))

            # Handle annotated assignment: self.x: Type = value
            elif isinstance(stmt, ast.AnnAssign):
                if (
                    isinstance(stmt.target, ast.Attribute)
                    and isinstance(stmt.target.value, ast.Name)
                    and stmt.target.value.id == "self"
                ):
                    field_name = stmt.target.attr
                    # Use the explicit type annotation
                    field_type = self.type_parser.parse(stmt.annotation, field_name)
                    fields.append((field_name, field_type))

        return fields

    def _infer_type_from_value(self, value: ast.expr) -> IRType:
        """Infer type from a literal value."""
        if isinstance(value, ast.Constant):
            if isinstance(value.value, str):
                return IRPrimitiveType(kind=PrimitiveType.STR)
            if isinstance(value.value, int) and not isinstance(value.value, bool):
                return IRPrimitiveType(kind=PrimitiveType.INT)
            if isinstance(value.value, float):
                return IRPrimitiveType(kind=PrimitiveType.FLOAT)
            if isinstance(value.value, bool):
                return IRPrimitiveType(kind=PrimitiveType.BOOL)
            if value.value is None:
                return IRPrimitiveType(kind=PrimitiveType.NONE)
        if isinstance(value, ast.List):
            return IRPrimitiveType(kind=PrimitiveType.INT)  # Default list element type
        if isinstance(value, ast.Dict):
            return IRPrimitiveType(kind=PrimitiveType.INT)  # Default dict type
        # Default fallback
        return IRPrimitiveType(kind=PrimitiveType.INT)

    def _method_modifies_self(self, method: ast.FunctionDef) -> bool:
        """Check if a method modifies self (needs &mut self)."""
        for stmt in ast.walk(method):
            # Check for self.x = ... assignments
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "self"
                    ):
                        return True
            # Check for augmented assignments like self.x += 1
            if isinstance(stmt, ast.AugAssign):
                if (
                    isinstance(stmt.target, ast.Attribute)
                    and isinstance(stmt.target.value, ast.Name)
                    and stmt.target.value.id == "self"
                ):
                    return True
        return False

    def _visit_statement(self, node: ast.stmt) -> IRStatement | None:
        """Visit a statement node."""
        line = node.lineno

        if isinstance(node, ast.Assign):
            return self._visit_assign(node)
        elif isinstance(node, ast.AnnAssign):
            return self._visit_ann_assign(node)
        elif isinstance(node, ast.AugAssign):
            return self._visit_aug_assign(node)
        elif isinstance(node, ast.Return):
            value = self._visit_expression(node.value) if node.value else None
            return IRReturn(value=value, line=line)
        elif isinstance(node, ast.If):
            return self._visit_if(node)
        elif isinstance(node, ast.While):
            return self._visit_while(node)
        elif isinstance(node, ast.For):
            return self._visit_for(node)
        elif isinstance(node, ast.Break):
            return IRBreak(line=line)
        elif isinstance(node, ast.Continue):
            return IRContinue(line=line)
        elif isinstance(node, ast.Pass):
            return IRPass(line=line)
        elif isinstance(node, ast.Expr):
            expr = self._visit_expression(node.value)
            return IRExprStmt(expr=expr, line=line)
        elif isinstance(node, ast.With):
            return self._visit_with(node)
        elif isinstance(node, ast.Try):
            return self._visit_try(node)
        elif isinstance(node, ast.Raise):
            exc = self._visit_expression(node.exc) if node.exc else None
            return IRRaise(exc=exc, line=line)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            # Imports at statement level are handled elsewhere
            return None
        elif isinstance(node, ast.FunctionDef):
            # Nested function - not supported
            raise self._unsupported("nested functions", node)
        elif isinstance(node, ast.ClassDef):
            # Nested class - not supported
            raise self._unsupported("nested classes", node)
        else:
            raise self._unsupported(f"statement type {type(node).__name__}", node)

    def _visit_assign(self, node: ast.Assign) -> IRStatement:
        """Visit an assignment statement (without type annotation)."""
        if len(node.targets) != 1:
            raise self._unsupported("multiple assignment targets", node)

        target = node.targets[0]
        value = self._visit_expression(node.value)

        # Handle attribute assignment (e.g., self.x = value)
        if isinstance(target, ast.Attribute):
            return IRAttrAssign(
                obj=self._visit_expression(target.value),
                attr=target.attr,
                value=value,
                line=node.lineno,
            )

        # Handle tuple unpacking (e.g., tx, rx = channel())
        if isinstance(target, ast.Tuple):
            targets: list[str] = []
            for elt in target.elts:
                if not isinstance(elt, ast.Name):
                    raise self._unsupported("complex tuple unpacking targets", node)
                targets.append(elt.id)
                # Define each variable in scope
                if self.current_scope.lookup(elt.id) is None:
                    self.current_scope.define(
                        SymbolInfo(
                            name=elt.id,
                            is_mutable=False,
                            line=node.lineno,
                        )
                    )
            return IRTupleUnpack(
                targets=targets,
                value=value,
                is_declaration=True,
                line=node.lineno,
            )

        if not isinstance(target, ast.Name):
            raise self._unsupported("complex assignment targets", node)

        # Check if this is a new declaration or reassignment
        existing = self.current_scope.lookup(target.id)
        is_declaration = existing is None

        if is_declaration:
            # For untyped assignments, we'll need type inference later
            self.current_scope.define(
                SymbolInfo(
                    name=target.id,
                    is_mutable=False,  # Default to immutable, will be fixed by mutability analysis
                    line=node.lineno,
                )
            )

        return IRAssign(
            target=target.id,
            value=value,
            is_declaration=is_declaration,
            is_mutable=False,  # Default to immutable
            line=node.lineno,
        )

    def _visit_ann_assign(self, node: ast.AnnAssign) -> IRStatement:
        """Visit an annotated assignment statement."""
        # Handle attribute assignment: self.attr: Type = value
        if isinstance(node.target, ast.Attribute):
            obj = self._visit_expression(node.target.value)
            attr_name = node.target.attr
            type_annotation = self.type_parser.parse(node.annotation, attr_name)

            value: IRExpression | None = None
            if node.value:
                value = self._visit_expression(node.value)

            return IRAttrAssign(
                obj=obj,
                attr=attr_name,
                value=value if value else IRLiteral(value=None),
                type_annotation=type_annotation,
                line=node.lineno,
            )

        if not isinstance(node.target, ast.Name):
            raise self._unsupported("complex annotated assignment targets", node)

        target_name = node.target.id
        type_annotation = self.type_parser.parse(node.annotation, target_name)

        value = None
        if node.value:
            value = self._visit_expression(node.value)

        # Define in scope
        self.current_scope.define(
            SymbolInfo(
                name=target_name,
                type=type_annotation,
                is_mutable=False,  # Default to immutable
                line=node.lineno,
            )
        )

        return IRAssign(
            target=target_name,
            value=value if value else IRLiteral(value=None),
            type_annotation=type_annotation,
            is_declaration=True,
            is_mutable=False,  # Default to immutable
            line=node.lineno,
        )

    def _visit_aug_assign(self, node: ast.AugAssign) -> IRStatement:
        """Visit an augmented assignment (+=, -=, etc.)."""
        op_type = type(node.op)

        if op_type not in BINOP_MAP:
            raise self._unsupported(f"augmented assignment operator {op_type.__name__}", node)

        right = self._visit_expression(node.value)

        # Handle attribute augmented assignment (e.g., self.x += value)
        if isinstance(node.target, ast.Attribute):
            obj = self._visit_expression(node.target.value)
            left = IRAttribute(obj=obj, attr=node.target.attr)
            value = IRBinaryOp(op=BINOP_MAP[op_type], left=left, right=right)
            return IRAttrAssign(
                obj=obj,
                attr=node.target.attr,
                value=value,
                line=node.lineno,
            )

        if not isinstance(node.target, ast.Name):
            raise self._unsupported("complex augmented assignment targets", node)

        target_name = node.target.id

        # Convert x += y to x = x + y
        left = IRName(name=target_name)
        value = IRBinaryOp(op=BINOP_MAP[op_type], left=left, right=right)

        return IRAssign(
            target=target_name,
            value=value,
            is_declaration=False,
            is_mutable=True,
            line=node.lineno,
        )

    def _visit_if(self, node: ast.If) -> IRIf:
        """Visit an if statement."""
        condition = self._visit_expression(node.test)
        # Visit each statement only once to avoid double-definition in scope tracking
        then_body = []
        for s in node.body:
            ir_stmt = self._visit_statement(s)
            if ir_stmt:
                then_body.append(ir_stmt)

        elif_clauses: list[tuple[IRExpression, list[IRStatement]]] = []
        else_body: list[IRStatement] = []

        # Process elif/else chain
        current_else = node.orelse
        while current_else:
            if len(current_else) == 1 and isinstance(current_else[0], ast.If):
                # This is an elif
                elif_node = current_else[0]
                elif_cond = self._visit_expression(elif_node.test)
                # Visit each statement only once
                elif_body = []
                for s in elif_node.body:
                    ir_stmt = self._visit_statement(s)
                    if ir_stmt:
                        elif_body.append(ir_stmt)
                elif_clauses.append((elif_cond, elif_body))
                current_else = elif_node.orelse
            else:
                # This is the final else - visit each statement only once
                for s in current_else:
                    ir_stmt = self._visit_statement(s)
                    if ir_stmt:
                        else_body.append(ir_stmt)
                break

        return IRIf(
            condition=condition,
            then_body=then_body,
            elif_clauses=elif_clauses,
            else_body=else_body,
            line=node.lineno,
        )

    def _visit_while(self, node: ast.While) -> IRWhile:
        """Visit a while loop."""
        condition = self._visit_expression(node.test)
        # Visit each statement only once to avoid double-definition in scope tracking
        body = []
        for s in node.body:
            ir_stmt = self._visit_statement(s)
            if ir_stmt:
                body.append(ir_stmt)
        return IRWhile(
            condition=condition,
            body=body,
            line=node.lineno,
        )

    def _visit_for(self, node: ast.For) -> IRFor:
        """Visit a for loop."""
        if not isinstance(node.target, ast.Name):
            raise self._unsupported("complex for loop targets (use simple variable)", node)

        target = node.target.id
        iter_expr = self._visit_expression(node.iter)
        # Visit each statement only once to avoid double-definition in scope tracking
        body = []
        for s in node.body:
            ir_stmt = self._visit_statement(s)
            if ir_stmt:
                body.append(ir_stmt)

        return IRFor(
            target=target,
            iter=iter_expr,
            body=body,
            line=node.lineno,
        )

    def _visit_with(self, node: ast.With) -> IRWith:
        """Visit a with statement."""
        if len(node.items) != 1:
            raise self._unsupported("multiple context managers in single with", node)

        item = node.items[0]
        context = self._visit_expression(item.context_expr)

        target: str | None = None
        if item.optional_vars:
            if not isinstance(item.optional_vars, ast.Name):
                raise self._unsupported("complex with target", node)
            target = item.optional_vars.id

        # Visit each statement only once to avoid double-definition in scope tracking
        body = []
        for s in node.body:
            ir_stmt = self._visit_statement(s)
            if ir_stmt:
                body.append(ir_stmt)

        return IRWith(
            context=context,
            target=target,
            body=body,
            line=node.lineno,
        )

    def _visit_try(self, node: ast.Try) -> IRTry:
        """Visit a try statement."""
        # Visit each statement only once to avoid double-definition in scope tracking
        body = []
        for s in node.body:
            ir_stmt = self._visit_statement(s)
            if ir_stmt:
                body.append(ir_stmt)

        handlers: list[IRExceptHandler] = []
        for handler in node.handlers:
            exc_type: str | None = None
            if handler.type:
                if isinstance(handler.type, ast.Name):
                    exc_type = handler.type.id
                elif isinstance(handler.type, ast.Attribute):
                    exc_type = handler.type.attr

            # Visit each statement only once
            handler_body = []
            for s in handler.body:
                ir_stmt = self._visit_statement(s)
                if ir_stmt:
                    handler_body.append(ir_stmt)
            handlers.append(
                IRExceptHandler(
                    exc_type=exc_type,
                    name=handler.name,
                    body=handler_body,
                )
            )

        # Visit each statement only once
        finally_body = []
        for s in node.finalbody:
            ir_stmt = self._visit_statement(s)
            if ir_stmt:
                finally_body.append(ir_stmt)

        return IRTry(
            body=body,
            handlers=handlers,
            finally_body=finally_body,
            line=node.lineno,
        )

    def _visit_expression(self, node: ast.expr) -> IRExpression:
        """Visit an expression node."""
        line = node.lineno

        if isinstance(node, ast.Constant):
            return IRLiteral(value=node.value, line=line)

        elif isinstance(node, ast.Name):
            return IRName(name=node.id, line=line)

        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in BINOP_MAP:
                raise self._unsupported(f"binary operator {op_type.__name__}", node)
            return IRBinaryOp(
                op=BINOP_MAP[op_type],
                left=self._visit_expression(node.left),
                right=self._visit_expression(node.right),
                line=line,
            )

        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in UNARYOP_MAP:
                raise self._unsupported(f"unary operator {op_type.__name__}", node)
            return IRUnaryOp(
                op=UNARYOP_MAP[op_type],
                operand=self._visit_expression(node.operand),
                line=line,
            )

        elif isinstance(node, ast.Compare):
            return self._visit_compare(node)

        elif isinstance(node, ast.BoolOp):
            return self._visit_boolop(node)

        elif isinstance(node, ast.Call):
            return self._visit_call(node)

        elif isinstance(node, ast.Attribute):
            return IRAttribute(
                obj=self._visit_expression(node.value),
                attr=node.attr,
                line=line,
            )

        elif isinstance(node, ast.Subscript):
            return IRSubscript(
                obj=self._visit_expression(node.value),
                index=self._visit_expression(node.slice),
                line=line,
            )

        elif isinstance(node, ast.List):
            return IRList(
                elements=[self._visit_expression(e) for e in node.elts],
                line=line,
            )

        elif isinstance(node, ast.Dict):
            keys = [self._visit_expression(k) if k else IRLiteral(value=None) for k in node.keys]
            values = [self._visit_expression(v) for v in node.values]
            return IRDict(keys=keys, values=values, line=line)

        elif isinstance(node, ast.Set):
            return IRSet(
                elements=[self._visit_expression(e) for e in node.elts],
                line=line,
            )

        elif isinstance(node, ast.Tuple):
            return IRTuple(
                elements=[self._visit_expression(e) for e in node.elts],
                line=line,
            )

        elif isinstance(node, ast.IfExp):
            return IRIfExp(
                condition=self._visit_expression(node.test),
                then_expr=self._visit_expression(node.body),
                else_expr=self._visit_expression(node.orelse),
                line=line,
            )

        elif isinstance(node, ast.ListComp):
            if len(node.generators) != 1:
                raise self._unsupported("multiple generators in list comprehension", node)
            gen = node.generators[0]
            if not isinstance(gen.target, ast.Name):
                raise self._unsupported("complex comprehension target", node)
            return IRListComp(
                element=self._visit_expression(node.elt),
                target=gen.target.id,
                iter=self._visit_expression(gen.iter),
                conditions=[self._visit_expression(c) for c in gen.ifs],
                line=line,
            )

        elif isinstance(node, ast.JoinedStr):
            # f-string
            return self._visit_fstring(node)

        elif isinstance(node, ast.FormattedValue):
            # Part of an f-string - just visit the value
            return self._visit_expression(node.value)

        elif isinstance(node, ast.Await):
            # Await expression for async code
            return IRAwait(
                value=self._visit_expression(node.value),
                line=line,
            )

        else:
            raise self._unsupported(f"expression type {type(node).__name__}", node)

    def _visit_fstring(self, node: ast.JoinedStr) -> IRFString:
        """Visit an f-string."""
        parts: list[IRExpression] = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                # String literal part
                parts.append(IRLiteral(value=value.value, line=node.lineno))
            elif isinstance(value, ast.FormattedValue):
                # Expression part
                parts.append(self._visit_expression(value.value))
            else:
                parts.append(self._visit_expression(value))
        return IRFString(parts=parts, line=node.lineno)

    def _visit_compare(self, node: ast.Compare) -> IRExpression:
        """Visit a comparison expression."""
        # Handle chained comparisons: a < b < c becomes (a < b) and (b < c)
        left = self._visit_expression(node.left)

        if len(node.ops) == 1:
            op_type = type(node.ops[0])
            if op_type not in CMPOP_MAP:
                raise self._unsupported(f"comparison operator {op_type.__name__}", node)
            return IRBinaryOp(
                op=CMPOP_MAP[op_type],
                left=left,
                right=self._visit_expression(node.comparators[0]),
                line=node.lineno,
            )

        # Chained comparison
        comparisons: list[IRExpression] = []
        current_left = left
        for op, comparator in zip(node.ops, node.comparators):
            op_type = type(op)
            if op_type not in CMPOP_MAP:
                raise self._unsupported(f"comparison operator {op_type.__name__}", node)
            right = self._visit_expression(comparator)
            comparisons.append(
                IRBinaryOp(
                    op=CMPOP_MAP[op_type],
                    left=current_left,
                    right=right,
                    line=node.lineno,
                )
            )
            current_left = right

        # Combine with AND
        result = comparisons[0]
        for comp in comparisons[1:]:
            result = IRBinaryOp(op=BinaryOp.AND, left=result, right=comp, line=node.lineno)
        return result

    def _visit_boolop(self, node: ast.BoolOp) -> IRExpression:
        """Visit a boolean operation (and/or)."""
        op_type = type(node.op)
        if op_type not in BOOLOP_MAP:
            raise self._unsupported(f"boolean operator {op_type.__name__}", node)

        op = BOOLOP_MAP[op_type]
        values = [self._visit_expression(v) for v in node.values]

        result = values[0]
        for value in values[1:]:
            result = IRBinaryOp(op=op, left=result, right=value, line=node.lineno)
        return result

    def _visit_call(self, node: ast.Call) -> IRExpression:
        """Visit a function/method call."""
        args = [self._visit_expression(a) for a in node.args]
        kwargs = {kw.arg: self._visit_expression(kw.value) for kw in node.keywords if kw.arg}

        # Check if this is a method call
        if isinstance(node.func, ast.Attribute):
            return IRMethodCall(
                obj=self._visit_expression(node.func.value),
                method=node.func.attr,
                args=args,
                kwargs=kwargs,
                line=node.lineno,
            )

        return IRCall(
            func=self._visit_expression(node.func),
            args=args,
            kwargs=kwargs,
            line=node.lineno,
        )


def parse_source(source: str, filename: str | None = None) -> IRModule:
    """Parse Python source code and return an IR module.

    Args:
        source: The Python source code to parse
        filename: Optional filename for error messages

    Returns:
        The parsed IR module

    Raises:
        ParseError: If the source cannot be parsed
        TypeAnnotationError: If type annotations are missing or invalid
        UnsupportedFeatureError: If unsupported Python features are used
    """
    try:
        tree = ast.parse(source, filename=filename or "<string>")
    except SyntaxError as e:
        raise ParseError(
            f"Syntax error: {e.msg}",
            filename=filename,
            line=e.lineno,
        ) from e

    source_lines = source.splitlines()
    visitor = PythonASTVisitor(filename=filename, source_lines=source_lines)
    return visitor.visit_Module(tree)


def parse_file(filepath: str | Path) -> IRModule:
    """Parse a Python file and return an IR module.

    Args:
        filepath: Path to the Python file to parse

    Returns:
        The parsed IR module

    Raises:
        ParseError: If the file cannot be parsed
        TypeAnnotationError: If type annotations are missing or invalid
        UnsupportedFeatureError: If unsupported Python features are used
        FileNotFoundError: If the file does not exist
    """
    path = Path(filepath)
    source = path.read_text(encoding="utf-8")
    return parse_source(source, filename=str(path))
