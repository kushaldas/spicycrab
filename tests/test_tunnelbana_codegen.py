"""Regression tests for tunnelbana-oriented code generation."""

from __future__ import annotations

import pytest

from spicycrab.analyzer.type_resolver import resolve_types
from spicycrab.codegen.cargo import generate_cargo_toml
from spicycrab.codegen.emitter import RustEmitter
from spicycrab.codegen.stdlib.types import StdlibMapping
from spicycrab.codegen.stub_discovery import StubPackage
from spicycrab.parser import parse_source


@pytest.fixture
def tunnelbana_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install a minimal in-memory tunnelbana stub package."""
    from spicycrab.codegen import stub_discovery

    pkg = StubPackage(
        name="tunnelbana-core",
        rust_crate="tunnelbana_core",
        rust_version="0.1.0",
        python_module="spicycrab_tunnelbana_core",
        function_mappings={
            "tunnelbana-core.Result.Ok": StdlibMapping(
                python_module="spicycrab_tunnelbana_core",
                python_func="Ok",
                rust_code="Ok({arg0})",
                rust_imports=[],
            ),
            "tunnelbana-core.Result.Err": StdlibMapping(
                python_module="spicycrab_tunnelbana_core",
                python_func="Err",
                rust_code="Err({arg0})",
                rust_imports=[],
            ),
            "tunnelbana-core.Error.Authn": StdlibMapping(
                python_module="spicycrab_tunnelbana_core",
                python_func="Authn",
                rust_code="tunnelbana_core::Error::Authn({arg0})",
                rust_imports=[],
            ),
        },
        method_mappings={
            "InternalData.attr_first": StdlibMapping(
                python_module="spicycrab_tunnelbana_core",
                python_func="InternalData.attr_first",
                rust_code="{self}.attr_first({arg0}).map(|s| s.to_string())",
                rust_imports=[],
                param_types=["&str"],
                returns="Option<String>",
            ),
            "InternalData.set_attr": StdlibMapping(
                python_module="spicycrab_tunnelbana_core",
                python_func="InternalData.set_attr",
                rust_code="{self}.set_attr({arg0}, {arg1})",
                rust_imports=[],
                param_types=["impl Into<String>", "impl Into<String>"],
            ),
            "State.set_str": StdlibMapping(
                python_module="spicycrab_tunnelbana_core",
                python_func="State.set_str",
                rust_code="{self}.set_str({arg0}, {arg1}, {arg2})",
                rust_imports=[],
                param_types=["&str", "&str", "impl Into<String>"],
            ),
        },
        type_mappings={
            "Context": "tunnelbana_core::Context",
            "InternalData": "tunnelbana_core::InternalData",
            "MicroService": "tunnelbana_core::MicroService",
            "Result": "Result",
            "Error": "tunnelbana_core::Error",
            "State": "tunnelbana_core::State",
        },
    )
    monkeypatch.setattr(stub_discovery, "_stub_cache", {"tunnelbana-core": pkg})


def test_microservice_trait_impl_and_option_guard(tunnelbana_stub: None) -> None:
    """Tunnelbana MicroService subclasses emit trait impls and compile-shaped option use."""
    source = """
from spicycrab_tunnelbana_core import Context, Error, InternalData, MicroService, Result

class PairwiseId(MicroService):
    name: str
    pairwise_salt: str

    def __init__(self, name: str, pairwise_salt: str) -> None:
        self.name = name
        self.pairwise_salt = pairwise_salt

    async def process_request(self, ctx: Context, data: InternalData) -> Result[InternalData, Error]:
        ctx.state.set_str(self.name, "subject_type", "persistent")
        return Result.Ok(data)

    async def process_response(self, ctx: Context, data: InternalData) -> Result[InternalData, Error]:
        subject_id = data.attr_first("subject-id")
        if subject_id is None:
            return Result.Err(Error.Authn("No subject-id attribute found"))
        data.set_attr("pairwise-id", subject_id)
        return Result.Ok(data)
