"""Tests for stub package discovery and loading."""

from __future__ import annotations

import tempfile
import tomllib
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


class TestClapStubPackage:
    """Tests using the manually created clap stub package."""

    @pytest.fixture
    def clap_toml_path(self):
        """Get path to clap stub's _spicycrab.toml."""
        return (
            Path(__file__).parent.parent
            / "stubs"
            / "spicycrab-clap"
            / "spicycrab_clap"
            / "_spicycrab.toml"
        )

    def test_clap_toml_exists(self, clap_toml_path):
        """Test that the clap stub package TOML exists."""
        assert clap_toml_path.exists(), f"Expected {clap_toml_path} to exist"

    def test_clap_toml_parses(self, clap_toml_path):
        """Test that the clap stub package TOML parses correctly."""
        content = clap_toml_path.read_text()
        config = tomllib.loads(content)

        pkg = _parse_config(config)

        assert pkg.name == "clap"
        assert pkg.rust_crate == "clap"
        assert pkg.rust_version == "4.5"
        assert pkg.python_module == "spicycrab_clap"

    def test_clap_function_mappings(self, clap_toml_path):
        """Test clap function mappings are parsed correctly."""
        content = clap_toml_path.read_text()
        config = tomllib.loads(content)
        pkg = _parse_config(config)

        # Check Command.new mapping
        assert "clap.Command.new" in pkg.function_mappings
        cmd_new = pkg.function_mappings["clap.Command.new"]
        assert "clap::Command::new" in cmd_new.rust_code
        assert "clap::Command" in cmd_new.rust_imports

        # Check Arg.new mapping
        assert "clap.Arg.new" in pkg.function_mappings
        arg_new = pkg.function_mappings["clap.Arg.new"]
        assert "clap::Arg::new" in arg_new.rust_code

    def test_clap_method_mappings(self, clap_toml_path):
        """Test clap method mappings are parsed correctly."""
        content = clap_toml_path.read_text()
        config = tomllib.loads(content)
        pkg = _parse_config(config)

        # Check Command.arg method
        assert "Command.arg" in pkg.method_mappings
        cmd_arg = pkg.method_mappings["Command.arg"]
        assert "{self}.arg" in cmd_arg.rust_code

        # Check ArgMatches.get_one method
        assert "ArgMatches.get_one" in pkg.method_mappings
        get_one = pkg.method_mappings["ArgMatches.get_one"]
        assert "get_one::<String>" in get_one.rust_code

    def test_clap_type_mappings(self, clap_toml_path):
        """Test clap type mappings are parsed correctly."""
        content = clap_toml_path.read_text()
        config = tomllib.loads(content)
        pkg = _parse_config(config)

        assert pkg.type_mappings["Command"] == "clap::Command"
        assert pkg.type_mappings["Arg"] == "clap::Arg"
        assert pkg.type_mappings["ArgMatches"] == "clap::ArgMatches"

    def test_clap_cargo_deps(self, clap_toml_path):
        """Test clap cargo dependencies are parsed correctly."""
        content = clap_toml_path.read_text()
        config = tomllib.loads(content)
        pkg = _parse_config(config)

        assert "clap" in pkg.cargo_deps
        clap_dep = pkg.cargo_deps["clap"]
        assert clap_dep["version"] == "4.5"
        assert "derive" in clap_dep["features"]


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
