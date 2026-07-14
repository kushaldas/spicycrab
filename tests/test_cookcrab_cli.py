"""Regression tests for cookcrab's wheel build and installation commands."""

from __future__ import annotations

import sys
from pathlib import Path

from spicycrab.cookcrab import cli


def test_uv_build_does_not_use_project_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "is_uv_available", lambda: True)
    stub_path = tmp_path / "stub"
    wheel_dir = tmp_path / "wheels"

    assert cli.get_build_command(stub_path, wheel_dir) == [
        "uv",
        "build",
        "--wheel",
        "--out-dir",
        str(wheel_dir),
        str(stub_path),
    ]


def test_python_build_uses_cookcrab_interpreter(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "is_uv_available", lambda: False)
    stub_path = tmp_path / "stub"
    wheel_dir = tmp_path / "wheels"

    assert cli.get_build_command(stub_path, wheel_dir) == [
        sys.executable,
        "-m",
        "build",
        "--wheel",
        "--outdir",
        str(wheel_dir),
        str(stub_path),
    ]


def test_uv_install_targets_cookcrab_interpreter(monkeypatch) -> None:
    monkeypatch.setattr(cli, "is_uv_available", lambda: True)

    assert cli.get_pip_command() == ["uv", "pip", "install", "--python", sys.executable]


def test_pip_install_uses_cookcrab_interpreter(monkeypatch) -> None:
    monkeypatch.setattr(cli, "is_uv_available", lambda: False)

    assert cli.get_pip_command() == [sys.executable, "-m", "pip", "install"]
