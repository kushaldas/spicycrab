"""Rust code emitter for spicycrab.

Converts IR nodes to Rust source code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from spicycrab.analyzer.type_resolver import TypeResolver, RustType
from spicycrab.ir.nodes import (
    BinaryOp,
    IRAssign,
    IRAttrAssign,
    IRAttribute,
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
    IRRaise,
    IRReturn,
    IRSet,
    IRStatement,
    IRSubscript,
    IRTry,
    IRTuple,
    IRType,
    IRUnaryOp,
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

    def indent_str(self) -> str:
        return "    " * self.indent


class RustEmitter:
    """Emits Rust code from IR nodes."""

    def __init__(self, resolver: TypeResolver | None = None) -> None:
        self.resolver = resolver or TypeResolver()
        self.ctx = EmitterContext(resolver=self.resolver)
        self.output: list[str] = []

    def emit_module(self, module: IRModule) -> str:
        """Emit a complete Rust module."""
        lines: list[str] = []

        # Module docstring as comment
        if module.docstring:
            lines.append(f"//! {module.docstring.split(chr(10))[0]}")
            lines.append("")

        # Standard imports
        imports = self._collect_imports(module)
        if imports:
            lines.extend(imports)
            lines.append("")

        # Emit classes as structs
        for cls in module.classes:
            lines.append(self.emit_class(cls))
            lines.append("")

        # Emit functions
        for func in module.functions:
            lines.append(self.emit_function(func))
            lines.append("")

        # Emit top-level statements in main() if any
        if module.statements:
            lines.append("fn main() {")
            self.ctx.indent = 1
            for stmt in module.statements:
                lines.append(self.emit_statement(stmt))
            self.ctx.indent = 0
            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _collect_imports(self, module: IRModule) -> list[str]:
        """Collect required Rust imports."""
        imports = set()

        # Check if module uses HashMap or HashSet
        needs_collections = self._needs_collections(module)
        if needs_collections:
            imports.add("use std::collections::{HashMap, HashSet};")

        # Add resolver-detected imports
        imports.update(self.resolver.get_imports())

        return sorted(imports)

    def _needs_collections(self, module: IRModule) -> bool:
        """Check if module uses HashMap or HashSet."""
        # Quick check via string representation - not ideal but works
        for func in module.functions:
            for stmt in func.body:
                if self._stmt_needs_collections(stmt):
                    return True
        for cls in module.classes:
            for method in cls.methods:
                for stmt in method.body:
                    if self._stmt_needs_collections(stmt):
                        return True
        return False

    def _stmt_needs_collections(self, stmt: IRStatement) -> bool:
        """Check if statement uses collections."""
        if isinstance(stmt, IRAssign) and stmt.value:
            return self._expr_needs_collections(stmt.value)
        if isinstance(stmt, IRExprStmt):
            return self._expr_needs_collections(stmt.expr)
        if isinstance(stmt, IRReturn) and stmt.value:
            return self._expr_needs_collections(stmt.value)
        if isinstance(stmt, IRFor):
            return self._expr_needs_collections(stmt.iter) or any(
                self._stmt_needs_collections(s) for s in stmt.body
            )
        if isinstance(stmt, IRIf):
            return (
                any(self._stmt_needs_collections(s) for s in stmt.then_body) or
                any(self._stmt_needs_collections(s) for s in stmt.else_body)
            )
        return False

    def _expr_needs_collections(self, expr: IRExpression) -> bool:
        """Check if expression uses collections."""
        if isinstance(expr, IRDict):
            return True
        if isinstance(expr, IRSet):
            return True
        if isinstance(expr, IRCall):
            return any(self._expr_needs_collections(a) for a in expr.args)
        if isinstance(expr, IRBinaryOp):
            return (
                self._expr_needs_collections(expr.left) or
                self._expr_needs_collections(expr.right)
            )
        return False

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

        # Impl block for methods
        if cls.methods:
            lines.append(f"{indent}impl {cls.name} {{")
            self.ctx.indent += 1
            self.ctx.in_impl = True
            self.ctx.current_class = cls.name

            for method in cls.methods:
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

        # Build parameter list
        params: list[str] = []
        is_constructor = method.name == "__init__"

        if not is_constructor and method.is_method:
            # Add self parameter
            params.append("&self")

        for param in method.params:
            rust_type = self.resolver.resolve(param.type)
            params.append(f"{param.name}: {rust_type.to_rust()}")

        params_str = ", ".join(params)

        # Return type
        if is_constructor:
            ret_str = f" -> Self"
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
                    lines.append(f"{field_indent}{stmt.attr}: {self.emit_expression(stmt.value)},")
            self.ctx.indent -= 1
            lines.append(f"{inner_indent}}}")
            self.ctx.indent -= 1
        else:
            # Regular method body
            self.ctx.indent += 1
            for stmt in method.body:
                lines.append(self.emit_statement(stmt))
            self.ctx.indent -= 1

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

        lines.append(f"{indent}pub fn {func.name}({params_str}){ret_str} {{")

        # Body - mark last statement for expression return
        self.ctx.indent += 1
        for i, stmt in enumerate(func.body):
            is_last = (i == len(func.body) - 1)
            self.ctx.in_last_stmt = is_last
            lines.append(self.emit_statement(stmt))
        self.ctx.in_last_stmt = False
        self.ctx.indent -= 1

        lines.append(f"{indent}}}")

        return "\n".join(lines)

    def emit_statement(self, stmt: IRStatement) -> str:
        """Emit a statement."""
        indent = self.ctx.indent_str()

        if isinstance(stmt, IRAssign):
            return self._emit_assign(stmt)

        if isinstance(stmt, IRAttrAssign):
            return f"{indent}self.{stmt.attr} = {self.emit_expression(stmt.value)};"

        if isinstance(stmt, IRReturn):
            if stmt.value:
                expr = self.emit_expression(stmt.value)
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
                return f"{indent}return Err({self.emit_expression(stmt.exc)});"
            return f"{indent}panic!(\"re-raise\");"

        return f"{indent}// Unsupported: {type(stmt).__name__}"

    def _emit_assign(self, stmt: IRAssign) -> str:
        """Emit an assignment statement."""
        indent = self.ctx.indent_str()
        value = self.emit_expression(stmt.value)

        if stmt.is_declaration:
            # Only add mut if explicitly marked mutable (reassigned later)
            mut = "mut " if stmt.is_mutable else ""
            if stmt.type_annotation:
                rust_type = self.resolver.resolve(stmt.type_annotation)
                return f"{indent}let {mut}{stmt.target}: {rust_type.to_rust()} = {value};"
            return f"{indent}let {mut}{stmt.target} = {value};"
        else:
            return f"{indent}{stmt.target} = {value};"

    def _emit_if(self, stmt: IRIf) -> str:
        """Emit an if statement."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        cond = self.emit_expression(stmt.condition)
        lines.append(f"{indent}if {cond} {{")

        self.ctx.indent += 1
        for s in stmt.then_body:
            lines.append(self.emit_statement(s))
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

        if stmt.target:
            lines.append(f"{inner_indent}let {stmt.target} = {ctx_expr};")
        else:
            lines.append(f"{inner_indent}let _ctx = {ctx_expr};")

        for s in stmt.body:
            lines.append(self.emit_statement(s))

        self.ctx.indent -= 1
        lines.append(f"{indent}}} // drop")

        return "\n".join(lines)

    def _emit_try(self, stmt: IRTry) -> str:
        """Emit try/except as match on Result."""
        lines: list[str] = []
        indent = self.ctx.indent_str()

        lines.append(f"{indent}// try/except translated to Result handling")
        lines.append(f"{indent}{{")
        self.ctx.indent += 1

        for s in stmt.body:
            lines.append(self.emit_statement(s))

        self.ctx.indent -= 1
        lines.append(f"{indent}}}")

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
            obj = self.emit_expression(expr.obj)
            return f"{obj}.{expr.attr}"

        if isinstance(expr, IRSubscript):
            obj = self.emit_expression(expr.obj)
            index = self.emit_expression(expr.index)
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
        left = self.emit_expression(expr.left)
        right = self.emit_expression(expr.right)

        # Special handling for floor division
        if expr.op == BinaryOp.FLOOR_DIV:
            return f"{left} / {right}"

        # Special handling for power
        if expr.op == BinaryOp.POW:
            return f"({left} as f64).powf({right} as f64) as i64"

        op = BINOP_MAP.get(expr.op, "+")
        return f"{left} {op} {right}"

    def _emit_call(self, expr: IRCall) -> str:
        """Emit a function call."""
        func = self.emit_expression(expr.func)
        args = [self.emit_expression(a) for a in expr.args]

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
                return f'println!("{{}}", {args[0]})'
            return 'println!()'

        # Handle str()
        if func == "str":
            return f"{args[0]}.to_string()"

        # Handle int()
        if func == "int":
            return f"{args[0]} as i64"

        # Handle float()
        if func == "float":
            return f"{args[0]} as f64"

        return f"{func}({', '.join(args)})"

    def _emit_method_call(self, expr: IRMethodCall) -> str:
        """Emit a method call."""
        obj = self.emit_expression(expr.obj)
        args = [self.emit_expression(a) for a in expr.args]

        method = expr.method

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
                return f'{obj}.split({args[0]}).collect::<Vec<_>>()'
            return f'{obj}.split_whitespace().collect::<Vec<_>>()'
        if method == "join":
            return f"{args[0]}.join(&{obj})"
        if method == "upper":
            return f"{obj}.to_uppercase()"
        if method == "lower":
            return f"{obj}.to_lowercase()"
        if method == "replace":
            return f"{obj}.replace({args[0]}, {args[1]})"
        if method == "startswith":
            return f"{obj}.starts_with({args[0]})"
        if method == "endswith":
            return f"{obj}.ends_with({args[0]})"

        # Dict methods
        if method == "get":
            if len(args) >= 2:
                return f"{obj}.get(&{args[0]}).cloned().unwrap_or({args[1]})"
            return f"{obj}.get(&{args[0]}).cloned()"
        if method == "keys":
            return f"{obj}.keys()"
        if method == "values":
            return f"{obj}.values()"
        if method == "items":
            return f"{obj}.iter()"

        return f"{obj}.{method}({', '.join(args)})"

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
