"""Regression tests for cookcrab stub generation edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from spicycrab.analyzer.type_resolver import resolve_types
from spicycrab.codegen.cargo import generate_cargo_toml
from spicycrab.codegen.emitter import RustEmitter
from spicycrab.codegen.stdlib.types import StdlibMapping
from spicycrab.codegen.stub_discovery import StubPackage
from spicycrab.cookcrab.generator import STD_METHOD_STUBS, generate_reexport_toml
from spicycrab.parser import parse_source


def test_reexport_toml_rewrites_type_mappings(tmp_path: Path) -> None:
    """Re-export stubs should not leak source-crate Rust type paths."""
    source_pkg = tmp_path / "clap_builder" / "spicycrab_clap_builder"
    source_pkg.mkdir(parents=True)
    (source_pkg / "_spicycrab.toml").write_text(
        """
[package]
name = "clap_builder"
rust_crate = "clap_builder"
rust_version = "4.6.0"
python_module = "spicycrab_clap_builder"

[[mappings.functions]]
python = "clap_builder.Command.new"
rust_code = "clap_builder::Command::new({arg0})"
rust_imports = ["clap_builder::Command"]
needs_result = false

[[mappings.types]]
python = "Command"
rust = "clap_builder::Command"
""",
        encoding="utf-8",
    )

    toml = generate_reexport_toml("clap", ["clap_builder"], "4.6.1", "spicycrab_clap", tmp_path)

    assert 'python = "clap.Command.new"' in toml
    assert 'rust_code = "clap::Command::new({arg0})"' in toml
    assert 'rust_imports = ["clap::Command"]' in toml
    assert 'rust = "clap::Command"' in toml
    assert "clap_builder::Command" not in toml


def test_reqwest_request_builder_send_is_zero_arg_override() -> None:
    """reqwest RequestBuilder.send must stay a zero-argument method mapping."""
    rust_code, returns_self, needs_result, returns_type, param_types = STD_METHOD_STUBS[
        ("reqwest", "RequestBuilder", "send")
    ]

    assert rust_code == "{self}.send()"
    assert returns_self is False
    assert needs_result is True
    assert returns_type == "Response"
    assert param_types == []


def test_actix_route_passthrough_attribute_adds_cargo_dependency() -> None:
    """Using #[get(...)] without actix stubs still needs actix-web in Cargo.toml."""
    module = parse_source(
        """
# #[get("/")]
async def index() -> str:
    return "ok"
"""
    )

    cargo_toml = generate_cargo_toml("route_attr", modules=[module])

    assert 'actix-web = "4"' in cargo_toml
    assert 'tokio = { version = "1", features = ["full"] }' in cargo_toml


def test_chained_stub_method_lookup_uses_receiver_crate(monkeypatch: pytest.MonkeyPatch) -> None:
    """reqwest chains should not pick ureq's RequestBuilder.send mapping."""
    from spicycrab.codegen import stub_discovery

    ureq_pkg = StubPackage(
        name="ureq",
        rust_crate="ureq",
        rust_version="3.3.0",
        python_module="spicycrab_ureq",
        method_mappings={
            "RequestBuilder.send": StdlibMapping(
                python_module="spicycrab_ureq",
                python_func="RequestBuilder.send",
                rust_code="{self}.send({arg0})",
                rust_imports=[],
                needs_result=True,
                param_types=["impl AsSendBody"],
                returns="Response",
            )
        },
        type_mappings={"RequestBuilder": "ureq::RequestBuilder"},
    )
    reqwest_pkg = StubPackage(
        name="reqwest",
        rust_crate="reqwest",
        rust_version="0.13.4",
        python_module="spicycrab_reqwest",
        function_mappings={
            "reqwest.Client.new": StdlibMapping(
                python_module="spicycrab_reqwest",
                python_func="Client.new",
                rust_code="reqwest::Client::new()",
                rust_imports=[],
            )
        },
        method_mappings={
            "Client.get": StdlibMapping(
                python_module="spicycrab_reqwest",
                python_func="Client.get",
                rust_code="{self}.get({arg0})",
                rust_imports=[],
                param_types=["&str"],
                returns="RequestBuilder",
            ),
            "RequestBuilder.send": StdlibMapping(
                python_module="spicycrab_reqwest",
                python_func="RequestBuilder.send",
                rust_code="{self}.send()",
                rust_imports=[],
                needs_result=True,
                returns="Response",
            ),
        },
        type_mappings={
            "Client": "reqwest::Client",
            "Response": "reqwest::Response",
        },
    )
    monkeypatch.setattr(
        stub_discovery,
        "_stub_cache",
        {
            "ureq": ureq_pkg,
            "reqwest": reqwest_pkg,
        },
    )

    module = parse_source(
        """
from spicycrab_reqwest import Client, Response

async def fetch(url: str) -> str:
    client: Client = Client.new()
    response: Response = await client.get(url).send()
    text: str = await response.text()
    return text
"""
    )

    rust_code = RustEmitter(resolve_types(module)).emit_module(module)

    assert ".get(&url).send().await.unwrap()" in rust_code
    assert ".send({arg0})" not in rust_code
