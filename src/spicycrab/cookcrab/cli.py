"""cookcrab CLI: Generate Python type stubs from Rust crates.

Commands:
    validate - Validate a stub package structure
    build    - Build a wheel from a stub package
    install  - Install a stub package from the spicycrab index
    search   - Search for available stub packages
    generate - Generate stubs from a Rust crate

IMPORTANT: Stub packages should be installed using `cookcrab install`, NOT pip.
This ensures packages come from the official spicycrab index, not PyPI.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

import click

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found]

# Spicycrab stubs repository
SPICYCRAB_STUBS_REPO = "https://github.com/kushaldas/spicycrab-stubs.git"

# crates.io API
CRATES_IO_API = "https://crates.io/api/v1/crates"
CRATES_IO_DOWNLOAD = "https://static.crates.io/crates"


def fetch_crate_info(crate_name: str) -> dict:
    """Fetch crate information from crates.io API.

    Args:
        crate_name: Name of the crate on crates.io

    Returns:
        Dict with crate info including 'max_version'

    Raises:
        click.ClickException: If crate not found or API error
    """
    url = f"{CRATES_IO_API}/{crate_name}"
    headers = {"User-Agent": "cookcrab/0.1.0 (https://github.com/kushaldas/spicycrab)"}

    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["crate"]
    except HTTPError as e:
        if e.code == 404:
            raise click.ClickException(f"Crate '{crate_name}' not found on crates.io")
        raise click.ClickException(f"Failed to fetch crate info: HTTP {e.code}")
    except URLError as e:
        raise click.ClickException(f"Network error fetching crate info: {e.reason}")
    except (json.JSONDecodeError, KeyError) as e:
        raise click.ClickException(f"Invalid response from crates.io: {e}")


def download_crate(crate_name: str, version: str, output_dir: Path) -> Path:
    """Download and extract a crate from crates.io.

    Args:
        crate_name: Name of the crate
        version: Version to download
        output_dir: Directory to extract to

    Returns:
        Path to the extracted crate directory

    Raises:
        click.ClickException: If download or extraction fails
    """
    # Download URL format: https://static.crates.io/crates/{name}/{name}-{version}.crate
    url = f"{CRATES_IO_DOWNLOAD}/{crate_name}/{crate_name}-{version}.crate"
    headers = {"User-Agent": "cookcrab/0.1.0 (https://github.com/kushaldas/spicycrab)"}

    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            crate_data = response.read()
    except HTTPError as e:
        if e.code == 404:
            raise click.ClickException(f"Crate '{crate_name}' version '{version}' not found on crates.io")
        raise click.ClickException(f"Failed to download crate: HTTP {e.code}")
    except URLError as e:
        raise click.ClickException(f"Network error downloading crate: {e.reason}")

    # The .crate file is a gzipped tarball
    try:
        # Write to temp file and extract
        crate_file = output_dir / f"{crate_name}-{version}.crate"
        crate_file.write_bytes(crate_data)

        # Extract the tarball
        with tarfile.open(crate_file, "r:gz") as tar:
            tar.extractall(path=output_dir)

        # Remove the .crate file
        crate_file.unlink()

        # The extracted directory is named {crate_name}-{version}
        extracted_dir = output_dir / f"{crate_name}-{version}"
        if not extracted_dir.exists():
            # Some crates might have different directory structure
            dirs = [d for d in output_dir.iterdir() if d.is_dir()]
            if dirs:
                extracted_dir = dirs[0]
            else:
                raise click.ClickException("Failed to find extracted crate directory")

        return extracted_dir

    except tarfile.TarError as e:
        raise click.ClickException(f"Failed to extract crate: {e}")


def is_uv_available() -> bool:
    """Check if uv is available in the environment."""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_pip_command() -> list[str]:
    """Get the appropriate pip command (uv pip or python -m pip)."""
    if is_uv_available():
        return ["uv", "pip"]
    return [sys.executable, "-m", "pip"]


def get_build_command() -> list[str]:
    """Get the appropriate build command."""
    if is_uv_available():
        return ["uv", "run", "python", "-m", "build"]
    return [sys.executable, "-m", "build"]


@click.group()
@click.version_option()
def main():
    """cookcrab: Generate Python type stubs from Rust crates.

    This tool helps create and manage Python type stub packages
    for Rust crates, enabling transpilation with spicycrab.

    \b
    IMPORTANT: Always use `cookcrab install` to install stub packages.
    Do NOT use pip directly - stubs must come from the spicycrab index.
    """
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
def validate(path: Path):
    """Validate a stub package structure.

    Checks that the package has all required files and that
    the _spicycrab.toml is correctly formatted.

    \b
    Example:
        cookcrab validate ./spicycrab-clap
    """
    errors: list[str] = []
    warnings: list[str] = []

    click.echo(f"Validating stub package at: {path}")

    # Check pyproject.toml exists
    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        errors.append("Missing pyproject.toml")
    else:
        click.echo("  [OK] pyproject.toml found")
        try:
            content = pyproject.read_text()
            config = tomllib.loads(content)
            name = config.get("project", {}).get("name", "")
            if not name.startswith("spicycrab-"):
                warnings.append(f"Package name '{name}' should start with 'spicycrab-'")
        except Exception as e:
            errors.append(f"Invalid pyproject.toml: {e}")

    # Find package directory
    src_dir = path / "src"
    pkg_dirs = []
    if src_dir.exists():
        pkg_dirs = [d for d in src_dir.iterdir() if d.is_dir() and d.name.startswith("spicycrab_")]
    else:
        pkg_dirs = [d for d in path.iterdir() if d.is_dir() and d.name.startswith("spicycrab_")]

    if not pkg_dirs:
        errors.append("No spicycrab_* package directory found")
    else:
        pkg_dir = pkg_dirs[0]
        click.echo(f"  [OK] Package directory found: {pkg_dir.name}")

        # Check __init__.py
        init_py = pkg_dir / "__init__.py"
        if not init_py.exists():
            errors.append(f"Missing {pkg_dir.name}/__init__.py")
        else:
            click.echo("  [OK] __init__.py found")

        # Check _spicycrab.toml
        toml_file = pkg_dir / "_spicycrab.toml"
        if not toml_file.exists():
            errors.append(f"Missing {pkg_dir.name}/_spicycrab.toml")
        else:
            click.echo("  [OK] _spicycrab.toml found")
            try:
                content = toml_file.read_text()
                config = tomllib.loads(content)

                # Validate required fields
                pkg = config.get("package", {})
                required = ["name", "rust_crate", "rust_version", "python_module"]
                for field in required:
                    if field not in pkg:
                        errors.append(f"Missing required field: package.{field}")
                    else:
                        click.echo(f"  [OK] package.{field} = {pkg[field]}")

                # Check mappings structure
                mappings = config.get("mappings", {})
                funcs = mappings.get("functions", [])
                methods = mappings.get("methods", [])
                types = mappings.get("types", [])

                click.echo(f"  [OK] {len(funcs)} function mapping(s)")
                click.echo(f"  [OK] {len(methods)} method mapping(s)")
                click.echo(f"  [OK] {len(types)} type mapping(s)")

                # Validate each mapping has required fields
                for i, func in enumerate(funcs):
                    if "python" not in func:
                        errors.append(f"Function mapping {i} missing 'python' field")
                    if "rust_code" not in func:
                        errors.append(f"Function mapping {i} missing 'rust_code' field")

                for i, method in enumerate(methods):
                    if "python" not in method:
                        errors.append(f"Method mapping {i} missing 'python' field")
                    if "rust_code" not in method:
                        errors.append(f"Method mapping {i} missing 'rust_code' field")

                for i, typ in enumerate(types):
                    if "python" not in typ:
                        errors.append(f"Type mapping {i} missing 'python' field")
                    if "rust" not in typ:
                        errors.append(f"Type mapping {i} missing 'rust' field")

            except Exception as e:
                errors.append(f"Invalid _spicycrab.toml: {e}")

    # Print results
    click.echo("")
    if warnings:
        click.echo("Warnings:")
        for w in warnings:
            click.echo(f"  - {w}")

    if errors:
        click.echo("Errors:")
        for e in errors:
            click.echo(f"  - {e}")
        click.echo("")
        click.echo(click.style("Validation FAILED", fg="red"))
        sys.exit(1)
    else:
        click.echo(click.style("Validation PASSED", fg="green"))


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for the wheel (default: ./dist)",
)
def build(path: Path, output: Path | None):
    """Build a wheel from a stub package.

    Creates a distributable wheel file from a stub package directory.
    The wheel can then be uploaded to the spicycrab index.

    \b
    Example:
        cookcrab build ./spicycrab-clap
        cookcrab build ./spicycrab-clap -o ./wheels
    """
    if output is None:
        output = path / "dist"

    click.echo(f"Building wheel for stub package at: {path}")

    # First validate the package
    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        click.echo(click.style("Error: Missing pyproject.toml", fg="red"), err=True)
        sys.exit(1)

    # Get package name and version from pyproject.toml
    try:
        content = pyproject.read_text()
        config = tomllib.loads(content)
        name = config.get("project", {}).get("name", "unknown")
        version = config.get("project", {}).get("version", "0.0.0")
    except Exception as e:
        click.echo(click.style(f"Error reading pyproject.toml: {e}", fg="red"), err=True)
        sys.exit(1)

    click.echo(f"  Package: {name}")
    click.echo(f"  Version: {version}")
    click.echo(f"  Output: {output}")

    # Build using pip wheel or python -m build
    output.mkdir(parents=True, exist_ok=True)

    # Use appropriate build command
    cmd = get_build_command() + [
        "--wheel",
        "--outdir",
        str(output),
        str(path),
    ]

    click.echo("")
    click.echo("Building wheel...")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        click.echo(result.stdout)

        # Find the built wheel
        wheels = list(output.glob(f"{name.replace('-', '_')}-*.whl"))
        if wheels:
            wheel_file = wheels[-1]  # Most recent
            click.echo("")
            click.echo(click.style(f"Successfully built: {wheel_file.name}", fg="green"))
            click.echo(f"  Location: {wheel_file}")
        else:
            click.echo(click.style("Build completed but wheel not found", fg="yellow"))

    except subprocess.CalledProcessError as e:
        click.echo(e.stderr, err=True)
        click.echo("")
        click.echo(click.style("Build failed", fg="red"), err=True)

        # Suggest installing build if not available
        if "No module named build" in (e.stderr or ""):
            click.echo("")
            if is_uv_available():
                click.echo("Install the build module with:")
                click.echo("  uv pip install build")
            else:
                click.echo("Install the build module with:")
                click.echo("  pip install build")

        sys.exit(1)


def sparse_checkout(repo_url: str, subdir: str, tag: str | None = None) -> Path:
    """Sparse checkout a single directory from a repo.

    Args:
        repo_url: Git repository URL
        subdir: Subdirectory to checkout
        tag: Optional git tag to checkout

    Returns:
        Path to the checked out subdirectory
    """
    tmpdir = Path(tempfile.mkdtemp())

    # Clone with sparse checkout enabled
    clone_cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--filter=blob:none",
        "--sparse",
    ]
    if tag:
        clone_cmd.extend(["--branch", tag])
    clone_cmd.extend([repo_url, str(tmpdir)])

    subprocess.run(clone_cmd, check=True, capture_output=True)

    # Set the sparse checkout path
    subprocess.run(
        ["git", "-C", str(tmpdir), "sparse-checkout", "set", subdir],
        check=True,
        capture_output=True,
    )

    return tmpdir / subdir


@main.command()
@click.argument("package")
@click.option(
    "--version",
    "-v",
    default=None,
    help="Specific version to install (e.g., '4.5.0')",
)
@click.option(
    "--repo",
    default=SPICYCRAB_STUBS_REPO,
    help="Stubs repository URL",
    show_default=True,
)
def install(package: str, version: str | None, repo: str):
    """Install a stub package from the spicycrab-stubs repository.

    \b
    This command:
    1. Sparse checkouts the stub from spicycrab-stubs repo
    2. Builds the wheel locally
    3. Installs it with pip (or uv pip if available)

    The package name should be the crate name (e.g., 'clap').

    \b
    Examples:
        cookcrab install clap              # Latest version
        cookcrab install clap -v 4.5.0     # Specific version (tag: clap-4.5.0)
        cookcrab install tokio             # Latest tokio stubs

    \b
    DO NOT install stubs using pip directly from PyPI.
    Always use `cookcrab install` instead.
    """
    # Normalize package name (remove spicycrab- prefix if present)
    crate_name = package.replace("spicycrab-", "")

    # Determine git tag if version specified
    tag = f"{crate_name}-{version}" if version else None

    using_uv = is_uv_available()
    pip_tool = "uv pip" if using_uv else "pip"

    click.echo(f"Installing spicycrab-{crate_name} from spicycrab-stubs...")
    click.echo(f"  Repository: {repo}")
    click.echo(f"  Package manager: {pip_tool}")
    if tag:
        click.echo(f"  Tag: {tag}")
    click.echo("")

    # Step 1: Sparse checkout
    click.echo("Fetching stub package...")
    try:
        # Stubs are stored in stubs/<crate_name>/ directory in the repo
        stub_path = sparse_checkout(repo, f"stubs/{crate_name}", tag)
    except subprocess.CalledProcessError:
        click.echo(click.style("Failed to fetch stub package", fg="red"), err=True)
        if tag:
            click.echo(f"  Tag '{tag}' may not exist. Try without -v flag for latest.", err=True)
        else:
            click.echo(f"  Stub 'stubs/{crate_name}' may not exist in the repository.", err=True)
        click.echo("")
        click.echo("Available stubs can be found at:")
        click.echo(f"  {repo.replace('.git', '')}")
        sys.exit(1)

    if not stub_path.exists():
        click.echo(click.style(f"Stub '{crate_name}' not found in repository", fg="red"), err=True)
        sys.exit(1)

    # Step 2: Build wheel
    click.echo("Building wheel...")
    wheel_dir = Path(tempfile.mkdtemp())

    try:
        build_cmd = get_build_command() + [
            "--wheel",
            "--outdir",
            str(wheel_dir),
            str(stub_path),
        ]
        subprocess.run(build_cmd, check=True, capture_output=True, text=True)

        # Find the built wheel
        wheels = list(wheel_dir.glob("*.whl"))
        if not wheels:
            click.echo(click.style("Failed to build wheel", fg="red"), err=True)
            sys.exit(1)

        wheel_file = wheels[0]
        click.echo(f"  Built: {wheel_file.name}")

        # Step 3: Install wheel
        click.echo("Installing...")
        install_cmd = get_pip_command() + [
            "install",
            "--force-reinstall",
            str(wheel_file),
        ]
        subprocess.run(install_cmd, check=True, capture_output=True, text=True)

        click.echo("")
        click.echo(click.style(f"Successfully installed spicycrab-{crate_name}", fg="green"))
        click.echo("")
        click.echo("The stub package is now available for spicycrab transpilation.")
        click.echo(f"  Import: from spicycrab_{crate_name.replace('-', '_')} import ...")

    except subprocess.CalledProcessError as e:
        click.echo(e.stderr if e.stderr else str(e), err=True)
        click.echo(click.style("Installation failed", fg="red"), err=True)
        sys.exit(1)

    finally:
        # Cleanup
        shutil.rmtree(stub_path.parent, ignore_errors=True)
        shutil.rmtree(wheel_dir, ignore_errors=True)


@main.command()
@click.argument("query")
def search(query: str):
    """Search for available stub packages.

    Lists stub packages available in the spicycrab-stubs repository.

    \b
    Examples:
        cookcrab search clap
        cookcrab search async
    """
    click.echo(f"Searching for '{query}'...")
    click.echo("")
    click.echo("Browse available stubs at:")
    click.echo(f"  {SPICYCRAB_STUBS_REPO.replace('.git', '')}")
    click.echo("")
    click.echo("Available stubs:")
    click.echo("  - clap       (CLI argument parser)")
    click.echo("")
    click.echo("To install a stub:")
    click.echo("  cookcrab install <crate_name>")
    click.echo("  cookcrab install <crate_name> -v <version>")


@main.command()
@click.argument("crate", type=str)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=Path("."),
    help="Output directory for generated stub package (default: current directory)",
)
@click.option(
    "-v",
    "--version",
    "crate_version",
    default=None,
    help="Crate version (default: latest from crates.io, or 0.1.0 for local)",
)
@click.option(
    "--local",
    is_flag=True,
    help="Treat CRATE as a local path instead of crate name",
)
@click.option(
    "-n",
    "--name",
    "output_name",
    default=None,
    help="Output crate name (default: same as input crate). Use for re-exports like clap_builder -> clap",
)
@click.option(
    "--debug-log",
    is_flag=True,
    help="Enable debug JSON logging to .spicycrab-logs/",
)
def generate(crate: str, output: Path, crate_version: str | None, local: bool, output_name: str | None, debug_log: bool):
    """Generate stubs from a Rust crate.

    Parses a Rust crate and generates Python type stubs with
    spicycrab mappings.

    \b
    Examples:
        cookcrab generate clap                            # From crates.io (latest)
        cookcrab generate clap -v 4.5.0                  # Specific version
        cookcrab generate ./my-crate --local             # From local path
        cookcrab generate ./my-crate --local -v 1.0.0   # Local with version
        cookcrab generate clap -o ./stubs                # Custom output dir

    \b
    The generated stub package will be created at:
        <output>/<crate_name>/
            pyproject.toml
            spicycrab_<crate_name>/
                __init__.py
                _spicycrab.toml
            README.md
    """
    try:
        from spicycrab.cookcrab._parser import parse_crate
    except ImportError:
        click.echo(
            click.style(
                "Error: Rust parser not available.",
                fg="red",
            ),
            err=True,
        )
        click.echo("")
        click.echo("The parser should be built when installing cookcrab.")
        click.echo("Try reinstalling with: uv pip install cookcrab")
        sys.exit(1)

    from spicycrab.cookcrab.generator import generate_stub_package

    # Enable debug logging if requested
    if debug_log:
        from spicycrab.debug_log import enable_logging

        enable_logging("stubs", crate)

    temp_dir = None
    crate_name = crate

    if local:
        # Local crate path
        crate_path = Path(crate)
        if not crate_path.exists():
            click.echo(click.style(f"Error: Path not found: {crate}", fg="red"), err=True)
            sys.exit(1)

        if crate_version is None:
            crate_version = "0.1.0"

        click.echo(f"Generating stubs from local crate at: {crate_path}")
        click.echo(f"  Output directory: {output}")
        click.echo(f"  Version: {crate_version}")
        click.echo("")
    else:
        # Download from crates.io
        click.echo("Fetching crate info from crates.io...")

        crate_info = fetch_crate_info(crate)
        crate_name = crate_info.get("id", crate)

        if crate_version is None:
            crate_version = crate_info.get("max_version", "0.1.0")
            click.echo(f"  Latest version: {crate_version}")
        else:
            click.echo(f"  Requested version: {crate_version}")

        click.echo(f"  Description: {crate_info.get('description', 'N/A')}")
        click.echo("")

        # Download and extract
        click.echo(f"Downloading {crate_name} v{crate_version}...")
        temp_dir = Path(tempfile.mkdtemp())
        try:
            crate_path = download_crate(crate_name, crate_version, temp_dir)
            click.echo(f"  Extracted to: {crate_path}")
        except click.ClickException:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise

        click.echo(f"  Output directory: {output}")
        click.echo("")

    # Parse the crate
    click.echo("Parsing Rust crate...")
    try:
        parsed_crate = parse_crate(str(crate_path.absolute()))
    except Exception as e:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        click.echo(click.style(f"Error parsing crate: {e}", fg="red"), err=True)
        sys.exit(1)

    # Use the parsed crate name, but prefer the one from crates.io for remote crates
    if local:
        crate_name = parsed_crate.name

    click.echo(f"  Crate name: {crate_name}")
    click.echo(f"  Found {len(parsed_crate.structs)} struct(s)")
    click.echo(f"  Found {len(parsed_crate.enums)} enum(s)")
    click.echo(f"  Found {len(parsed_crate.functions)} function(s)")
    click.echo(f"  Found {len(parsed_crate.impls)} impl block(s)")
    click.echo(f"  Found {len(parsed_crate.type_aliases)} type alias(es)")
    click.echo(f"  Found {len(parsed_crate.reexports)} re-export(s)")

    # Check for glob re-exports from other crates
    glob_reexports = [r for r in parsed_crate.reexports if r.is_glob]
    source_crates_to_generate = []

    if glob_reexports and len(parsed_crate.structs) + len(parsed_crate.enums) + len(parsed_crate.impls) < 5:
        click.echo("")
        click.echo(click.style("Detected re-exports from other crates:", fg="yellow"))
        for r in glob_reexports:
            click.echo(f"  pub use {r.source_crate}::*")
            source_crates_to_generate.append(r.source_crate)
        click.echo("")
        click.echo("This crate re-exports from other crates. Will generate stubs for source crates.")
    click.echo("")

    # Generate stubs for source crates first (if any)
    for source_crate in source_crates_to_generate:
        if not local:
            click.echo(f"Generating stubs for source crate: {source_crate}...")
            try:
                source_info = fetch_crate_info(source_crate)
                source_version = source_info.get("max_version", "0.1.0")
                click.echo(f"  Version: {source_version}")

                source_temp_dir = Path(tempfile.mkdtemp())
                source_path = download_crate(source_crate, source_version, source_temp_dir)
                source_parsed = parse_crate(str(source_path.absolute()))

                click.echo(f"  Found {len(source_parsed.structs)} struct(s)")
                click.echo(f"  Found {len(source_parsed.impls)} impl block(s)")

                # Generate the source crate stubs
                from spicycrab.cookcrab.generator import generate_stub_package

                generate_stub_package(
                    crate=source_parsed,
                    crate_name=source_crate,
                    version=source_version,
                    output_dir=output,
                )
                click.echo(f"  Generated: {output / source_crate}")

                shutil.rmtree(source_temp_dir, ignore_errors=True)
            except Exception as e:
                click.echo(click.style(f"  Warning: Could not generate {source_crate}: {e}", fg="yellow"))
        click.echo("")

    # Generate the stub package
    click.echo("Generating stub package...")
    try:
        if source_crates_to_generate:
            # This is a wrapper crate - generate re-export stub
            from spicycrab.cookcrab.generator import generate_reexport_stub_package

            generate_reexport_stub_package(
                crate_name=crate_name,
                source_crates=source_crates_to_generate,
                version=crate_version,
                output_dir=output,
            )
            pass  # No GeneratedStub returned for re-export packages
        else:
            generate_stub_package(
                crate=parsed_crate,
                crate_name=crate_name,
                version=crate_version,
                output_dir=output,
            )
    except Exception as e:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        click.echo(click.style(f"Error generating stubs: {e}", fg="red"), err=True)
        sys.exit(1)

    # Cleanup temp directory
    if temp_dir:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Save debug log if enabled
    if debug_log:
        from spicycrab.debug_log import save_log

        log_path = save_log(output)
        if log_path:
            click.echo(f"  Debug log: {log_path}")

    click.echo("")
    click.echo(click.style("Stub package generated successfully!", fg="green"))
    click.echo("")
    click.echo(f"Output directory: {output / crate_name}")
    click.echo("")
    click.echo("Next steps:")
    click.echo("  1. Review and edit the generated stubs")
    click.echo(f"  2. Validate: cookcrab validate {output / crate_name}")
    click.echo(f"  3. Build: cookcrab build {output / crate_name}")
    click.echo("")
    click.echo("To contribute to spicycrab-stubs:")
    click.echo(f"  1. Copy {output / crate_name} to stubs/ in your spicycrab-stubs clone")
    click.echo(f"  2. Run: just tag {crate_name} {crate_version}")
    click.echo(f"  3. Push: git push origin main && git push origin {crate_name}-{crate_version}")


if __name__ == "__main__":
    main()