"""
    module = parse_source(source)
    resolver = resolve_types(module)
    rust_code = RustEmitter(resolver).emit_module(module)

    assert "#[async_trait::async_trait]" in rust_code
    assert "impl tunnelbana_core::MicroService for PairwiseId" in rust_code
    assert (
        "async fn process_response("
        "&self, ctx: &mut tunnelbana_core::Context, mut data: tunnelbana_core::InternalData"
        ") -> tunnelbana_core::Result<tunnelbana_core::InternalData>"
    ) in rust_code
    assert 'ctx.state.set_str(&self.name, "subject_type", "persistent".to_string());' in rust_code
    assert 'data.attr_first("subject-id").map(|s| s.to_string())' in rust_code
    assert 'data.set_attr("pairwise-id".to_string(), subject_id.unwrap());' in rust_code
    assert 'return Err(tunnelbana_core::Error::Authn("No subject-id attribute found".to_string()));' in rust_code
    assert "Ok(data)" in rust_code


def test_internal_data_option_field_read_clones(tunnelbana_stub: None) -> None:
    """Reading owned optional InternalData fields should not partially move data."""
    source = """
from spicycrab_tunnelbana_core import Context, Error, InternalData, MicroService, Result

class Metrics(MicroService):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    async def process_response(self, ctx: Context, data: InternalData) -> Result[InternalData, Error]:
        requester = data.requester
        if requester is None:
            return Result.Ok(data)
        return Result.Ok(data)
"""
    module = parse_source(source)
    resolver = resolve_types(module)
    rust_code = RustEmitter(resolver).emit_module(module)

    assert "let requester = data.requester.clone();" in rust_code
    assert "Ok(data)" in rust_code


def test_microservice_self_field_set_attr_clones_owned_string(tunnelbana_stub: None) -> None:
    """Owned self string fields passed to set_attr should be cloned, not moved."""
    source = """
from spicycrab_tunnelbana_core import Context, Error, InternalData, MicroService, Result

class GeneratedMarker(MicroService):
    name: str
    marker_value: str

    def __init__(self, name: str, marker_value: str) -> None:
        self.name = name
        self.marker_value = marker_value

    async def process_response(self, ctx: Context, data: InternalData) -> Result[InternalData, Error]:
        data.set_attr("generated-marker", self.marker_value)
        return Result.Ok(data)
"""
    module = parse_source(source)
    resolver = resolve_types(module)
    rust_code = RustEmitter(resolver).emit_module(module)

    assert 'data.set_attr("generated-marker".to_string(), self.marker_value.clone());' in rust_code


def test_option_param_transform_preserves_none_and_wraps_values() -> None:
    """Stub mappings with Option<T> parameters should emit Rust-shaped options."""
    emitter = RustEmitter()

    assert emitter._transform_arg_for_type("None", "Option<&str>") == "None"
    assert emitter._transform_arg_for_type('"S256".to_string()', "Option<&str>") == 'Some("S256")'
    assert emitter._transform_arg_for_type("method", "Option<&str>") == "Some(&method)"


def test_cargo_toml_limits_stub_deps_to_imported_crates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Installed stubs should not add Cargo deps unless their Python module is imported."""
    from spicycrab.codegen import stub_discovery

    grindvakt_pkg = StubPackage(
        name="grindvakt",
        rust_crate="grindvakt",
        rust_version="0.6.1",
        python_module="spicycrab_grindvakt",
        cargo_deps={"grindvakt": {"path": "/tmp/grindvakt"}},
    )
    tunnelbana_pkg = StubPackage(
        name="tunnelbana-plugins",
        rust_crate="tunnelbana_plugins",
        rust_version="0.1.0",
        python_module="spicycrab_tunnelbana_plugins",
        cargo_deps={
            "tunnelbana-core": {"path": "/tmp/tunnelbana-core"},
            "tunnelbana-plugins": {"path": "/tmp/tunnelbana-plugins"},
        },
    )
    monkeypatch.setattr(
        stub_discovery,
        "_stub_cache",
        {
            "grindvakt": grindvakt_pkg,
            "tunnelbana-plugins": tunnelbana_pkg,
        },
    )

    module = parse_source(
        """
from spicycrab_grindvakt import s256_challenge

def main() -> None:
    pass
"""
    )
    cargo_toml = generate_cargo_toml("stub_deps", modules=[module])

    assert 'grindvakt = { path = "/tmp/grindvakt" }' in cargo_toml
    assert "tunnelbana-core" not in cargo_toml
    assert "tunnelbana-plugins" not in cargo_toml


