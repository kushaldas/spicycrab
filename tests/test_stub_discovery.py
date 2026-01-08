"""Tests for stub package discovery and loading."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from spicycrab.codegen.stub_discovery import (
    StubPackage,
    _parse_config,
    clear_stub_cache,
    get_all_stub_packages,
    get_stub_cargo_deps,
    get_stub_mapping,
    get_stub_method_mapping,
    get_stub_type_mapping,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the stub cache before and after each test."""
    clear_stub_cache()
    yield
    clear_stub_cache()


class TestParseConfig:
    """Tests for _parse_config function."""

    def test_parse_basic_config(self):
        """Test parsing a basic _spicycrab.toml config."""
        config = {
            "package": {
                "name": "test_crate",
                "rust_crate": "test_crate",
                "rust_version": "1.0",
                "python_module": "spicycrab_test",
            },
            "cargo": {"dependencies": {"test_crate": "1.0"}},
            "mappings": {
                "functions": [
                    {
                        "python": "test.func",
                        "rust_code": "test_crate::func({arg0})",
                        "rust_imports": ["test_crate"],
                        "needs_result": False,
                    }
                ],
                "methods": [
                    {
                        "python": "TestType.method",
                        "rust_code": "{self}.method()",
                        "rust_imports": [],
                        "needs_result": False,
                    }
                ],
                "types": [{"python": "TestType", "rust": "test_crate::TestType"}],
            },
        }

        pkg = _parse_config(config)

        assert pkg.name == "test_crate"
        assert pkg.rust_crate == "test_crate"
        assert pkg.rust_version == "1.0"
        assert pkg.python_module == "spicycrab_test"
        assert "test_crate" in pkg.cargo_deps
        assert "test.func" in pkg.function_mappings
        assert "TestType.method" in pkg.method_mappings
        assert "TestType" in pkg.type_mappings

    def test_parse_config_with_features(self):
        """Test parsing config with cargo features."""
        config = {
            "package": {
                "name": "clap",
                "rust_crate": "clap",
                "rust_version": "4.5",
                "python_module": "spicycrab_clap",
            },
            "cargo": {
                "dependencies": {"clap": {"version": "4.5", "features": ["derive"]}}
            },
            "mappings": {},
        }

        pkg = _parse_config(config)

        assert pkg.cargo_deps["clap"]["version"] == "4.5"
        assert "derive" in pkg.cargo_deps["clap"]["features"]

    def test_parse_config_minimal(self):
        """Test parsing minimal config without mappings."""
        config = {
            "package": {
                "name": "minimal",
                "rust_crate": "minimal",
                "rust_version": "0.1",
                "python_module": "spicycrab_minimal",
            }
        }

        pkg = _parse_config(config)

        assert pkg.name == "minimal"
        assert len(pkg.function_mappings) == 0
        assert len(pkg.method_mappings) == 0
        assert len(pkg.type_mappings) == 0
        assert len(pkg.cargo_deps) == 0


class TestStubPackage:
    """Tests for StubPackage dataclass."""

    def test_stub_package_creation(self):
        """Test creating a StubPackage instance."""
        pkg = StubPackage(
            name="test",
            rust_crate="test",
            rust_version="1.0",
            python_module="spicycrab_test",
        )

        assert pkg.name == "test"
        assert pkg.cargo_deps == {}
        assert pkg.function_mappings == {}
        assert pkg.method_mappings == {}
        assert pkg.type_mappings == {}


