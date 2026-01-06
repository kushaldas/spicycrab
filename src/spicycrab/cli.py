"""Command-line interface for spicycrab."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click

from spicycrab import __version__
from spicycrab.analyzer.type_resolver import TypeResolver, resolve_types
from spicycrab.codegen.cargo import generate_cargo_toml, generate_main_rs
from spicycrab.codegen.emitter import RustEmitter, emit_module
from spicycrab.parser import parse_file, parse_source
from spicycrab.utils.errors import CrabpyError


@click.group(invoke_without_command=True)
@click.option("--version", "-V", is_flag=True, help="Show version and exit.")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """crabpy - A Python to Rust transpiler for type-annotated Python code."""
    if version:
        click.echo(f"crabpy {__version__}")
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@main.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./rusty",
    help="Output directory for the Rust project (default: ./rusty).",
)
@click.option(
    "--check", "-c",
    is_flag=True,
    help="Only check if the input can be parsed, don't generate output.",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output.",
)
@click.option(
    "--format/--no-format",
    default=True,
    help="Run rustfmt on generated code (default: enabled).",
)
@click.option(
    "--name", "-n",
    type=str,
    default=None,
    help="Project name (default: derived from input file/directory name).",
)
def transpile(
    input_path: str,
    output: str,
    check: bool,
    verbose: bool,
    format: bool,
    name: str | None,
) -> None:
    """Transpile Python code to Rust.

    INPUT_PATH can be a Python file (.py) or a directory containing Python files.
    Output is written to the --output directory (default: ./rusty).
    """
    path = Path(input_path)
    output_dir = Path(output)

    try:
        if path.is_file():
            _transpile_file(path, output_dir, check, verbose, format, name)
        elif path.is_dir():
            _transpile_directory(path, output_dir, check, verbose, format, name)
        else:
            raise click.ClickException(f"Invalid input path: {input_path}")
    except CrabpyError as e:
        raise click.ClickException(str(e)) from e


def _transpile_file(
    input_path: Path,
    output_dir: Path,
    check: bool,
    verbose: bool,
    format_code: bool,
    project_name: str | None,
) -> None:
    """Transpile a single Python file."""
    if verbose:
        click.echo(f"Parsing {input_path}...")

    ir_module = parse_file(input_path)

    if verbose:
        click.echo(f"  Found {len(ir_module.functions)} function(s)")
        click.echo(f"  Found {len(ir_module.classes)} class(es)")
        click.echo(f"  Found {len(ir_module.imports)} import(s)")

    if check:
        click.echo(click.style(f"OK: {input_path}", fg="green"))
        return

    # Determine project name
    name = project_name or input_path.stem.replace("-", "_")

    # Create output directory structure
    output_dir.mkdir(parents=True, exist_ok=True)
    src_dir = output_dir / "src"
    src_dir.mkdir(exist_ok=True)

    if verbose:
        click.echo(f"Generating Rust project in {output_dir}...")

    # Resolve types
    resolver = resolve_types(ir_module)

    # Generate Rust code
    emitter = RustEmitter(resolver)
    rust_code = emitter.emit_module(ir_module)

    # Determine if this is a library or binary
    has_main = any(f.name == "main" for f in ir_module.functions)

    # Write main.rs or lib.rs
    if has_main:
        main_rs = src_dir / "main.rs"
        main_rs.write_text(rust_code)
        if verbose:
            click.echo(f"  Wrote {main_rs}")
    else:
        # For modules without main, generate a library
        lib_rs = src_dir / "lib.rs"
        lib_rs.write_text(rust_code)
        if verbose:
            click.echo(f"  Wrote {lib_rs}")

        # Also generate a simple main.rs that uses the library
        main_rs = src_dir / "main.rs"
        main_content = generate_main_rs(None)
        main_rs.write_text(main_content)
        if verbose:
            click.echo(f"  Wrote {main_rs}")

    # Generate Cargo.toml
    cargo_toml = output_dir / "Cargo.toml"
    cargo_content = generate_cargo_toml(
        name=name,
        modules=[ir_module],
        is_library=not has_main,
    )
    cargo_toml.write_text(cargo_content)
    if verbose:
        click.echo(f"  Wrote {cargo_toml}")

    # Run rustfmt if requested
    if format_code:
        _run_rustfmt(output_dir, verbose)

    click.echo(click.style(
        f"✓ Transpiled {input_path} to {output_dir}",
        fg="green",
    ))


def _transpile_directory(
    input_path: Path,
    output_dir: Path,
    check: bool,
    verbose: bool,
    format_code: bool,
    project_name: str | None,
) -> None:
    """Transpile a directory of Python files."""
    py_files = list(input_path.rglob("*.py"))

    # Filter out __pycache__ and hidden directories
    py_files = [
        f for f in py_files
        if "__pycache__" not in str(f) and not any(
            part.startswith(".") for part in f.parts
        )
    ]

    if not py_files:
        raise click.ClickException(f"No Python files found in {input_path}")

    if verbose:
        click.echo(f"Found {len(py_files)} Python file(s)")

    # Determine project name
    name = project_name or input_path.name.replace("-", "_")

    if check:
        # Just validate all files
        success_count = 0
        error_count = 0

        for py_file in py_files:
            try:
                if verbose:
                    click.echo(f"Checking {py_file}...")
                parse_file(py_file)
                success_count += 1
                click.echo(click.style(f"OK: {py_file}", fg="green"))
            except CrabpyError as e:
                error_count += 1
                click.echo(click.style(f"Error in {py_file}: {e}", fg="red"), err=True)

        click.echo(f"\nChecked {len(py_files)} file(s): {success_count} OK, {error_count} error(s)")
        return

    # Create output directory structure
    output_dir.mkdir(parents=True, exist_ok=True)
    src_dir = output_dir / "src"
    src_dir.mkdir(exist_ok=True)

    if verbose:
        click.echo(f"Generating Rust project in {output_dir}...")

    # Parse all modules and collect IR
    modules = []
    module_names = []
    has_main = False

    for py_file in py_files:
        try:
            if verbose:
                click.echo(f"Processing {py_file}...")
            ir_module = parse_file(py_file)
            modules.append(ir_module)

            # Track module name
            module_name = py_file.stem.replace("-", "_")
            if module_name != "__init__":
                module_names.append(module_name)

            # Check if any module has main
            if any(f.name == "main" for f in ir_module.functions):
                has_main = True

        except CrabpyError as e:
            click.echo(click.style(f"Error in {py_file}: {e}", fg="red"), err=True)

    # Create set of local module names for import resolution
    local_module_set = set(module_names)

    # Find which module has main (will become main.rs)
    main_module_name = None
    for module, py_file in zip(modules, py_files):
        if any(f.name == "main" for f in module.functions):
            main_module_name = py_file.stem.replace("-", "_")
            break

    # Generate Rust code for each module
    for module, py_file in zip(modules, py_files):
        resolver = resolve_types(module)
        module_name = py_file.stem.replace("-", "_")

        # Use crate_name for main.rs (binary imports from library)
        crate_name = name if module_name == main_module_name else None
        emitter = RustEmitter(resolver, local_modules=local_module_set, crate_name=crate_name)
        rust_code = emitter.emit_module(module)

        if module_name == "__init__":
            # __init__.py becomes mod.rs
            rs_file = src_dir / "mod.rs"
        else:
            rs_file = src_dir / f"{module_name}.rs"

        rs_file.write_text(rust_code)
        if verbose:
            click.echo(f"  Wrote {rs_file}")

    # Generate lib.rs that exports all modules
    if module_names:
        lib_content = "\n".join(f"pub mod {name};" for name in sorted(module_names))
        lib_rs = src_dir / "lib.rs"
        lib_rs.write_text(lib_content + "\n")
        if verbose:
            click.echo(f"  Wrote {lib_rs}")

    # Generate main.rs
    main_rs = src_dir / "main.rs"
    main_content = generate_main_rs(None)
    main_rs.write_text(main_content)
    if verbose:
        click.echo(f"  Wrote {main_rs}")

    # Generate Cargo.toml
    cargo_toml = output_dir / "Cargo.toml"
    cargo_content = generate_cargo_toml(
        name=name,
        modules=modules,
        is_library=True,
    )
    cargo_toml.write_text(cargo_content)
    if verbose:
        click.echo(f"  Wrote {cargo_toml}")

    # Run rustfmt if requested
    if format_code:
        _run_rustfmt(output_dir, verbose)

    click.echo(click.style(
        f"✓ Transpiled {len(modules)} file(s) to {output_dir}",
        fg="green",
    ))


def _run_rustfmt(output_dir: Path, verbose: bool) -> None:
    """Run rustfmt on generated Rust files."""
    rustfmt = shutil.which("rustfmt")
    if not rustfmt:
        if verbose:
            click.echo("  rustfmt not found, skipping formatting")
        return

    src_dir = output_dir / "src"
    rs_files = list(src_dir.glob("*.rs"))

    for rs_file in rs_files:
        try:
            subprocess.run(
                [rustfmt, str(rs_file)],
                check=True,
                capture_output=True,
            )
            if verbose:
                click.echo(f"  Formatted {rs_file}")
        except subprocess.CalledProcessError as e:
            if verbose:
                click.echo(click.style(
                    f"  Warning: rustfmt failed on {rs_file}: {e.stderr.decode()}",
                    fg="yellow",
                ))


@main.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed AST information.",
)
def parse(input_path: str, verbose: bool) -> None:
    """Parse a Python file and show its IR structure.

    This is useful for debugging and understanding how crabpy
    interprets your Python code.
    """
    path = Path(input_path)

    try:
        ir_module = parse_file(path)
    except CrabpyError as e:
        raise click.ClickException(str(e)) from e

    click.echo(f"Module: {ir_module.name}")

    if ir_module.docstring:
        click.echo(f"Docstring: {ir_module.docstring[:50]}...")

    click.echo(f"\nImports ({len(ir_module.imports)}):")
    for imp in ir_module.imports:
        if imp.names:
            names = ", ".join(n[0] for n in imp.names)
            click.echo(f"  from {imp.module} import {names}")
        else:
            click.echo(f"  import {imp.module}")

    click.echo(f"\nFunctions ({len(ir_module.functions)}):")
    for func in ir_module.functions:
        params = ", ".join(f"{p.name}: {_format_type(p.type)}" for p in func.params)
        ret = f" -> {_format_type(func.return_type)}" if func.return_type else ""
        click.echo(f"  def {func.name}({params}){ret}")
        if verbose and func.body:
            click.echo(f"      {len(func.body)} statement(s)")

    click.echo(f"\nClasses ({len(ir_module.classes)}):")
    for cls in ir_module.classes:
        decorators = "@dataclass " if cls.is_dataclass else ""
        bases = f"({', '.join(cls.bases)})" if cls.bases else ""
        click.echo(f"  {decorators}class {cls.name}{bases}")
        if verbose:
            click.echo(f"      Fields: {len(cls.fields)}")
            click.echo(f"      Methods: {len(cls.methods)}")
            if cls.has_enter and cls.has_exit:
                click.echo(f"      Context manager: yes")


def _format_type(ir_type: object) -> str:
    """Format an IR type for display."""
    if ir_type is None:
        return "?"

    from spicycrab.ir.nodes import (
        IRClassType,
        IRFunctionType,
        IRGenericType,
        IRPrimitiveType,
        IRUnionType,
    )

    if isinstance(ir_type, IRPrimitiveType):
        return ir_type.kind.name.lower()

    if isinstance(ir_type, IRGenericType):
        if ir_type.type_args:
            args = ", ".join(_format_type(a) for a in ir_type.type_args)
            return f"{ir_type.name}[{args}]"
        return ir_type.name

    if isinstance(ir_type, IRUnionType):
        variants = " | ".join(_format_type(v) for v in ir_type.variants)
        return variants

    if isinstance(ir_type, IRClassType):
        if ir_type.module:
            return f"{ir_type.module}.{ir_type.name}"
        return ir_type.name

    if isinstance(ir_type, IRFunctionType):
        params = ", ".join(_format_type(p) for p in ir_type.param_types)
        ret = _format_type(ir_type.return_type)
        return f"Callable[[{params}], {ret}]"

    return str(ir_type)


if __name__ == "__main__":
    main()
