"""Rust code emitter for spicycrab.

Converts IR nodes to Rust source code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from spicycrab.analyzer.type_resolver import TypeResolver
from spicycrab.codegen.stdlib import (
    PATHLIB_MAPPINGS,
    StdlibMapping,
    get_crate_for_python_module,
    get_datetime_mapping,
    get_datetime_method_mapping,
    get_stdlib_mapping,
    get_stub_mapping,
    get_stub_method_mapping,
)
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
    IRClassType,
    IRContinue,
    IRDict,
    IRExpression,
    IRExprStmt,
    IRFor,
    IRFString,
    IRFunction,
    IRGenericType,
    IRIf,
    IRIfExp,
    IRImport,
    IRList,
    IRListComp,
    IRLiteral,
    IRMethodCall,
    IRModule,
    IRName,
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
    IRUnionType,
    IRWhile,
    IRWith,
    PrimitiveType,
    UnaryOp,
)

if TYPE_CHECKING:
    pass


# Binary operator mapping
BINOP_MAP: dict[BinaryOp, str] = {
    BinaryOp.ADD: "+",
    BinaryOp.SUB: "-",
    BinaryOp.MUL: "*",
    BinaryOp.DIV: "/",
    BinaryOp.MOD: "%",
    BinaryOp.EQ: "==",
    BinaryOp.NE: "!=",
    BinaryOp.LT: "<",
    BinaryOp.LE: "<=",
    BinaryOp.GT: ">",
    BinaryOp.GE: ">=",
    BinaryOp.AND: "&&",
    BinaryOp.OR: "||",
    BinaryOp.BIT_AND: "&",
    BinaryOp.BIT_OR: "|",
    BinaryOp.BIT_XOR: "^",
    BinaryOp.LSHIFT: "<<",
    BinaryOp.RSHIFT: ">>",
}

UNARYOP_MAP: dict[UnaryOp, str] = {
    UnaryOp.NEG: "-",
    UnaryOp.POS: "+",
    UnaryOp.NOT: "!",
    UnaryOp.BIT_NOT: "!",
}


@dataclass
class EmitterContext:
    """Context for code emission."""

    indent: int = 0
    in_impl: bool = False
    current_class: str | None = None
    resolver: TypeResolver = field(default_factory=TypeResolver)
    in_last_stmt: bool = False  # True when emitting the last statement in a block
    class_names: set[str] = field(default_factory=set)  # Known class names for constructor detection
    stdlib_imports: set[str] = field(default_factory=set)  # Required stdlib use statements
    local_modules: set[str] = field(default_factory=set)  # Module names in the same project
    local_imports: dict[str, list[tuple[str, str | None]]] = field(default_factory=dict)  # module -> [(name, alias)]
    crate_name: str | None = None  # Crate name for inter-module imports (None uses "crate::")
    # Error handling support
    result_functions: set[str] = field(default_factory=set)  # Functions that return Result
    in_result_context: bool = False  # True when inside a Result-returning function
    in_option_context: bool = False  # True when inside an Option-returning function
    # Type tracking for instance method resolution
    type_env: dict[str, str] = field(default_factory=dict)  # var_name -> type string (e.g., "datetime.datetime")
    # Stub package imports: imported_name -> crate_name (e.g., "Result" -> "anyhow")
    stub_imports: dict[str, str] = field(default_factory=dict)
    # Assignment target type for turbofish inference (e.g., "String" for get_one::<String>)
    assignment_target_type: str | None = None
    # Variables that have been unwrapped via "if let Some(x) = x" pattern
    unwrapped_options: set[str] = field(default_factory=set)

    def indent_str(self) -> str:
        return "    " * self.indent


class RustEmitter:
    """Emits Rust code from IR nodes."""

    def __init__(
        self,
        resolver: TypeResolver | None = None,
        local_modules: set[str] | None = None,
        crate_name: str | None = None,
    ) -> None:
        self.resolver = resolver or TypeResolver()
        self.ctx = EmitterContext(resolver=self.resolver)
        self.ctx.local_modules = local_modules or set()
        self.ctx.crate_name = crate_name  # For main.rs importing from lib
        self.output: list[str] = []

    def _is_result_type(self, ir_type: IRType | None) -> bool:
        """Check if a type is Result[T, E]."""
        if ir_type is None:
            return False
        if isinstance(ir_type, IRGenericType):
            return ir_type.name == "Result"
        return False

    def _is_option_type(self, ir_type: IRType | None) -> bool:
        """Check if a type is T | None (Option<T> in Rust)."""
        if ir_type is None:
            return False
        # Handle IRGenericType with name "Optional" (from Optional[T] or T | None)
        if isinstance(ir_type, IRGenericType):
            return ir_type.name == "Optional"
        if isinstance(ir_type, IRUnionType):
            # Check if this is a T | None union (becomes Option<T>)
            types = ir_type.types
            if len(types) == 2:
                none_count = sum(1 for t in types if isinstance(t, IRPrimitiveType) and t.name == PrimitiveType.NONE)
                return none_count == 1
        return False

    def _extract_type_string(self, ir_type: IRType | None) -> str | None:
        """Extract a type string for method mapping lookup.

        Returns strings like "datetime.datetime", "datetime.date", "datetime.timedelta"
        that can be used to look up method mappings.
        """
        if ir_type is None:
            return None
        if isinstance(ir_type, IRClassType):
            if ir_type.module:
                return f"{ir_type.module}.{ir_type.name}"
            return ir_type.name
        if isinstance(ir_type, IRGenericType):
            # For Optional types, extract the inner type
            if ir_type.name == "Optional" and ir_type.type_args:
                return self._extract_type_string(ir_type.type_args[0])
            # For other generics, return just the outer type name
            return ir_type.name
        return None

    def emit_module(self, module: IRModule) -> str:
        """Emit a complete Rust module."""
        header_lines: list[str] = []
        body_lines: list[str] = []

        # Collect class names for constructor detection
        self.ctx.class_names = {cls.name for cls in module.classes}

        # Collect Result-returning functions for ? operator support
        for func in module.functions:
            if self._is_result_type(func.return_type):
                self.ctx.result_functions.add(func.name)
        for cls in module.classes:
            for method in cls.methods:
                if self._is_result_type(method.return_type):
                    # Track as ClassName.method_name
                    self.ctx.result_functions.add(f"{cls.name}.{method.name}")
                    # Also track just the method name for simple lookups
                    self.ctx.result_functions.add(method.name)

        # Process imports and track local module imports
        self._process_imports(module.imports)

        # Sync stub imports to the resolver for type resolution
        self.resolver.stub_imports = self.ctx.stub_imports.copy()

        # Module docstring as comment
        if module.docstring:
            header_lines.append(f"//! {module.docstring.split(chr(10))[0]}")
            header_lines.append("")

        # Emit classes as structs (this may add stdlib_imports)
        for cls in module.classes:
            body_lines.append(self.emit_class(cls))
            body_lines.append("")

        # Emit functions (this may add stdlib_imports)
        for func in module.functions:
            body_lines.append(self.emit_function(func))
            body_lines.append("")

        # Emit top-level statements in main() if any
        # Filter out `if __name__ == "__main__"` patterns as they don't apply in Rust
        # Filter out `asyncio.run(main())` as #[tokio::main] handles this
        filtered_statements = [
            stmt for stmt in module.statements if not self._is_name_main_check(stmt) and not self._is_asyncio_run(stmt)
        ]
        if filtered_statements:
            body_lines.append("fn main() {")
            self.ctx.indent = 1
            for stmt in filtered_statements:
                body_lines.append(self.emit_statement(stmt))
            self.ctx.indent = 0
            body_lines.append("}")
            body_lines.append("")

        # Now collect imports (after emission so stdlib_imports is populated)
        imports = self._collect_imports(module)
        if imports:
            header_lines.extend(imports)
            header_lines.append("")

        return "\n".join(header_lines + body_lines)

    def _is_name_main_check(self, stmt: IRStatement) -> bool:
        """Check if statement is `if __name__ == "__main__": ...`.

        This Python idiom doesn't apply in Rust, so we skip it.
        """
        if isinstance(stmt, IRIf):
            cond = stmt.condition
            # Check for __name__ == "__main__"
            if isinstance(cond, IRBinaryOp) and cond.op == BinaryOp.EQ:
                left, right = cond.left, cond.right
                # Check both orders: __name__ == "__main__" or "__main__" == __name__
                if isinstance(left, IRName) and left.name == "__name__":
                    if isinstance(right, IRLiteral) and right.value == "__main__":
                        return True
                if isinstance(right, IRName) and right.name == "__name__":
                    if isinstance(left, IRLiteral) and left.value == "__main__":
                        return True
        return False

    def _is_asyncio_run(self, stmt: IRStatement) -> bool:
        """Check if statement is `asyncio.run(...)`.

        When we have an async main function with #[tokio::main],
        we don't need asyncio.run() as the runtime is handled by the attribute.
        """
        if isinstance(stmt, IRExprStmt):
            expr = stmt.expr
            if isinstance(expr, IRCall):
                func = expr.func
                # Check for asyncio.run() pattern
                if isinstance(func, IRAttribute):
                    if isinstance(func.obj, IRName) and func.obj.name == "asyncio":
                        if func.attr == "run":
                            return True
        return False

    def _process_imports(self, imports: list[IRImport]) -> None:
        """Process Python imports and categorize them."""
        for imp in imports:
            module_name = imp.module.split(".")[0]  # Get top-level module

            # Check if this is a stub package import (e.g., from spicycrab_anyhow import Result)
            crate_name = get_crate_for_python_module(module_name)
            if crate_name:
                # Track which names came from which crate
                if imp.names:
                    for name, alias in imp.names:
                        effective_name = alias if alias else name
                        self.ctx.stub_imports[effective_name] = crate_name
                        # Track uppercase names as class names for constructor detection
                        if name[0].isupper():
                            self.ctx.class_names.add(effective_name)
                continue

            # Check if this is a local module import
            if module_name in self.ctx.local_modules:
                if module_name not in self.ctx.local_imports:
                    self.ctx.local_imports[module_name] = []
                if imp.names:
                    self.ctx.local_imports[module_name].extend(imp.names)
                    # Track imported names as potential classes for constructor detection
                    # Use Python convention: class names start with uppercase
                    for name, alias in imp.names:
                        effective_name = alias if alias else name
                        if name[0].isupper():  # Only classes (uppercase first letter)
                            self.ctx.class_names.add(effective_name)
                else:
                    # import module - import all public items
                    self.ctx.local_imports[module_name].append((module_name, None))
            # Stdlib modules are handled by the emitter during code generation

    def _collect_imports(self, module: IRModule) -> list[str]:
        """Collect required Rust imports."""
        imports = set()

        # Check which collections the module uses (HashMap, HashSet)
        needed_collections = self._needed_collections(module)
        if needed_collections:
            imports.add(f"use std::collections::{{{', '.join(sorted(needed_collections))}}};")

        # Add resolver-detected imports
        imports.update(self.resolver.get_imports())

        # Add stdlib imports collected during emission
        for imp in self.ctx.stdlib_imports:
            # Convert module path to use statement
            if "::" in imp:
                imports.add(f"use {imp};")
            else:
                imports.add(f"use {imp};")

        # Add stub package imports (external crate imports)
        # Get unique crate names from stub_imports
        stub_crates = set(self.ctx.stub_imports.values())
        for crate_name in stub_crates:
            # Only add bare crate import for anyhow (needed for anyhow! macro)
            # Other crates use fully qualified paths so bare import is redundant
            if crate_name == "anyhow":
                imports.add(f"use {crate_name};")

        # Filter out redundant imports for stub crates
        # If we have "use clap;", we don't need "use clap::Arg;" since we use full paths
        # But keep trait imports (like chrono::Datelike, chrono::Timelike) as they're needed
        known_traits = {"Datelike", "Timelike", "SubsecRound", "DurationRound"}
        for crate_name in stub_crates:
            imports = {
                imp
                for imp in imports
                if not imp.startswith(f"use {crate_name}::")
                or any(imp.endswith(f"::{trait};") for trait in known_traits)
            }

        # Add local module imports
        # Use crate_name for main.rs (binary imports from library), "crate" for lib code
        prefix = self.ctx.crate_name if self.ctx.crate_name else "crate"
        for module_name, names in self.ctx.local_imports.items():
            if names:
                for name, alias in names:
                    if alias:
                        imports.add(f"use {prefix}::{module_name}::{name} as {alias};")
                    else:
                        imports.add(f"use {prefix}::{module_name}::{name};")

        return sorted(imports)

    def _needed_collections(self, module: IRModule) -> set[str]:
        """Return set of collection types needed (HashMap, HashSet)."""
        needed: set[str] = set()
        for func in module.functions:
            for stmt in func.body:
                needed.update(self._stmt_collections(stmt))
        for cls in module.classes:
            for method in cls.methods:
                for stmt in method.body:
                    needed.update(self._stmt_collections(stmt))
        return needed

    def _stmt_collections(self, stmt: IRStatement) -> set[str]:
        """Return set of collection types used by statement."""
        if isinstance(stmt, IRAssign) and stmt.value:
            return self._expr_collections(stmt.value)
        if isinstance(stmt, IRExprStmt):
            return self._expr_collections(stmt.expr)
        if isinstance(stmt, IRReturn) and stmt.value:
            return self._expr_collections(stmt.value)
        if isinstance(stmt, IRFor):
            result = self._expr_collections(stmt.iter)
            for s in stmt.body:
                result.update(self._stmt_collections(s))
            return result
        if isinstance(stmt, IRIf):
            result: set[str] = set()
            for s in stmt.then_body:
                result.update(self._stmt_collections(s))
            for s in stmt.else_body:
                result.update(self._stmt_collections(s))
            return result
        return set()

    def _expr_collections(self, expr: IRExpression) -> set[str]:
        """Return set of collection types used by expression."""
        if isinstance(expr, IRDict):
            return {"HashMap"}
        if isinstance(expr, IRSet):
            return {"HashSet"}
        if isinstance(expr, IRCall):
            result: set[str] = set()
            for a in expr.args:
                result.update(self._expr_collections(a))
            return result
        if isinstance(expr, IRBinaryOp):
            result = self._expr_collections(expr.left)
            result.update(self._expr_collections(expr.right))
            return result
        return set()

    def emit_class(self, cls: IRClass) -> str:
        """Emit a class as a Rust struct + impl block."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        # Check for Rust attributes
        rust_attrs = getattr(cls, "__rust_attrs__", None)
        if rust_attrs:
            for attr in rust_attrs.to_rust_attributes():
                lines.append(f"{indent}{attr}")

        # Docstring
        if cls.docstring:
            lines.append(f"{indent}/// {cls.docstring.split(chr(10))[0]}")

        # Struct definition
        # Add default derives if no rust_attrs
        if not rust_attrs:
            lines.append(f"{indent}#[derive(Debug, Clone)]")

        lines.append(f"{indent}pub struct {cls.name} {{")

        # Fields
        self.ctx.indent += 1
        field_indent = self.ctx.indent_str()
        for field_name, field_type in cls.fields:
            rust_type = self.resolver.resolve(field_type)
            lines.append(f"{field_indent}pub {field_name}: {rust_type.to_rust()},")
        self.ctx.indent -= 1

        lines.append(f"{indent}}}")
        lines.append("")

        # Check if class has __init__ method
        has_init = any(m.name == "__init__" for m in cls.methods)

        # Impl block for methods (or just constructor for dataclass)
        if cls.methods or (cls.is_dataclass and cls.fields):
            lines.append(f"{indent}impl {cls.name} {{")
            self.ctx.indent += 1
            self.ctx.in_impl = True
            self.ctx.current_class = cls.name

            # Generate constructor for dataclass without __init__
            if cls.is_dataclass and not has_init and cls.fields:
                lines.append(self._emit_dataclass_constructor(cls))
                lines.append("")

            for method in cls.methods:
                # Skip __enter__/__exit__ for context managers - Drop trait handles it
                if method.name in ("__enter__", "__exit__"):
                    continue
                lines.append(self.emit_method(method, cls))
                lines.append("")

            self.ctx.indent -= 1
            self.ctx.in_impl = False
            self.ctx.current_class = None
            lines.append(f"{indent}}}")

        # Drop trait for context managers
        if cls.has_enter and cls.has_exit:
            lines.append("")
            lines.append(f"{indent}impl Drop for {cls.name} {{")
            lines.append(f"{indent}    fn drop(&mut self) {{")
            lines.append(f"{indent}        // Auto-generated from __exit__")
            lines.append(f"{indent}    }}")
            lines.append(f"{indent}}}")

        return "\n".join(lines)

    def _emit_dataclass_constructor(self, cls: IRClass) -> str:
        """Generate a new() constructor for a dataclass."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        # Build parameter list
        params: list[str] = []
        for field_name, field_type in cls.fields:
            rust_type = self.resolver.resolve(field_type)
            params.append(f"{field_name}: {rust_type.to_rust()}")

        params_str = ", ".join(params)
        lines.append(f"{indent}pub fn new({params_str}) -> Self {{")

        self.ctx.indent += 1
        inner_indent = self.ctx.indent_str()
        lines.append(f"{inner_indent}Self {{")

        self.ctx.indent += 1
        field_indent = self.ctx.indent_str()
        for field_name, _ in cls.fields:
            lines.append(f"{field_indent}{field_name},")
        self.ctx.indent -= 1

        lines.append(f"{inner_indent}}}")
        self.ctx.indent -= 1
        lines.append(f"{indent}}}")

        return "\n".join(lines)

    def emit_method(self, method: IRFunction, cls: IRClass) -> str:
        """Emit a method within an impl block."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        # Check for Rust attributes
        rust_attrs = getattr(method, "__rust_attrs__", None)
        if rust_attrs:
            for attr in rust_attrs.to_rust_attributes():
                lines.append(f"{indent}{attr}")

        # Docstring
        if method.docstring:
            lines.append(f"{indent}/// {method.docstring.split(chr(10))[0]}")

        # Translate __init__ to new
        name = method.name
        if name == "__init__":
            name = "new"

        # Escape Rust keywords used as method names
        rust_keywords = {
            "use",
            "type",
            "impl",
            "trait",
            "mod",
            "pub",
            "fn",
            "let",
            "mut",
            "ref",
            "move",
            "self",
            "super",
            "crate",
            "as",
            "break",
            "continue",
            "else",
            "for",
            "if",
            "in",
            "loop",
            "match",
            "return",
            "while",
            "async",
            "await",
            "dyn",
            "struct",
            "enum",
            "union",
            "const",
            "static",
            "extern",
            "unsafe",
            "where",
        }
        if name in rust_keywords:
            name = f"r#{name}"

        # Build parameter list
        params: list[str] = []
        is_constructor = method.name == "__init__"

        if not is_constructor and method.is_method:
            # Add self parameter - use &mut self if method modifies self
            if method.modifies_self:
                params.append("&mut self")
            else:
                params.append("&self")

        for param in method.params:
            rust_type = self.resolver.resolve(param.type)
            params.append(f"{param.name}: {rust_type.to_rust()}")

        params_str = ", ".join(params)

        # Return type
        if is_constructor:
            ret_str = " -> Self"
        elif method.return_type:
            rust_ret = self.resolver.resolve(method.return_type)
            if rust_ret.name != "()":
                ret_str = f" -> {rust_ret.to_rust()}"
            else:
                ret_str = ""
        else:
            ret_str = ""

        lines.append(f"{indent}pub fn {name}({params_str}){ret_str} {{")

        # Constructor special handling
        if is_constructor:
            self.ctx.indent += 1
            inner_indent = self.ctx.indent_str()
            lines.append(f"{inner_indent}Self {{")
            self.ctx.indent += 1
            field_indent = self.ctx.indent_str()
            # Initialize fields from __init__ body
            for stmt in method.body:
                if isinstance(stmt, IRAttrAssign) and isinstance(stmt.obj, IRName) and stmt.obj.name == "self":
                    value_str = self.emit_expression(stmt.value)
                    # Use Rust shorthand syntax when field name matches value (clippy::redundant_field_names)
                    if stmt.attr == value_str:
                        lines.append(f"{field_indent}{stmt.attr},")
                    else:
                        lines.append(f"{field_indent}{stmt.attr}: {value_str},")
            self.ctx.indent -= 1
            lines.append(f"{inner_indent}}}")
            self.ctx.indent -= 1
        else:
            # Track if we're in a Result-returning or Option-returning method
            prev_result_context = self.ctx.in_result_context
            prev_option_context = self.ctx.in_option_context
            self.ctx.in_result_context = self._is_result_type(method.return_type)
            self.ctx.in_option_context = self._is_option_type(method.return_type)

            # Regular method body
            self.ctx.indent += 1
            for i, stmt in enumerate(method.body):
                is_last = i == len(method.body) - 1
                self.ctx.in_last_stmt = is_last
                lines.append(self.emit_statement(stmt))
            self.ctx.in_last_stmt = False
            self.ctx.indent -= 1

            # Restore previous context
            self.ctx.in_result_context = prev_result_context
            self.ctx.in_option_context = prev_option_context

        lines.append(f"{indent}}}")

        return "\n".join(lines)

    def emit_function(self, func: IRFunction) -> str:
        """Emit a standalone function."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        # Check for Rust attributes
        rust_attrs = getattr(func, "__rust_attrs__", None)
        if rust_attrs:
            for attr in rust_attrs.to_rust_attributes():
                lines.append(f"{indent}{attr}")

        # Add #[tokio::main] for async main function
        if func.is_async and func.name == "main":
            lines.append(f"{indent}#[tokio::main]")

        # Docstring
        if func.docstring:
            lines.append(f"{indent}/// {func.docstring.split(chr(10))[0]}")

        # Build parameter list
        params: list[str] = []
        for param in func.params:
            rust_type = self.resolver.resolve(param.type)
            params.append(f"{param.name}: {rust_type.to_rust()}")

        params_str = ", ".join(params)

        # Return type
        if func.return_type:
            rust_ret = self.resolver.resolve(func.return_type)
            if rust_ret.name != "()":
                ret_str = f" -> {rust_ret.to_rust()}"
            else:
                ret_str = ""
        else:
            ret_str = ""

        # Async functions get the async keyword
        async_kw = "async " if func.is_async else ""
        lines.append(f"{indent}pub {async_kw}fn {func.name}({params_str}){ret_str} {{")

        # Track if we're in a Result-returning or Option-returning function
        prev_result_context = self.ctx.in_result_context
        prev_option_context = self.ctx.in_option_context
        self.ctx.in_result_context = self._is_result_type(func.return_type)
        self.ctx.in_option_context = self._is_option_type(func.return_type)

        # Body - mark last statement for expression return
        self.ctx.indent += 1
        for i, stmt in enumerate(func.body):
            is_last = i == len(func.body) - 1
            self.ctx.in_last_stmt = is_last
            lines.append(self.emit_statement(stmt))
        self.ctx.in_last_stmt = False
        self.ctx.indent -= 1

        # Restore previous context
        self.ctx.in_result_context = prev_result_context
        self.ctx.in_option_context = prev_option_context

        lines.append(f"{indent}}}")

        return "\n".join(lines)

    def emit_statement(self, stmt: IRStatement) -> str:
        """Emit a statement."""
        indent = self.ctx.indent_str()

        if isinstance(stmt, IRAssign):
            return self._emit_assign(stmt)

        if isinstance(stmt, IRTupleUnpack):
            return self._emit_tuple_unpack(stmt)

        if isinstance(stmt, IRAttrAssign):
            # Check for compound assignment pattern: self.attr = self.attr op y -> self.attr op= y
            # This avoids clippy::assign_op_pattern warnings
            if isinstance(stmt.value, IRBinaryOp):
                if isinstance(stmt.value.left, IRAttribute):
                    left_attr = stmt.value.left
                    if (
                        isinstance(left_attr.obj, IRName)
                        and left_attr.obj.name == "self"
                        and left_attr.attr == stmt.attr
                    ):
                        op = stmt.value.op
                        compound_ops = {
                            BinaryOp.ADD: "+=",
                            BinaryOp.SUB: "-=",
                            BinaryOp.MUL: "*=",
                            BinaryOp.DIV: "/=",
                            BinaryOp.MOD: "%=",
                        }
                        if op in compound_ops:
                            right = self.emit_expression(stmt.value.right)
                            return f"{indent}self.{stmt.attr} {compound_ops[op]} {right};"
            return f"{indent}self.{stmt.attr} = {self.emit_expression(stmt.value)};"

        if isinstance(stmt, IRReturn):
            if stmt.value:
                expr = self.emit_expression(stmt.value)
                # Wrap non-None values in Some() for Option-returning functions
                if self.ctx.in_option_context and expr != "None":
                    expr = f"Some({expr})"
                # If this is the last statement, emit as expression (implicit return)
                # Otherwise, use explicit return
                if self.ctx.in_last_stmt:
                    return f"{indent}{expr}"
                return f"{indent}return {expr};"
            return f"{indent}return;"

        if isinstance(stmt, IRIf):
            return self._emit_if(stmt)

        if isinstance(stmt, IRWhile):
            return self._emit_while(stmt)

        if isinstance(stmt, IRFor):
            return self._emit_for(stmt)

        if isinstance(stmt, IRBreak):
            return f"{indent}break;"

        if isinstance(stmt, IRContinue):
            return f"{indent}continue;"

        if isinstance(stmt, IRPass):
            return f"{indent}// pass"

        if isinstance(stmt, IRExprStmt):
            return f"{indent}{self.emit_expression(stmt.expr)};"

        if isinstance(stmt, IRWith):
            return self._emit_with(stmt)

        if isinstance(stmt, IRTry):
            return self._emit_try(stmt)

        if isinstance(stmt, IRRaise):
            if stmt.exc:
                # Handle raise SomeException("message") -> return Err("message")
                exc_expr = stmt.exc
                if isinstance(exc_expr, IRCall):
                    # Extract the message from the exception constructor
                    if exc_expr.args:
                        err_msg = self.emit_expression(exc_expr.args[0])
                        return f"{indent}return Err({err_msg});"
                    # No args, use the exception type name
                    func_name = self.emit_expression(exc_expr.func)
                    return f'{indent}return Err("{func_name}".to_string());'
                return f"{indent}return Err({self.emit_expression(stmt.exc)});"
            return f'{indent}panic!("re-raise");'

        return f"{indent}// Unsupported: {type(stmt).__name__}"

    def _emit_assign(self, stmt: IRAssign) -> str:
        """Emit an assignment statement."""
        indent = self.ctx.indent_str()

        if stmt.is_declaration:
            # Set target type for turbofish inference before emitting value
            if stmt.type_annotation:
                rust_type = self.resolver.resolve(stmt.type_annotation)
                self.ctx.assignment_target_type = rust_type.to_rust()
            else:
                self.ctx.assignment_target_type = None

            value = self.emit_expression(stmt.value)

            # Clear target type after emission
            self.ctx.assignment_target_type = None

            # Only add mut if explicitly marked mutable (reassigned later)
            mut = "mut " if stmt.is_mutable else ""
            if stmt.type_annotation:
                rust_type = self.resolver.resolve(stmt.type_annotation)
                # Track the type for instance method resolution
                type_str = self._extract_type_string(stmt.type_annotation)
                if type_str:
                    self.ctx.type_env[stmt.target] = type_str
                # Wrap non-None values in Some() for Option types
                # But don't wrap function/method calls that already return Option types
                is_call = isinstance(stmt.value, (IRCall, IRMethodCall))
                if rust_type.name == "Option" and value != "None" and not is_call:
                    value = f"Some({value})"
                return f"{indent}let {mut}{stmt.target}: {rust_type.to_rust()} = {value};"
            return f"{indent}let {mut}{stmt.target} = {value};"
        else:
            # Check for compound assignment pattern: x = x op y -> x op= y
            # This avoids clippy::assign_op_pattern warnings
            if isinstance(stmt.value, IRBinaryOp):
                if isinstance(stmt.value.left, IRName) and stmt.value.left.name == stmt.target:
                    op = stmt.value.op
                    compound_ops = {
                        BinaryOp.ADD: "+=",
                        BinaryOp.SUB: "-=",
                        BinaryOp.MUL: "*=",
                        BinaryOp.DIV: "/=",
                        BinaryOp.MOD: "%=",
                        BinaryOp.BIT_AND: "&=",
                        BinaryOp.BIT_OR: "|=",
                        BinaryOp.BIT_XOR: "^=",
                        BinaryOp.LSHIFT: "<<=",
                        BinaryOp.RSHIFT: ">>=",
                    }
                    if op in compound_ops:
                        right = self.emit_expression(stmt.value.right)
                        return f"{indent}{stmt.target} {compound_ops[op]} {right};"
            value = self.emit_expression(stmt.value)
            return f"{indent}{stmt.target} = {value};"

    def _emit_tuple_unpack(self, stmt: IRTupleUnpack) -> str:
        """Emit a tuple unpacking assignment.

        Python: tx, rx = mpsc_channel(10)
        Rust:   let (tx, mut rx) = tokio::sync::mpsc::channel(10);
        """
        indent = self.ctx.indent_str()
        value = self.emit_expression(stmt.value)

        # Build the tuple pattern with mutability
        target_parts = []
        for i, target in enumerate(stmt.targets):
            is_mut = i < len(stmt.is_mutable) and stmt.is_mutable[i]
            if is_mut:
                target_parts.append(f"mut {target}")
            else:
                target_parts.append(target)
        targets_str = ", ".join(target_parts)

        # Check if we have type annotations for each target
        if stmt.type_annotations and any(t is not None for t in stmt.type_annotations):
            # We have type annotations - emit with types
            # let (tx, mut rx): (Sender<T>, Receiver<T>) = ...
            type_parts = []
            for i, target in enumerate(stmt.targets):
                if i < len(stmt.type_annotations) and stmt.type_annotations[i]:
                    rust_type = self.resolver.resolve(stmt.type_annotations[i])
                    type_parts.append(rust_type.to_rust())
                else:
                    type_parts.append("_")  # Use type inference for unannotated
            types_str = ", ".join(type_parts)
            return f"{indent}let ({targets_str}): ({types_str}) = {value};"

        # No type annotations - let Rust infer the types
        return f"{indent}let ({targets_str}) = {value};"

    def _emit_if(self, stmt: IRIf) -> str:
        """Emit an if statement."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        # Check for "x is not None" pattern -> use "if let Some(x) = x"
        unwrapped_var: str | None = None
        if (
            isinstance(stmt.condition, IRBinaryOp)
            and stmt.condition.op == BinaryOp.IS_NOT
            and isinstance(stmt.condition.left, IRName)
            and isinstance(stmt.condition.right, IRLiteral)
            and stmt.condition.right.value is None
        ):
            var_name = stmt.condition.left.name
            unwrapped_var = var_name
            lines.append(f"{indent}if let Some({var_name}) = {var_name} {{")
        else:
            cond = self.emit_expression(stmt.condition)
            lines.append(f"{indent}if {cond} {{")

        self.ctx.indent += 1
        # If we unwrapped a variable, track it so method calls don't use Option
        if unwrapped_var:
            self.ctx.unwrapped_options.add(unwrapped_var)
        for s in stmt.then_body:
            lines.append(self.emit_statement(s))
        if unwrapped_var:
            self.ctx.unwrapped_options.discard(unwrapped_var)
        self.ctx.indent -= 1

        for elif_cond, elif_body in stmt.elif_clauses:
            cond = self.emit_expression(elif_cond)
            lines.append(f"{indent}}} else if {cond} {{")
            self.ctx.indent += 1
            for s in elif_body:
                lines.append(self.emit_statement(s))
            self.ctx.indent -= 1

        if stmt.else_body:
            lines.append(f"{indent}}} else {{")
            self.ctx.indent += 1
            for s in stmt.else_body:
                lines.append(self.emit_statement(s))
            self.ctx.indent -= 1

        lines.append(f"{indent}}}")

        return "\n".join(lines)

    def _emit_while(self, stmt: IRWhile) -> str:
        """Emit a while loop."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        cond = self.emit_expression(stmt.condition)
        lines.append(f"{indent}while {cond} {{")

        self.ctx.indent += 1
        for s in stmt.body:
            lines.append(self.emit_statement(s))
        self.ctx.indent -= 1

        lines.append(f"{indent}}}")

        return "\n".join(lines)

    def _emit_for(self, stmt: IRFor) -> str:
        """Emit a for loop."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        iter_expr = self.emit_expression(stmt.iter)
        lines.append(f"{indent}for {stmt.target} in {iter_expr} {{")

        self.ctx.indent += 1
        for s in stmt.body:
            lines.append(self.emit_statement(s))
        self.ctx.indent -= 1

        lines.append(f"{indent}}}")

        return "\n".join(lines)

    def _emit_with(self, stmt: IRWith) -> str:
        """Emit a with statement as a scoped block."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        ctx_expr = self.emit_expression(stmt.context)

        lines.append(f"{indent}{{")
        self.ctx.indent += 1
        inner_indent = self.ctx.indent_str()

        # Check for tempfile context managers that return path in __enter__
        is_tempfile_ctx = False
        if isinstance(stmt.context, IRMethodCall):
            if isinstance(stmt.context.obj, IRName):
                if stmt.context.obj.name == "tempfile":
                    if stmt.context.method in ("TemporaryDirectory", "NamedTemporaryFile"):
                        is_tempfile_ctx = True

        # Use mut by default since context managers often need mutation
        if stmt.target:
            if is_tempfile_ctx:
                # tempfile context managers: bind the path, not the object
                # Keep the TempDir alive with _temp_ctx, bind path to target
                lines.append(f"{inner_indent}let _temp_ctx = {ctx_expr};")
                if "TemporaryDirectory" in ctx_expr or "tempdir" in ctx_expr:
                    lines.append(f"{inner_indent}let {stmt.target} = _temp_ctx.path().to_string_lossy().to_string();")
                else:
                    # NamedTempFile - get the path
                    lines.append(f"{inner_indent}let {stmt.target} = _temp_ctx.path().to_string_lossy().to_string();")
            else:
                lines.append(f"{inner_indent}let mut {stmt.target} = {ctx_expr};")
        else:
            lines.append(f"{inner_indent}let _ctx = {ctx_expr};")

        for s in stmt.body:
            lines.append(self.emit_statement(s))

        self.ctx.indent -= 1
        lines.append(f"{indent}}} // drop")

        return "\n".join(lines)

    def _emit_try(self, stmt: IRTry) -> str:
        """Emit try/except as match on Result or catch_unwind for panics."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        # Check if this is a single-statement try with a Result-returning call
        # Pattern: try: result = fallible_call() except: handle_error()
        if len(stmt.body) == 1 and stmt.handlers and isinstance(stmt.body[0], IRAssign) and stmt.body[0].value:
            assign = stmt.body[0]
            # Check if the call returns Result
            call = assign.value
            is_result_call = False
            if isinstance(call, IRCall):
                func = self.emit_expression(call.func)
                is_result_call = func in self.ctx.result_functions
            elif isinstance(call, IRMethodCall):
                is_result_call = call.method in self.ctx.result_functions

            if is_result_call:
                return self._emit_try_as_match(stmt, assign, indent)

        # Check if try body is a single expression statement with Result call
        if len(stmt.body) == 1 and stmt.handlers and isinstance(stmt.body[0], IRExprStmt) and stmt.body[0].expr:
            expr_stmt = stmt.body[0]
            call = expr_stmt.expr
            is_result_call = False
            if isinstance(call, IRCall):
                func = self.emit_expression(call.func)
                is_result_call = func in self.ctx.result_functions
            elif isinstance(call, IRMethodCall):
                is_result_call = call.method in self.ctx.result_functions

            if is_result_call:
                return self._emit_try_expr_as_match(stmt, expr_stmt, indent)

        # Fallback: use catch_unwind for runtime panics
        if stmt.handlers:
            lines.append(
                f"{indent}if let Err(_panic_err) = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {{"
            )
            self.ctx.indent += 1

            for s in stmt.body:
                lines.append(self.emit_statement(s))

            self.ctx.indent -= 1
            lines.append(f"{indent}}})) {{")

            self.ctx.indent += 1
            if stmt.handlers:
                handler = stmt.handlers[0]
                for s in handler.body:
                    lines.append(self.emit_statement(s))
            self.ctx.indent -= 1
            lines.append(f"{indent}}}")
        else:
            lines.append(f"{indent}{{")
            self.ctx.indent += 1
            for s in stmt.body:
                lines.append(self.emit_statement(s))
            self.ctx.indent -= 1
            lines.append(f"{indent}}}")

        if stmt.finally_body:
            lines.append(f"{indent}// finally block")
            for s in stmt.finally_body:
                lines.append(self.emit_statement(s))

        return "\n".join(lines)

    def _emit_try_as_match(self, stmt: IRTry, assign: IRAssign, indent: str) -> str:
        """Emit try/except with assignment as match on Result."""
        lines: list[str] = []
        call_expr = self.emit_expression(assign.value)
        var_name = assign.target

        # match fallible_call() { Ok(var) => { ... }, Err(e) => { ... } }
        lines.append(f"{indent}match {call_expr} {{")
        self.ctx.indent += 1
        inner_indent = self.ctx.indent_str()

        # Ok arm - just bind the variable, rest of code continues after match
        lines.append(f"{inner_indent}Ok({var_name}) => {{}}")

        # Err arm - execute handler body
        handler = stmt.handlers[0]
        err_name = handler.name if handler.name else "_err"
        lines.append(f"{inner_indent}Err({err_name}) => {{")
        self.ctx.indent += 1
        for s in handler.body:
            lines.append(self.emit_statement(s))
        self.ctx.indent -= 1
        lines.append(f"{inner_indent}}}")

        self.ctx.indent -= 1
        lines.append(f"{indent}}}")

        # Finally block
        if stmt.finally_body:
            lines.append(f"{indent}// finally block")
            for s in stmt.finally_body:
                lines.append(self.emit_statement(s))

        return "\n".join(lines)

    def _emit_try_expr_as_match(self, stmt: IRTry, expr_stmt: IRExprStmt, indent: str) -> str:
        """Emit try/except with expression (no assignment) as match on Result."""
        lines: list[str] = []
        call_expr = self.emit_expression(expr_stmt.expr)

        # match fallible_call() { Ok(_) => { }, Err(e) => { ... } }
        lines.append(f"{indent}match {call_expr} {{")
        self.ctx.indent += 1
        inner_indent = self.ctx.indent_str()

        lines.append(f"{inner_indent}Ok(_) => {{}}")

        handler = stmt.handlers[0]
        err_name = handler.name if handler.name else "_err"
        lines.append(f"{inner_indent}Err({err_name}) => {{")
        self.ctx.indent += 1
        for s in handler.body:
            lines.append(self.emit_statement(s))
        self.ctx.indent -= 1
        lines.append(f"{inner_indent}}}")

        self.ctx.indent -= 1
        lines.append(f"{indent}}}")

        if stmt.finally_body:
            lines.append(f"{indent}// finally block")
            for s in stmt.finally_body:
                lines.append(self.emit_statement(s))

        return "\n".join(lines)

    def emit_expression(self, expr: IRExpression | None) -> str:
        """Emit an expression."""
        if expr is None:
            return "()"

        if isinstance(expr, IRLiteral):
            return self._emit_literal(expr)

        if isinstance(expr, IRName):
            return expr.name

        if isinstance(expr, IRBinaryOp):
            return self._emit_binop(expr)

        if isinstance(expr, IRUnaryOp):
            op = UNARYOP_MAP.get(expr.op, "!")
            operand = self.emit_expression(expr.operand)
            return f"{op}{operand}"

        if isinstance(expr, IRCall):
            return self._emit_call(expr)

        if isinstance(expr, IRMethodCall):
            return self._emit_method_call(expr)

        if isinstance(expr, IRAttribute):
            # Check for stdlib module attributes (e.g., sys.argv, sys.platform)
            if isinstance(expr.obj, IRName):
                module = expr.obj.name
                mapping = get_stdlib_mapping(module, expr.attr)
                if mapping:
                    # Track required imports
                    for imp in mapping.rust_imports:
                        self.ctx.stdlib_imports.add(imp)
                    return mapping.rust_code

                # Check for typed variable property access (e.g., dt.year for datetime)
                if module in self.ctx.type_env:
                    var_type = self.ctx.type_env[module]
                    # Extract class name from type (e.g., "datetime.datetime" -> "datetime")
                    class_name = var_type.split(".")[-1]
                    # Look up method mapping with full key (e.g., "datetime.year")
                    method_key = f"{class_name}.{expr.attr}"
                    mapping = get_datetime_method_mapping(method_key)
                    if mapping:
                        obj = self.emit_expression(expr.obj)
                        rust_code = mapping.rust_code.replace("{self}", obj)
                        for imp in mapping.rust_imports:
                            self.ctx.stdlib_imports.add(imp)
                        return rust_code

                # Check for stub type enum variant access (e.g., ArgAction.SetTrue)
                # Convert Python enum syntax to Rust path syntax: Type.Variant -> crate::Type::Variant
                if module in self.ctx.stub_imports:
                    crate_name = self.ctx.stub_imports[module]
                    return f"{crate_name}::{module}::{expr.attr}"

            obj = self.emit_expression(expr.obj)
            return f"{obj}.{expr.attr}"

        if isinstance(expr, IRSubscript):
            obj = self.emit_expression(expr.obj)
            index = self.emit_expression(expr.index)
            # Cast integer indices to usize for Vec/slice indexing
            # This handles cases like values[i] where i: int (i64 in Rust)
            if isinstance(expr.index, IRName):
                # Variable used as index - cast to usize if it's a simple name
                # (likely an integer counter)
                index = f"{index} as usize"
            return f"{obj}[{index}]"

        if isinstance(expr, IRList):
            elements = [self.emit_expression(e) for e in expr.elements]
            return f"vec![{', '.join(elements)}]"

        if isinstance(expr, IRDict):
            pairs = []
            for k, v in zip(expr.keys, expr.values):
                key = self.emit_expression(k)
                val = self.emit_expression(v)
                pairs.append(f"({key}, {val})")
            return f"HashMap::from([{', '.join(pairs)}])"

        if isinstance(expr, IRSet):
            elements = [self.emit_expression(e) for e in expr.elements]
            return f"HashSet::from([{', '.join(elements)}])"

        if isinstance(expr, IRTuple):
            elements = [self.emit_expression(e) for e in expr.elements]
            return f"({', '.join(elements)})"

        if isinstance(expr, IRIfExp):
            cond = self.emit_expression(expr.condition)
            then = self.emit_expression(expr.then_expr)
            else_ = self.emit_expression(expr.else_expr)
            return f"if {cond} {{ {then} }} else {{ {else_} }}"

        if isinstance(expr, IRListComp):
            return self._emit_list_comp(expr)

        if isinstance(expr, IRFString):
            return self._emit_fstring(expr)

        if isinstance(expr, IRAwait):
            # Emit await expression: value.await
            inner = self.emit_expression(expr.value)
            return f"{inner}.await"

        return f"/* unsupported: {type(expr).__name__} */"

    def _emit_literal(self, expr: IRLiteral) -> str:
        """Emit a literal value."""
        if expr.value is None:
            return "None"  # Rust Option::None
        if isinstance(expr.value, bool):
            return "true" if expr.value else "false"
        if isinstance(expr.value, str):
            escaped = expr.value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}".to_string()'
        if isinstance(expr.value, int):
            return str(expr.value)
        if isinstance(expr.value, float):
            s = str(expr.value)
            if "." not in s and "e" not in s.lower():
                s += ".0"
            return s
        return repr(expr.value)

    def _emit_binop(self, expr: IRBinaryOp) -> str:
        """Emit a binary operation."""
        # Special handling for str.find() comparisons
        # Python: str.find(x) >= 0  -> Rust: str.contains(x)
        # Python: str.find(x) != -1 -> Rust: str.contains(x)
        # Python: str.find(x) == -1 -> Rust: !str.contains(x)
        # Python: str.find(x) < 0   -> Rust: !str.contains(x)
        if isinstance(expr.left, IRMethodCall) and expr.left.method == "find":
            right_val = self.emit_expression(expr.right)
            if right_val in ("0", "-1"):
                obj = self.emit_expression(expr.left.obj)
                # Emit the search argument without .to_string() for contains()
                if expr.left.args:
                    arg = self.emit_expression(expr.left.args[0])
                    # Strip .to_string() since contains takes &str
                    if arg.endswith(".to_string()"):
                        arg = arg[:-12]  # Remove .to_string()
                    else:
                        arg = f"&{arg}"
                else:
                    arg = '""'

                # Determine if this is a "found" or "not found" check
                if right_val == "0":
                    # >= 0 means found, < 0 means not found
                    if expr.op == BinaryOp.GE:
                        return f"{obj}.contains({arg})"
                    if expr.op == BinaryOp.LT:
                        return f"!{obj}.contains({arg})"
                elif right_val == "-1":
                    # != -1 means found, == -1 means not found
                    if expr.op == BinaryOp.NE:
                        return f"{obj}.contains({arg})"
                    if expr.op == BinaryOp.EQ:
                        return f"!{obj}.contains({arg})"

        left = self.emit_expression(expr.left)
        right = self.emit_expression(expr.right)

        # Special handling for len() comparisons with 0 to avoid clippy::len_zero
        # len(x) > 0  -> !x.is_empty()
        # len(x) != 0 -> !x.is_empty()
        # len(x) == 0 -> x.is_empty()
        # len(x) >= 1 -> !x.is_empty()
        # 0 < len(x)  -> !x.is_empty()
        if left.endswith(".len()") and right == "0":
            base = left[:-6]  # Remove .len()
            if expr.op in (BinaryOp.GT, BinaryOp.NE):
                return f"!{base}.is_empty()"
            if expr.op == BinaryOp.EQ:
                return f"{base}.is_empty()"
        if right.endswith(".len()") and left == "0":
            base = right[:-6]  # Remove .len()
            if expr.op == BinaryOp.LT:
                return f"!{base}.is_empty()"
            if expr.op == BinaryOp.EQ:
                return f"{base}.is_empty()"
        # Also handle >= 1 pattern
        if left.endswith(".len()") and right == "1" and expr.op == BinaryOp.GE:
            base = left[:-6]
            return f"!{base}.is_empty()"

        # Handle integer variable compared with .len() - cast to usize
        # Example: i < values.len() where i is i64 -> (i as usize) < values.len()
        if right.endswith(".len()") and isinstance(expr.left, IRName):
            if expr.op in (
                BinaryOp.LT,
                BinaryOp.LE,
                BinaryOp.GT,
                BinaryOp.GE,
                BinaryOp.EQ,
                BinaryOp.NE,
            ):
                return f"({left} as usize) {BINOP_MAP.get(expr.op, '<')} {right}"
        if left.endswith(".len()") and isinstance(expr.right, IRName):
            if expr.op in (
                BinaryOp.LT,
                BinaryOp.LE,
                BinaryOp.GT,
                BinaryOp.GE,
                BinaryOp.EQ,
                BinaryOp.NE,
            ):
                return f"{left} {BINOP_MAP.get(expr.op, '<')} ({right} as usize)"

        # Special handling for floor division
        if expr.op == BinaryOp.FLOOR_DIV:
            return f"{left} / {right}"

        # Special handling for 'in' operator
        # Python: x in container -> Rust: container.contains(&x)
        # Note: operands are swapped!
        if expr.op == BinaryOp.IN:
            return f"{right}.contains(&{left})"

        # Special handling for 'not in' operator
        if expr.op == BinaryOp.NOT_IN:
            return f"!{right}.contains(&{left})"

        # Special handling for 'is' operator (identity comparison)
        # Python: x is None -> Rust: x.is_none()
        # Python: x is not None -> Rust: x.is_some()
        if expr.op == BinaryOp.IS:
            if right == "None":
                return f"{left}.is_none()"
            # For non-None identity checks, fall through to pointer equality
            # (rare in transpiled code, but handle it)
            return f"std::ptr::eq(&{left}, &{right})"

        if expr.op == BinaryOp.IS_NOT:
            if right == "None":
                return f"{left}.is_some()"
            return f"!std::ptr::eq(&{left}, &{right})"

        # Special handling for power - return f64
        # Convert the entire left expression to f64 first, then apply powf
        if expr.op == BinaryOp.POW:
            # Wrap left in parens if it's a compound expression
            if isinstance(expr.left, IRBinaryOp):
                return f"(({left}) as f64).powf({right} as f64)"
            return f"({left} as f64).powf({right} as f64)"

        # Special handling for string concatenation
        # If either operand looks like a string (ends with .to_string() or is a string field)
        # use format! macro which works with both String and &str
        if expr.op == BinaryOp.ADD:
            if self._looks_like_string(left) or self._looks_like_string(right):
                return f'format!("{{}}{{}}", {left}, {right})'

        op = BINOP_MAP.get(expr.op, "+")

        # Add parentheses around nested binary ops to preserve precedence
        if isinstance(expr.left, IRBinaryOp):
            left = f"({left})"
        if isinstance(expr.right, IRBinaryOp):
            right = f"({right})"

        return f"{left} {op} {right}"

    def _looks_like_string(self, expr_str: str) -> bool:
        """Heuristic to detect if an expression is likely a String type."""
        # String literals end with .to_string()
        if expr_str.endswith(".to_string()"):
            return True
        # Don't mark numbers as strings
        if expr_str.isdigit():
            return False
        return False

    def _emit_call(self, expr: IRCall) -> str:
        """Emit a function call."""
        args = [self.emit_expression(a) for a in expr.args]

        # Check for standalone function calls imported from stub packages (e.g., sleep())
        if isinstance(expr.func, IRName):
            func_name = expr.func.name
            # Check if this function was imported from a stub package
            if func_name in self.ctx.stub_imports:
                crate_name = self.ctx.stub_imports[func_name]
                # Look up the full mapping key: crate.function (e.g., "tokio.sleep")
                full_key = f"{crate_name}.{func_name}"
                mapping = get_stub_mapping(full_key)
                if mapping:
                    result = self._apply_stdlib_mapping(mapping, args)
                    if mapping.needs_result and self.ctx.in_result_context:
                        if result.endswith(".unwrap()"):
                            result = result[:-9] + "?"
                    return result

        # Check for stub package Type.method calls (e.g., Result.Ok(), Error.msg())
        if isinstance(expr.func, IRAttribute) and isinstance(expr.func.obj, IRName):
            type_name = expr.func.obj.name
            func_name = expr.func.attr

            # Check if the type was imported from a stub package
            if type_name in self.ctx.stub_imports:
                crate_name = self.ctx.stub_imports[type_name]
                # Look up the full mapping key: crate.Type.method (e.g., "anyhow.Result.Ok")
                full_key = f"{crate_name}.{type_name}.{func_name}"
                mapping = get_stub_mapping(full_key)
                if mapping:
                    result = self._apply_stdlib_mapping(mapping, args)
                    # Add ? for Result-returning stub calls in Result context
                    if mapping.needs_result and self.ctx.in_result_context:
                        if result.endswith(".unwrap()"):
                            result = result[:-9] + "?"
                    return result

            # Check for stdlib module.function calls (e.g., os.getcwd(), json.loads())
            mapping = get_stdlib_mapping(type_name, func_name)
            if mapping:
                result = self._apply_stdlib_mapping(mapping, args)
                # Add ? for Result-returning stdlib calls in Result context
                if mapping.needs_result and self.ctx.in_result_context:
                    # Remove .unwrap() and add ? instead
                    if result.endswith(".unwrap()"):
                        result = result[:-9] + "?"
                return result

        func = self.emit_expression(expr.func)

        # Handle Path() constructor from pathlib
        if func == "Path":
            mapping = PATHLIB_MAPPINGS.get("Path")
            if mapping:
                return mapping.rust_code.format(args=", ".join(args))

        # Handle class constructor calls - ClassName(...) -> ClassName::new(...)
        if func in self.ctx.class_names:
            return f"{func}::new({', '.join(args)})"

        # Handle Some() constructor
        if func == "Some":
            return f"Some({', '.join(args)})"

        # Handle Ok/Err constructors
        if func in ("Ok", "Err"):
            return f"{func}({', '.join(args)})"

        # Handle range()
        if func == "range":
            if len(args) == 1:
                return f"0..{args[0]}"
            if len(args) == 2:
                return f"{args[0]}..{args[1]}"
            if len(args) == 3:
                return f"({args[0]}..{args[1]}).step_by({args[2]} as usize)"

        # Handle len()
        if func == "len":
            return f"{args[0]}.len()"

        # Handle print()
        if func == "print":
            if args:
                # Strip .to_string() since println! handles Display types directly
                arg = args[0].removesuffix(".to_string()") if args[0].endswith(".to_string()") else args[0]
                # If arg is a string literal, use println!("literal") directly
                # to avoid clippy::print_literal warning
                if arg.startswith('"') and arg.endswith('"'):
                    return f"println!({arg})"
                return f'println!("{{}}", {arg})'
            return "println!()"

        # Handle str()
        if func == "str":
            return f"{args[0]}.to_string()"

        # Handle int()
        if func == "int":
            # If the argument looks like a string, use parse()
            arg = args[0]
            if arg.endswith(".to_string()") or arg.startswith('"'):
                return f"{arg}.parse::<i64>().unwrap()"
            # For variables, we assume they might be strings if they're not numeric literals
            if not arg.lstrip("-").isdigit():
                return f"{arg}.parse::<i64>().unwrap()"
            return f"{arg} as i64"

        # Handle float()
        if func == "float":
            return f"{args[0]} as f64"

        # Regular function call - check if it returns Result
        call_expr = f"{func}({', '.join(args)})"

        # Append ? if calling a Result-returning function inside a Result context
        if self.ctx.in_result_context and func in self.ctx.result_functions:
            call_expr += "?"

        return call_expr

    def _infer_stub_type(self, expr: IRExpression) -> str | None:
        """Infer the stub type of an expression for method chaining.

        For expressions like Arg.new(...).short(...), we need to know that
        Arg.new(...) returns an Arg type so we can look up the short() method.

        Returns the type name (e.g., "Arg") if it can be inferred, None otherwise.
        """
        # Simple variable with known type
        if isinstance(expr, IRName):
            if expr.name in self.ctx.type_env:
                var_type = self.ctx.type_env[expr.name]
                return var_type.split(".")[-1]
            # Check if this is a stub type name (e.g., Arg, Command)
            if expr.name in self.ctx.stub_imports:
                return expr.name
            return None

        # Method call on a stub type: Type.method(...) -> Type (if returns_self)
        # or method call chain: expr.method(...) where expr is a stub type
        if isinstance(expr, IRMethodCall):
            # Check if this is Type.new(...) pattern - static method on stub type
            if isinstance(expr.obj, IRName) and expr.obj.name in self.ctx.stub_imports:
                # Type.method() where Type is a stub type - returns the Type
                return expr.obj.name

            # Otherwise, try to infer the type of the receiver for chained calls
            receiver_type = self._infer_stub_type(expr.obj)
            if receiver_type:
                # Check if this method returns_self (builder pattern)
                stub_mapping = get_stub_method_mapping(receiver_type, expr.method)
                if stub_mapping:
                    # For now, assume builder methods return self
                    # The mapping has returns_self but we're not using it yet
                    return receiver_type
            return None

        # Call on a stub type constructor: Type.new(...) -> Type
        if isinstance(expr, IRCall):
            if isinstance(expr.func, IRAttribute):
                # Type.method() pattern
                if isinstance(expr.func.obj, IRName):
                    type_name = expr.func.obj.name
                    # Check if this is a constructor-like static method (new, from, etc.)
                    if type_name in self.ctx.stub_imports:
                        # It's a known stub type, the result type is the type itself
                        return type_name
            return None

        return None

    def _inject_turbofish(self, rust_code: str, method: str) -> str:
        """Inject turbofish type parameter for generic methods.

        For methods like get_one that need ::<Type>, inject based on
        the assignment target type context.
        """
        # Methods that need turbofish type inference
        turbofish_methods = {"get_one", "try_get_one", "get_many", "try_get_many"}

        if method not in turbofish_methods:
            return rust_code

        target_type = self.ctx.assignment_target_type
        if not target_type:
            # Default to String for get_one/get_many when no type annotation
            # This is the most common case for clap argument retrieval
            target_type = "String"

        # Insert turbofish after the method name
        # Pattern: .get_one( -> .get_one::<Type>(
        old_pattern = f".{method}("
        new_pattern = f".{method}::<{target_type}>("
        return rust_code.replace(old_pattern, new_pattern)

    def _transform_arg_for_type(self, arg: str, rust_type: str) -> str:
        """Transform an argument based on expected Rust type.

        Handles char and &str types that don't accept String.
        """
        # Handle char type: "x".to_string() -> 'x'
        # Also handles wrapped types like implIntoResettable<char>
        if rust_type == "char" or "char>" in rust_type or "<char" in rust_type:
            # Extract the character from "x".to_string()
            # Pattern: "x".to_string() -> suffix is ".to_string() (13 chars)
            if arg.startswith('"') and arg.endswith(".to_string()"):
                char_val = arg[1:-13]  # Remove " prefix and ".to_string() suffix
                if len(char_val) == 1:
                    return f"'{char_val}'"
            # Already a char literal
            if arg.startswith("'") and arg.endswith("'"):
                return arg

        # Handle &str type: "x".to_string() -> "x"
        # Also handles wrapped types containing &str
        if rust_type in ("&str", "&'static str", "&'staticstr") or "&str" in rust_type:
            if arg.endswith(".to_string()"):
                return arg[:-12]  # Remove .to_string()

        # Handle impl Into<Str> which accepts &str but NOT String
        # clap's Str type only implements From<&str>, not From<String>
        if "Str>" in rust_type or rust_type.endswith("Str"):
            if arg.endswith(".to_string()"):
                return arg[:-12]  # Remove .to_string()

        # Handle impl Into<Id> which accepts &str but NOT String
        # clap's Id type only implements From<&str>, not From<String>
        if "Id>" in rust_type or rust_type.endswith("Id"):
            if arg.endswith(".to_string()"):
                return arg[:-12]  # Remove .to_string()
            # Handle vec of strings for args([...]) pattern
            if arg.startswith("vec!["):
                # Strip .to_string() from each element in the vec
                import re

                return re.sub(r'"([^"]*)"\.to_string\(\)', r'"\1"', arg)

        return arg

    def _apply_stdlib_mapping(self, mapping: StdlibMapping, args: list[str]) -> str:
        """Apply a stdlib mapping to generate Rust code."""

        rust_code = mapping.rust_code

        # Transform args based on param_types if available
        # Use getattr since not all mapping types have param_types
        param_types = getattr(mapping, "param_types", None)
        if param_types:
            transformed_args = []
            for i, arg in enumerate(args):
                if i < len(param_types):
                    arg = self._transform_arg_for_type(arg, param_types[i])
                transformed_args.append(arg)
            args = transformed_args

        # Handle different placeholder formats
        if "{args}" in rust_code:
            rust_code = rust_code.format(args=", ".join(args))
        elif "{arg0}" in rust_code or "{arg1}" in rust_code:
            # Handle indexed args
            replacements = {f"arg{i}": arg for i, arg in enumerate(args)}
            for key, val in replacements.items():
                rust_code = rust_code.replace(f"{{{key}}}", val)

        # Track required imports
        for imp in mapping.rust_imports:
            self.ctx.stdlib_imports.add(imp)

        return rust_code

    def _apply_datetime_constructor(self, mapping: StdlibMapping, args: list[str], expr: IRMethodCall) -> str:
        """Apply a datetime constructor mapping, handling keyword arguments."""

        rust_code = mapping.rust_code

        # Build keyword args dict from the expression
        kwargs: dict[str, str] = {}
        if hasattr(expr, "kwargs") and expr.kwargs:
            for key, val_expr in expr.kwargs.items():
                kwargs[key] = self.emit_expression(val_expr)

        # Handle datetime.date(year, month, day)
        if mapping.python_func == "date" and mapping.python_module == "datetime":
            if len(args) == 3:
                rust_code = rust_code.replace("{args}", ", ".join(args))
            for imp in mapping.rust_imports:
                self.ctx.stdlib_imports.add(imp)
            return rust_code

        # Handle datetime.time(hour, minute, second, microsecond)
        if mapping.python_func == "time" and mapping.python_module == "datetime":
            # Pad with defaults: hour=0, minute=0, second=0, microsecond=0
            while len(args) < 4:
                args.append("0")
            rust_code = rust_code.replace("{args}", ", ".join(args))
            for imp in mapping.rust_imports:
                self.ctx.stdlib_imports.add(imp)
            return rust_code

        # Handle datetime.datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0)
        if mapping.python_func == "datetime" and "{year}" in rust_code:
            defaults = {
                "year": "0",
                "month": "1",
                "day": "1",
                "hour": "0",
                "minute": "0",
                "second": "0",
                "microsecond": "0",
            }
            # Fill from positional args in order
            arg_names = ["year", "month", "day", "hour", "minute", "second", "microsecond"]
            for i, arg in enumerate(args):
                if i < len(arg_names):
                    defaults[arg_names[i]] = arg
            # Override with keyword args
            defaults.update(kwargs)
            for key, val in defaults.items():
                rust_code = rust_code.replace(f"{{{key}}}", val)
            for imp in mapping.rust_imports:
                self.ctx.stdlib_imports.add(imp)
            return rust_code

        # Handle datetime.timedelta(days=0, seconds=0, microseconds=0, ...)
        if mapping.python_func == "timedelta":
            defaults = {
                "days": "0",
                "seconds": "0",
                "microseconds": "0",
                "milliseconds": "0",
                "minutes": "0",
                "hours": "0",
                "weeks": "0",
            }
            # Fill from positional args in order
            arg_names = [
                "days",
                "seconds",
                "microseconds",
                "milliseconds",
                "minutes",
                "hours",
                "weeks",
            ]
            for i, arg in enumerate(args):
                if i < len(arg_names):
                    defaults[arg_names[i]] = arg
            # Override with keyword args
            defaults.update(kwargs)

            # Build the duration expression
            # chrono::Duration doesn't have all these, so we combine them
            parts = []
            if defaults["weeks"] != "0":
                parts.append(f"chrono::Duration::weeks({defaults['weeks']})")
            if defaults["days"] != "0":
                parts.append(f"chrono::Duration::days({defaults['days']})")
            if defaults["hours"] != "0":
                parts.append(f"chrono::Duration::hours({defaults['hours']})")
            if defaults["minutes"] != "0":
                parts.append(f"chrono::Duration::minutes({defaults['minutes']})")
            if defaults["seconds"] != "0":
                parts.append(f"chrono::Duration::seconds({defaults['seconds']})")
            if defaults["milliseconds"] != "0":
                parts.append(f"chrono::Duration::milliseconds({defaults['milliseconds']})")
            if defaults["microseconds"] != "0":
                parts.append(f"chrono::Duration::microseconds({defaults['microseconds']})")

            if not parts:
                result = "chrono::Duration::zero()"
            else:
                result = " + ".join(parts)
            # Track required imports
            for imp in mapping.rust_imports:
                self.ctx.stdlib_imports.add(imp)
            return result

        # For simple mappings, just replace {args}
        if "{args}" in rust_code:
            rust_code = rust_code.replace("{args}", ", ".join(args))

        # Track required imports
        for imp in mapping.rust_imports:
            self.ctx.stdlib_imports.add(imp)

        return rust_code

    def _emit_method_call(self, expr: IRMethodCall) -> str:
        """Emit a method call."""
        args = [self.emit_expression(a) for a in expr.args]
        method = expr.method

        # Check for stub package Type.method calls (e.g., Result.Ok(), Error.msg())
        if isinstance(expr.obj, IRName):
            type_name = expr.obj.name
            if type_name in self.ctx.stub_imports:
                crate_name = self.ctx.stub_imports[type_name]
                # Look up the full mapping key: crate.Type.method (e.g., "anyhow.Result.Ok")
                full_key = f"{crate_name}.{type_name}.{method}"
                mapping = get_stub_mapping(full_key)
                if mapping:
                    result = self._apply_stdlib_mapping(mapping, args)
                    # Add ? for Result-returning stub calls in Result context
                    if mapping.needs_result and self.ctx.in_result_context:
                        if result.endswith(".unwrap()"):
                            result = result[:-9] + "?"
                    return result

        # Check for stdlib module.function calls (e.g., os.getcwd(), json.loads())
        if isinstance(expr.obj, IRName):
            module = expr.obj.name
            mapping = get_stdlib_mapping(module, method)
            if mapping:
                result = self._apply_stdlib_mapping(mapping, args)
                # Add ? for Result-returning stdlib calls in Result context
                if mapping.needs_result and self.ctx.in_result_context:
                    if result.endswith(".unwrap()"):
                        result = result[:-9] + "?"
                return result

            # Check for datetime module constructor/class method calls
            # e.g., datetime.date(2024, 1, 15), datetime.timedelta(days=5)
            full_key = f"{module}.{method}"
            dt_mapping = get_datetime_mapping(full_key)
            if dt_mapping:
                result = self._apply_datetime_constructor(dt_mapping, args, expr)
                if dt_mapping.needs_result and self.ctx.in_result_context:
                    if result.endswith(".unwrap()"):
                        result = result[:-9] + "?"
                return result

            # Check for typed variable method calls (e.g., dt.isoformat() for datetime)
            if module in self.ctx.type_env:
                var_type = self.ctx.type_env[module]
                # Extract class name from type (e.g., "datetime.datetime" -> "datetime")
                class_name = var_type.split(".")[-1]
                # Look up method mapping with full key (e.g., "datetime.isoformat")
                method_key = f"{class_name}.{method}"
                method_mapping = get_datetime_method_mapping(method_key)
                if method_mapping:
                    obj = self.emit_expression(expr.obj)
                    rust_code = method_mapping.rust_code.replace("{self}", obj)
                    # Replace argument placeholders if present
                    if "{args}" in rust_code:
                        rust_code = rust_code.replace("{args}", ", ".join(args))
                    elif args:
                        # Handle indexed args {arg0}, {arg1}, etc.
                        for i, arg in enumerate(args):
                            rust_code = rust_code.replace(f"{{arg{i}}}", arg)
                    for imp in method_mapping.rust_imports:
                        self.ctx.stdlib_imports.add(imp)
                    return rust_code

                # Check for stub method mapping (e.g., Command.about() for clap)
                stub_mapping = get_stub_method_mapping(class_name, method)
                if stub_mapping:
                    obj = self.emit_expression(expr.obj)
                    # Transform args based on param_types
                    if stub_mapping.param_types:
                        transformed_args = []
                        for i, arg in enumerate(args):
                            if i < len(stub_mapping.param_types):
                                arg = self._transform_arg_for_type(arg, stub_mapping.param_types[i])
                            transformed_args.append(arg)
                        args = transformed_args
                    rust_code = stub_mapping.rust_code.replace("{self}", obj)
                    # Inject turbofish for generic methods like get_one
                    rust_code = self._inject_turbofish(rust_code, method)
                    # Replace argument placeholders if present
                    if "{args}" in rust_code:
                        rust_code = rust_code.replace("{args}", ", ".join(args))
                    elif args:
                        # Handle indexed args {arg0}, {arg1}, etc.
                        for i, arg in enumerate(args):
                            rust_code = rust_code.replace(f"{{arg{i}}}", arg)
                    for imp in stub_mapping.rust_imports:
                        self.ctx.stdlib_imports.add(imp)
                    return rust_code

        # Check for chained stub method calls (e.g., Arg.new(...).short(...))
        # Try to infer the type from the expression chain
        inferred_type = self._infer_stub_type(expr.obj)
        if inferred_type:
            stub_mapping = get_stub_method_mapping(inferred_type, method)
            if stub_mapping:
                obj = self.emit_expression(expr.obj)
                # Transform args based on param_types
                if stub_mapping.param_types:
                    transformed_args = []
                    for i, arg in enumerate(args):
                        if i < len(stub_mapping.param_types):
                            arg = self._transform_arg_for_type(arg, stub_mapping.param_types[i])
                        transformed_args.append(arg)
                    args = transformed_args
                rust_code = stub_mapping.rust_code.replace("{self}", obj)
                # Inject turbofish for generic methods like get_one
                rust_code = self._inject_turbofish(rust_code, method)
                # Replace argument placeholders if present
                if "{args}" in rust_code:
                    rust_code = rust_code.replace("{args}", ", ".join(args))
                elif args:
                    # Handle indexed args {arg0}, {arg1}, etc.
                    for i, arg in enumerate(args):
                        rust_code = rust_code.replace(f"{{arg{i}}}", arg)
                for imp in stub_mapping.rust_imports:
                    self.ctx.stdlib_imports.add(imp)
                return rust_code

        # Check for nested stdlib calls (e.g., os.path.exists())
        if isinstance(expr.obj, IRAttribute) and isinstance(expr.obj.obj, IRName):
            module = f"{expr.obj.obj.name}.{expr.obj.attr}"
            mapping = get_stdlib_mapping(module, method)
            if mapping:
                result = self._apply_stdlib_mapping(mapping, args)
                if mapping.needs_result and self.ctx.in_result_context:
                    if result.endswith(".unwrap()"):
                        result = result[:-9] + "?"
                return result

            # Check for datetime module nested calls (e.g., datetime.datetime.now())
            full_key = f"{module}.{method}"
            dt_mapping = get_datetime_mapping(full_key)
            if dt_mapping:
                result = self._apply_stdlib_mapping(dt_mapping, args)
                if dt_mapping.needs_result and self.ctx.in_result_context:
                    if result.endswith(".unwrap()"):
                        result = result[:-9] + "?"
                return result

        # Handle Result/Option static method calls
        # Result.unwrap(x) -> x.unwrap(), Result.expect(x, msg) -> x.expect(msg), etc.
        if isinstance(expr.obj, IRName):
            type_name = expr.obj.name
            if type_name in ("Result", "Option") and args:
                # Methods that take (self) only
                if method in ("unwrap", "unwrap_err", "is_ok", "is_err", "is_some", "is_none"):
                    return f"{args[0]}.{method}()"
                # Methods that take (self, value)
                if method == "unwrap_or":
                    if len(args) >= 2:
                        return f"{args[0]}.{method}({args[1]})"
                # expect/expect_err take &str, not String
                if method in ("expect", "expect_err"):
                    if len(args) >= 2:
                        # Strip .to_string() since expect takes &str
                        msg = (
                            args[1].removesuffix(".to_string()") if args[1].endswith(".to_string()") else f"&{args[1]}"
                        )
                        return f"{args[0]}.{method}({msg})"
                # Methods that take (self, closure)
                if method in ("unwrap_or_else", "map", "map_err", "and_then", "or_else"):
                    if len(args) >= 2:
                        return f"{args[0]}.{method}({args[1]})"
                # Methods that take (self, default, closure)
                if method in ("map_or", "map_or_else"):
                    if len(args) >= 3:
                        return f"{args[0]}.{method}({args[1]}, {args[2]})"
                # ok_or / ok_or_else for Option
                if method in ("ok_or", "ok_or_else"):
                    if len(args) >= 2:
                        return f"{args[0]}.{method}({args[1]})"

        obj = self.emit_expression(expr.obj)

        # Handle .clone() -> .to_string() when target type is String
        # This handles &str -> String conversion which .clone() doesn't do
        # Methods like subcommand_name() return &str, so .clone() gives &str not String
        if method == "clone":
            target_type = self.ctx.assignment_target_type
            if target_type and target_type == "String":
                return f"{obj}.to_string()"

        # String methods
        if method == "append":
            return f"{obj}.push({args[0]})"
        if method == "extend":
            return f"{obj}.extend({args[0]})"
        if method == "pop":
            return f"{obj}.pop()"
        if method == "strip":
            return f"{obj}.trim().to_string()"
        if method == "split":
            if args:
                return f"{obj}.split({args[0]}).collect::<Vec<_>>()"
            return f"{obj}.split_whitespace().collect::<Vec<_>>()"
        if method == "join":
            return f"{args[0]}.join(&{obj})"
        if method == "upper":
            return f"{obj}.to_uppercase()"
        if method == "lower":
            return f"{obj}.to_lowercase()"
        if method == "replace":
            # replace takes &str, not String, so strip .to_string() if present
            arg0 = args[0].removesuffix(".to_string()") if args[0].endswith(".to_string()") else f"&{args[0]}"
            arg1 = args[1].removesuffix(".to_string()") if args[1].endswith(".to_string()") else f"&{args[1]}"
            return f"{obj}.replace({arg0}, {arg1})"
        if method == "startswith":
            arg = args[0].removesuffix(".to_string()") if args[0].endswith(".to_string()") else f"&{args[0]}"
            return f"{obj}.starts_with({arg})"
        if method == "endswith":
            arg = args[0].removesuffix(".to_string()") if args[0].endswith(".to_string()") else f"&{args[0]}"
            return f"{obj}.ends_with({arg})"
        if method == "isdigit":
            return f"{obj}.chars().all(|c| c.is_ascii_digit())"
        if method == "isalpha":
            return f"{obj}.chars().all(|c| c.is_alphabetic())"
        if method == "isalnum":
            return f"{obj}.chars().all(|c| c.is_alphanumeric())"
        if method == "isspace":
            return f"{obj}.chars().all(|c| c.is_whitespace())"

        # Dict methods (only apply if args present to distinguish from user methods)
        if method == "get" and args:
            if len(args) >= 2:
                return f"{obj}.get(&{args[0]}).cloned().unwrap_or({args[1]})"
            return f"{obj}.get(&{args[0]}).cloned()"
        if method == "keys":
            return f"{obj}.keys()"
        if method == "values":
            return f"{obj}.values()"
        if method == "items":
            return f"{obj}.iter()"

        # Escape Rust keywords used as method names
        rust_keywords = {
            "use",
            "type",
            "impl",
            "trait",
            "mod",
            "pub",
            "fn",
            "let",
            "mut",
            "ref",
            "move",
            "self",
            "super",
            "crate",
            "as",
            "break",
            "continue",
            "else",
            "for",
            "if",
            "in",
            "loop",
            "match",
            "return",
            "while",
            "async",
            "await",
            "dyn",
            "struct",
            "enum",
            "union",
            "const",
            "static",
            "extern",
            "unsafe",
            "where",
        }
        method_name = f"r#{method}" if method in rust_keywords else method

        call_expr = f"{obj}.{method_name}({', '.join(args)})"

        # Append ? if calling a Result-returning method inside a Result context
        if self.ctx.in_result_context and method in self.ctx.result_functions:
            call_expr += "?"

        return call_expr

    def _emit_list_comp(self, expr: IRListComp) -> str:
        """Emit a list comprehension as iterator."""
        iter_expr = self.emit_expression(expr.iter)
        element = self.emit_expression(expr.element)

        result = f"{iter_expr}.iter()"

        # Add filter if there are conditions
        for cond in expr.conditions:
            cond_expr = self.emit_expression(cond)
            result += f".filter(|{expr.target}| {cond_expr})"

        result += f".map(|{expr.target}| {element})"
        result += ".collect::<Vec<_>>()"

        return result

    def _emit_fstring(self, expr: IRFString) -> str:
        """Emit an f-string as format!()."""
        format_str = ""
        args: list[str] = []

        for part in expr.parts:
            if isinstance(part, IRLiteral) and isinstance(part.value, str):
                # Literal string part - escape braces
                escaped = part.value.replace("{", "{{").replace("}", "}}")
                format_str += escaped
            else:
                # Expression part
                format_str += "{}"
                args.append(self.emit_expression(part))

        if args:
            return f'format!("{format_str}", {", ".join(args)})'
        return f'"{format_str}".to_string()'


def emit_module(module: IRModule, resolver: TypeResolver | None = None) -> str:
    """Convenience function to emit a module."""
    emitter = RustEmitter(resolver)
    return emitter.emit_module(module)