def test_cargo_toml_includes_stub_transitive_deps(monkeypatch: pytest.MonkeyPatch) -> None:
    """Imported stubs can still provide multiple Cargo dependencies."""
    from spicycrab.codegen import stub_discovery

    tunnelbana_pkg = StubPackage(
        name="tunnelbana-plugins",
        rust_crate="tunnelbana_plugins",
        rust_version="0.1.0",
        python_module="spicycrab_tunnelbana_plugins",
        cargo_deps={
            "tunnelbana-core": {"path": "/tmp/tunnelbana-core"},
            "tunnelbana-plugins": {"path": "/tmp/tunnelbana-plugins"},
        },
    )
    monkeypatch.setattr(stub_discovery, "_stub_cache", {"tunnelbana-plugins": tunnelbana_pkg})

    module = parse_source(
        """
from spicycrab_tunnelbana_plugins import OidcFrontend

def main() -> None:
    pass
"""
    )
    cargo_toml = generate_cargo_toml("stub_deps", modules=[module])

    assert 'tunnelbana-core = { path = "/tmp/tunnelbana-core" }' in cargo_toml
    assert 'tunnelbana-plugins = { path = "/tmp/tunnelbana-plugins" }' in cargo_toml


def test_tunnelbana_plugin_build_direct_return(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plugin build mappings should return crate Result aliases directly."""
    from spicycrab.codegen import stub_discovery

    core_pkg = StubPackage(
        name="tunnelbana-core",
        rust_crate="tunnelbana_core",
        rust_version="0.1.0",
        python_module="spicycrab_tunnelbana_core",
        type_mappings={
            "BuildContext": "tunnelbana_core::BuildContext",
            "Error": "tunnelbana_core::Error",
            "Frontend": "Box<dyn tunnelbana_core::Frontend>",
            "MicroService": "tunnelbana_core::MicroService",
            "Result": "tunnelbana_core::Result",
        },
    )
    plugins_pkg = StubPackage(
        name="tunnelbana-plugins",
        rust_crate="tunnelbana_plugins",
        rust_version="0.1.0",
        python_module="spicycrab_tunnelbana_plugins",
        function_mappings={
            "tunnelbana-plugins.OidcFrontend.build": StdlibMapping(
                python_module="spicycrab_tunnelbana_plugins",
                python_func="build",
                rust_code="tunnelbana_plugins::oidc_frontend::OidcFrontend::build({arg0})",
                rust_imports=[],
                needs_result=True,
                param_types=["&tunnelbana_core::BuildContext"],
            ),
            "tunnelbana-plugins.PairwiseId.build": StdlibMapping(
                python_module="spicycrab_tunnelbana_plugins",
                python_func="build",
                rust_code="tunnelbana_plugins::microservices::PairwiseId::build({arg0})",
                rust_imports=[],
                needs_result=True,
                param_types=["&tunnelbana_core::BuildContext"],
            ),
        },
    )
    monkeypatch.setattr(
        stub_discovery,
        "_stub_cache",
        {
            "tunnelbana-core": core_pkg,
            "tunnelbana-plugins": plugins_pkg,
        },
    )

    module = parse_source(
        """
from spicycrab_tunnelbana_core import BuildContext, Error, Frontend, MicroService, Result
from spicycrab_tunnelbana_plugins import OidcFrontend, PairwiseId

def build_oidc(bx: BuildContext) -> Result[Frontend, Error]:
    return OidcFrontend.build(bx)

def build_pairwise(bx: BuildContext) -> Result[MicroService, Error]:
    return PairwiseId.build(bx)
"""
    )
    rust_code = RustEmitter(resolve_types(module)).emit_module(module)

    assert "-> tunnelbana_core::Result<Box<dyn tunnelbana_core::Frontend>>" in rust_code
    assert "-> tunnelbana_core::Result<Box<dyn tunnelbana_core::MicroService>>" in rust_code
    assert "tunnelbana_plugins::oidc_frontend::OidcFrontend::build(&bx)" in rust_code
    assert "tunnelbana_plugins::microservices::PairwiseId::build(&bx)" in rust_code
    assert "build(&bx)?" not in rust_code
