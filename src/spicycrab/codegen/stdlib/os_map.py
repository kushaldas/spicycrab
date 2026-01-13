"""Mappings for Python os and pathlib modules to Rust std::path and std::fs."""

from __future__ import annotations

from spicycrab.codegen.stdlib.types import StdlibMapping

# os module mappings
OS_MAPPINGS: dict[str, StdlibMapping] = {
    "os.getcwd": StdlibMapping(
        python_module="os",
        python_func="getcwd",
        rust_code="std::env::current_dir().unwrap().to_string_lossy().to_string()",
        rust_imports=[],  # Using full path, no import needed
        needs_result=True,
    ),
    "os.chdir": StdlibMapping(
        python_module="os",
        python_func="chdir",
        rust_code="std::env::set_current_dir({args}).unwrap()",
        rust_imports=[],  # Using full path, no import needed
        needs_result=True,
    ),
    "os.listdir": StdlibMapping(
        python_module="os",
        python_func="listdir",
        rust_code=(
            "std::fs::read_dir({args}).unwrap()"
            ".map(|e| e.unwrap().file_name().to_string_lossy().to_string()).collect::<Vec<_>>()"
        ),
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "os.mkdir": StdlibMapping(
        python_module="os",
        python_func="mkdir",
        rust_code="std::fs::create_dir({args}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "os.makedirs": StdlibMapping(
        python_module="os",
        python_func="makedirs",
        rust_code="std::fs::create_dir_all({args}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "os.remove": StdlibMapping(
        python_module="os",
        python_func="remove",
        rust_code="std::fs::remove_file({args}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "os.rmdir": StdlibMapping(
        python_module="os",
        python_func="rmdir",
        rust_code="std::fs::remove_dir({args}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "os.rename": StdlibMapping(
        python_module="os",
        python_func="rename",
        rust_code="std::fs::rename({args}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "os.path.exists": StdlibMapping(
        python_module="os.path",
        python_func="exists",
        rust_code="std::path::Path::new(&{args}).exists()",
        rust_imports=[],  # Using full path, no import needed
    ),
    "os.path.isfile": StdlibMapping(
        python_module="os.path",
        python_func="isfile",
        rust_code="std::path::Path::new(&{args}).is_file()",
        rust_imports=[],  # Using full path, no import needed
    ),
    "os.path.isdir": StdlibMapping(
        python_module="os.path",
        python_func="isdir",
        rust_code="std::path::Path::new(&{args}).is_dir()",
        rust_imports=[],  # Using full path, no import needed
    ),
    "os.path.join": StdlibMapping(
        python_module="os.path",
        python_func="join",
        rust_code="std::path::Path::new(&{arg0}).join(&{arg1}).to_string_lossy().to_string()",
        rust_imports=[],  # Using full path, no import needed
    ),
    "os.path.basename": StdlibMapping(
        python_module="os.path",
        python_func="basename",
        rust_code=(
            "std::path::Path::new(&{args}).file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default()"
        ),
        rust_imports=[],  # Using full path, no import needed
    ),
    "os.path.dirname": StdlibMapping(
        python_module="os.path",
        python_func="dirname",
        rust_code=(
            "std::path::Path::new(&{args}).parent().map(|p| p.to_string_lossy().to_string()).unwrap_or_default()"
        ),
        rust_imports=[],  # Using full path, no import needed
    ),
    "os.getenv": StdlibMapping(
        python_module="os",
        python_func="getenv",
        rust_code="std::env::var({args}).ok()",
        rust_imports=[],  # Using full path, no import needed
    ),
    "os.path.splitext": StdlibMapping(
        python_module="os.path",
        python_func="splitext",
        # Returns (stem, extension_with_dot) - returns tuple for indexing like Python
        # Using {arg0} instead of {args} to avoid format() escaping issues with braces
        rust_code=(
            '({ '
            'let __path = std::path::Path::new(&{arg0}); '
            '('
            '__path.file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default(), '
            '__path.extension().map(|s| format!(".{}", s.to_string_lossy())).unwrap_or_default()'
            ')'
            ' })'
        ),
        rust_imports=[],
    ),
}

# pathlib.Path mappings (method calls on Path objects)
PATHLIB_MAPPINGS: dict[str, StdlibMapping] = {
    "Path": StdlibMapping(
        python_module="pathlib",
        python_func="Path",
        rust_code="PathBuf::from({args})",
        rust_imports=["std::path::PathBuf"],
    ),
    "Path.read_text": StdlibMapping(
        python_module="pathlib",
        python_func="read_text",
        rust_code="std::fs::read_to_string({self}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "Path.read_bytes": StdlibMapping(
        python_module="pathlib",
        python_func="read_bytes",
        rust_code="std::fs::read({self}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "Path.write_text": StdlibMapping(
        python_module="pathlib",
        python_func="write_text",
        rust_code="std::fs::write({self}, {args}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "Path.write_bytes": StdlibMapping(
        python_module="pathlib",
        python_func="write_bytes",
        rust_code="std::fs::write({self}, {args}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "Path.exists": StdlibMapping(
        python_module="pathlib",
        python_func="exists",
        rust_code="{self}.exists()",
        rust_imports=[],
    ),
    "Path.is_file": StdlibMapping(
        python_module="pathlib",
        python_func="is_file",
        rust_code="{self}.is_file()",
        rust_imports=[],
    ),
    "Path.is_dir": StdlibMapping(
        python_module="pathlib",
        python_func="is_dir",
        rust_code="{self}.is_dir()",
        rust_imports=[],
    ),
    "Path.mkdir": StdlibMapping(
        python_module="pathlib",
        python_func="mkdir",
        rust_code="std::fs::create_dir_all({self}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "Path.unlink": StdlibMapping(
        python_module="pathlib",
        python_func="unlink",
        rust_code="std::fs::remove_file({self}).unwrap()",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "Path.parent": StdlibMapping(
        python_module="pathlib",
        python_func="parent",
        rust_code="{self}.parent().map(|p| p.to_path_buf())",
        rust_imports=[],
    ),
    "Path.name": StdlibMapping(
        python_module="pathlib",
        python_func="name",
        rust_code="{self}.file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default()",
        rust_imports=[],
    ),
    "Path.stem": StdlibMapping(
        python_module="pathlib",
        python_func="stem",
        rust_code="{self}.file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default()",
        rust_imports=[],
    ),
    "Path.suffix": StdlibMapping(
        python_module="pathlib",
        python_func="suffix",
        rust_code='{self}.extension().map(|s| format!(".", s.to_string_lossy())).unwrap_or_default()',
        rust_imports=[],
    ),
    "Path.joinpath": StdlibMapping(
        python_module="pathlib",
        python_func="joinpath",
        rust_code="{self}.join({args})",
        rust_imports=[],
    ),
    "Path.join": StdlibMapping(
        python_module="pathlib",
        python_func="join",
        rust_code="{self}.join({args})",
        rust_imports=[],
    ),
    "Path.__truediv__": StdlibMapping(
        python_module="pathlib",
        python_func="__truediv__",
        rust_code="{self}.join({args})",
        rust_imports=[],
    ),
}


# sys module mappings
SYS_MAPPINGS: dict[str, StdlibMapping] = {
    "sys.argv": StdlibMapping(
        python_module="sys",
        python_func="argv",
        rust_code="std::env::args().collect::<Vec<_>>()",
        rust_imports=[],  # Using full path, no import needed
    ),
    "sys.exit": StdlibMapping(
        python_module="sys",
        python_func="exit",
        rust_code="std::process::exit({args})",
        rust_imports=[],  # Using full path, no import needed
    ),
    "sys.platform": StdlibMapping(
        python_module="sys",
        python_func="platform",
        rust_code="std::env::consts::OS.to_string()",
        rust_imports=[],
    ),
    "sys.version": StdlibMapping(
        python_module="sys",
        python_func="version",
        rust_code='"Rust"',  # No direct equivalent
        rust_imports=[],
    ),
    "sys.path": StdlibMapping(
        python_module="sys",
        python_func="path",
        rust_code="vec![]",  # No direct equivalent in Rust
        rust_imports=[],
    ),
    "sys.stdin": StdlibMapping(
        python_module="sys",
        python_func="stdin",
        rust_code="std::io::stdin()",
        rust_imports=["std::io"],
    ),
    "sys.stdout": StdlibMapping(
        python_module="sys",
        python_func="stdout",
        rust_code="std::io::stdout()",
        rust_imports=["std::io"],
    ),
    "sys.stderr": StdlibMapping(
        python_module="sys",
        python_func="stderr",
        rust_code="std::io::stderr()",
        rust_imports=["std::io"],
    ),
}


def get_os_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for an os module function."""
    return OS_MAPPINGS.get(func_name)


def get_pathlib_mapping(method_name: str) -> StdlibMapping | None:
    """Get mapping for a pathlib.Path method."""
    return PATHLIB_MAPPINGS.get(method_name)


def get_sys_mapping(attr_name: str) -> StdlibMapping | None:
    """Get mapping for a sys module attribute/function."""
    return SYS_MAPPINGS.get(attr_name)