class TestGeneratedClapStubPackage:
    """Tests using cookcrab-generated clap stub package."""

    @pytest.fixture(scope="class")
    def generated_stubs_dir(self):
        """Generate clap stubs using cookcrab and return the output directory."""
        # Create temp directory for stubs
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Import cookcrab components
            from spicycrab.cookcrab._parser import parse_crate
            from spicycrab.cookcrab.cli import download_crate, fetch_crate_info
            from spicycrab.cookcrab.generator import (
                generate_stub_package,
                generate_reexport_stub_package,
            )

            # Fetch clap crate info
            crate_info = fetch_crate_info("clap")
            crate_version = crate_info.get("max_version", "4.5.0")

            # Download clap
            download_dir = Path(tempfile.mkdtemp())
            crate_path = download_crate("clap", crate_version, download_dir)

            # Parse clap crate
            parsed_crate = parse_crate(str(crate_path.absolute()))

            # Check for re-exports (clap re-exports from clap_builder)
            glob_reexports = [r for r in parsed_crate.reexports if r.is_glob]
            source_crates = [r.source_crate for r in glob_reexports]

            # Generate stubs for source crates first (clap_builder)
            for source_crate in source_crates:
                source_info = fetch_crate_info(source_crate)
                source_version = source_info.get("max_version", "0.1.0")

                source_temp_dir = Path(tempfile.mkdtemp())
                source_path = download_crate(source_crate, source_version, source_temp_dir)
                source_parsed = parse_crate(str(source_path.absolute()))

                generate_stub_package(
                    crate=source_parsed,
                    crate_name=source_crate,
                    version=source_version,
                    output_dir=temp_dir,
                )

                shutil.rmtree(source_temp_dir, ignore_errors=True)

            # Generate re-export stub for clap
            if source_crates:
                generate_reexport_stub_package(
                    crate_name="clap",
                    source_crates=source_crates,
                    version=crate_version,
                    output_dir=temp_dir,
                )
            else:
                generate_stub_package(
                    crate=parsed_crate,
                    crate_name="clap",
                    version=crate_version,
                    output_dir=temp_dir,
                )

            # Cleanup download dir
            shutil.rmtree(download_dir, ignore_errors=True)

            yield temp_dir

        finally:
            # Cleanup temp dir
            shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def clap_toml_path(self, generated_stubs_dir):
        """Get path to generated clap stub's _spicycrab.toml."""
        return generated_stubs_dir / "clap" / "spicycrab_clap" / "_spicycrab.toml"

    @pytest.fixture
    def clap_builder_toml_path(self, generated_stubs_dir):
        """Get path to generated clap_builder stub's _spicycrab.toml."""
        return generated_stubs_dir / "clap_builder" / "spicycrab_clap_builder" / "_spicycrab.toml"

    def test_clap_toml_exists(self, clap_toml_path):
        """Test that the generated clap stub package TOML exists."""
        assert clap_toml_path.exists(), f"Expected {clap_toml_path} to exist"

    def test_clap_builder_toml_exists(self, clap_builder_toml_path):
        """Test that the generated clap_builder stub package TOML exists."""
        assert clap_builder_toml_path.exists(), f"Expected {clap_builder_toml_path} to exist"

    def test_clap_toml_parses(self, clap_toml_path):
        """Test that the generated clap stub package TOML parses correctly."""
        import tomllib
        content = clap_toml_path.read_text()
        config = tomllib.loads(content)

        pkg = _parse_config(config)

        assert pkg.name == "clap"
        assert pkg.rust_crate == "clap"
        assert pkg.python_module == "spicycrab_clap"

    def test_clap_builder_has_command_mapping(self, clap_builder_toml_path):
        """Test clap_builder has Command.new function mapping."""
        import tomllib
        content = clap_builder_toml_path.read_text()
        config = tomllib.loads(content)
        pkg = _parse_config(config)

        # Check Command.new mapping exists
        assert "clap_builder.Command.new" in pkg.function_mappings
        cmd_new = pkg.function_mappings["clap_builder.Command.new"]
        # Generated stubs use crate name (clap_builder) in Rust code
        assert "clap_builder::Command::new" in cmd_new.rust_code

    def test_clap_builder_has_arg_mapping(self, clap_builder_toml_path):
        """Test clap_builder has Arg.new function mapping."""
        import tomllib
        content = clap_builder_toml_path.read_text()
        config = tomllib.loads(content)
        pkg = _parse_config(config)

        # Check Arg.new mapping exists
        assert "clap_builder.Arg.new" in pkg.function_mappings
        arg_new = pkg.function_mappings["clap_builder.Arg.new"]
        # Generated stubs use crate name (clap_builder) in Rust code
        assert "clap_builder::Arg::new" in arg_new.rust_code

    def test_clap_builder_has_method_mappings(self, clap_builder_toml_path):
        """Test clap_builder has method mappings for Command and Arg."""
        import tomllib
        content = clap_builder_toml_path.read_text()
        config = tomllib.loads(content)
        pkg = _parse_config(config)

        # Check Command.arg method mapping
        assert "Command.arg" in pkg.method_mappings
        cmd_arg = pkg.method_mappings["Command.arg"]
        assert "{self}.arg" in cmd_arg.rust_code

        # Check Command.about method mapping
        assert "Command.about" in pkg.method_mappings

    def test_clap_builder_has_type_mappings(self, clap_builder_toml_path):
        """Test clap_builder has type mappings."""
        import tomllib
        content = clap_builder_toml_path.read_text()
        config = tomllib.loads(content)
        pkg = _parse_config(config)

        assert "Command" in pkg.type_mappings
        assert "Arg" in pkg.type_mappings
        assert "ArgMatches" in pkg.type_mappings

    def test_clap_builder_has_cargo_deps(self, clap_builder_toml_path):
        """Test clap_builder cargo dependencies are set correctly."""
        import tomllib
        content = clap_builder_toml_path.read_text()
        config = tomllib.loads(content)
        pkg = _parse_config(config)

        # Generated stubs use the actual crate name (clap_builder) in cargo deps
        assert "clap_builder" in pkg.cargo_deps
        clap_dep = pkg.cargo_deps["clap_builder"]
        # Should have version set (can be string or dict with version key)
        assert isinstance(clap_dep, str) or "version" in clap_dep


class TestGetterFunctions:
    """Tests for the getter functions that access stub cache."""

    def test_get_stub_mapping_not_found(self):
        """Test get_stub_mapping returns None for unknown functions."""
        # With no packages installed, should return None
        result = get_stub_mapping("nonexistent.module.func")
        assert result is None

    def test_get_stub_method_mapping_not_found(self):
        """Test get_stub_method_mapping returns None for unknown methods."""
        result = get_stub_method_mapping("NonexistentType", "method")
        assert result is None

    def test_get_stub_type_mapping_not_found(self):
        """Test get_stub_type_mapping returns None for unknown types."""
        result = get_stub_type_mapping("NonexistentType")
        assert result is None

    def test_get_stub_cargo_deps_empty(self):
        """Test get_stub_cargo_deps returns empty dict when no packages."""
        deps = get_stub_cargo_deps()
        # May be empty or contain deps from installed packages
        assert isinstance(deps, dict)

    def test_get_all_stub_packages(self):
        """Test get_all_stub_packages returns a dict."""
        packages = get_all_stub_packages()
        assert isinstance(packages, dict)


class TestClearCache:
    """Tests for cache clearing."""

    def test_clear_stub_cache(self):
        """Test that clearing cache works."""
        # Access cache to initialize it
        get_all_stub_packages()

        # Clear it
        clear_stub_cache()

        # Should work without error
        packages = get_all_stub_packages()
        assert isinstance(packages, dict)
