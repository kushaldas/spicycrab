"""Tests for multi-file module transpilation and import resolution."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from spicycrab.analyzer.type_resolver import resolve_types
from spicycrab.codegen.cargo import generate_cargo_toml
from spicycrab.codegen.emitter import RustEmitter
from spicycrab.parser import parse_file


@pytest.fixture(scope="module")
def check_cargo():
    """Check if cargo is available."""
    if shutil.which("cargo") is None:
        pytest.skip("cargo not found, skipping multi-file tests")


class TestImportResolution:
    """Test import resolution between modules."""

    def test_local_module_import_resolution(self):
        """Test that local imports are properly resolved to use crate::."""
        # Create a module with a class
        models_code = '''
class User:
    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self) -> str:
        return self.name
'''
        # Create a module that imports from models
        main_code = '''
from models import User

def main() -> None:
    u: User = User("Alice")
    print(u.greet())
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write Python files
            models_py = tmpdir / "models.py"
            models_py.write_text(models_code)

            main_py = tmpdir / "main.py"
            main_py.write_text(main_code)

            # Parse both modules
            parse_file(models_py)
            main_ir = parse_file(main_py)

            # Set up local modules
            local_modules = {"models", "main"}

            # Generate Rust code for main module
            resolver = resolve_types(main_ir)
            emitter = RustEmitter(resolver, local_modules=local_modules)
            rust_code = emitter.emit_module(main_ir)

            # Verify the import was resolved correctly
            assert "use crate::models::User;" in rust_code

    def test_aliased_import_resolution(self):
        """Test import with alias (from x import Y as Z)."""
        utils_code = '''
class Helper:
    def __init__(self) -> None:
        pass

    def run(self) -> int:
        return 42
'''
        main_code = '''
from utils import Helper as H

def main() -> None:
    h: H = H()
    print(h.run())
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            utils_py = tmpdir / "utils.py"
            utils_py.write_text(utils_code)

            main_py = tmpdir / "main.py"
            main_py.write_text(main_code)

            main_ir = parse_file(main_py)

            local_modules = {"utils", "main"}

            resolver = resolve_types(main_ir)
            emitter = RustEmitter(resolver, local_modules=local_modules)
            rust_code = emitter.emit_module(main_ir)

            assert "use crate::utils::Helper as H;" in rust_code


class TestMultiFileTranspilation:
    """Test full multi-file transpilation and compilation."""

    def test_two_file_project(self, check_cargo):
        """Test transpiling a project with two files."""
        # Math utilities module
        math_utils_code = '''
def add(a: int, b: int) -> int:
    return a + b

def multiply(a: int, b: int) -> int:
    return a * b
'''
        # Main module that uses math_utils
        main_code = '''
from math_utils import add, multiply

def main() -> None:
    sum_result: int = add(5, 3)
    prod_result: int = multiply(4, 7)
    print(sum_result)
    print(prod_result)
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write Python files
            math_py = tmpdir / "math_utils.py"
            math_py.write_text(math_utils_code)

            main_py = tmpdir / "main.py"
            main_py.write_text(main_code)

            # Parse both
            math_ir = parse_file(math_py)
            main_ir = parse_file(main_py)

            local_modules = {"math_utils", "main"}

            # Create output directory
            out_dir = tmpdir / "rust_out"
            src_dir = out_dir / "src"
            src_dir.mkdir(parents=True)

            # Generate math_utils.rs
            resolver = resolve_types(math_ir)
            emitter = RustEmitter(resolver, local_modules=local_modules)
            math_rust = emitter.emit_module(math_ir)
            (src_dir / "math_utils.rs").write_text(math_rust)

            # Generate main.rs - use crate_name for binary to import from library
            resolver = resolve_types(main_ir)
            emitter = RustEmitter(resolver, local_modules=local_modules, crate_name="test_multifile")
            main_rust = emitter.emit_module(main_ir)
            (src_dir / "main.rs").write_text(main_rust)

            # Generate lib.rs with module declarations
            lib_rs = "pub mod math_utils;\n"
            (src_dir / "lib.rs").write_text(lib_rs)

            # Generate Cargo.toml
            cargo_content = generate_cargo_toml(
                name="test_multifile",
                modules=[math_ir, main_ir],
                is_library=True,
            )
            (out_dir / "Cargo.toml").write_text(cargo_content)

            # Build
            result = subprocess.run(
                ["cargo", "build", "--release"],
                cwd=out_dir,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Cargo build failed:\n{result.stderr}"

            # Run
            result = subprocess.run(
                ["cargo", "run", "--release", "-q"],
                cwd=out_dir,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Cargo run failed:\n{result.stderr}"

            # Verify output
            lines = result.stdout.strip().split('\n')
            assert lines[0] == "8", f"Expected add(5,3)=8, got {lines[0]}"
            assert lines[1] == "28", f"Expected multiply(4,7)=28, got {lines[1]}"

    def test_class_import_project(self, check_cargo):
        """Test importing classes from another module."""
        models_code = '''
class Point:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def distance_from_origin(self) -> int:
        return self.x + self.y
'''
        main_code = '''
from models import Point

def main() -> None:
    p: Point = Point(3, 4)
    d: int = p.distance_from_origin()
    print(d)
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Write Python files
            (tmpdir / "models.py").write_text(models_code)
            (tmpdir / "main.py").write_text(main_code)

            # Parse both
            models_ir = parse_file(tmpdir / "models.py")
            main_ir = parse_file(tmpdir / "main.py")

            local_modules = {"models", "main"}

            # Create output directory
            out_dir = tmpdir / "rust_out"
            src_dir = out_dir / "src"
            src_dir.mkdir(parents=True)

            # Generate models.rs
            resolver = resolve_types(models_ir)
            emitter = RustEmitter(resolver, local_modules=local_modules)
            (src_dir / "models.rs").write_text(emitter.emit_module(models_ir))

            # Generate main.rs - use crate_name for binary imports
            resolver = resolve_types(main_ir)
            emitter = RustEmitter(resolver, local_modules=local_modules, crate_name="test_class_import")
            (src_dir / "main.rs").write_text(emitter.emit_module(main_ir))

            # lib.rs
            (src_dir / "lib.rs").write_text("pub mod models;\n")

            # Cargo.toml
            cargo_content = generate_cargo_toml(
                name="test_class_import",
                modules=[models_ir, main_ir],
                is_library=True,
            )
            (out_dir / "Cargo.toml").write_text(cargo_content)

            # Build
            result = subprocess.run(
                ["cargo", "build", "--release"],
                cwd=out_dir,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Cargo build failed:\n{result.stderr}"

            # Run
            result = subprocess.run(
                ["cargo", "run", "--release", "-q"],
                cwd=out_dir,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Cargo run failed:\n{result.stderr}"

            assert result.stdout.strip() == "7"


class TestSubdirectoryModules:
    """Test modules in subdirectories (packages)."""

    def test_nested_module_structure(self):
        """Test parsing modules in a nested directory structure."""
        # This tests that we can handle package structures
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create package structure: mypackage/__init__.py, mypackage/utils.py
            pkg_dir = tmpdir / "mypackage"
            pkg_dir.mkdir()

            init_code = '''
"""Package init."""
'''
            (pkg_dir / "__init__.py").write_text(init_code)

            utils_code = '''
def helper() -> str:
    return "ok"
'''
            (pkg_dir / "utils.py").write_text(utils_code)

            # Parse the utils module
            utils_ir = parse_file(pkg_dir / "utils.py")

            assert utils_ir.name == "utils"
            assert len(utils_ir.functions) == 1
            assert utils_ir.functions[0].name == "helper"
