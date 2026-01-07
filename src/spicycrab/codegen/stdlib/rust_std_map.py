"""Mappings for Rust standard library modules.

This module provides mappings for Rust std types that are commonly used
by external crates. These mappings enable:
1. cookcrab to generate valid Python stubs
2. spicycrab to transpile code using these types back to Rust

Supported modules:
- std::fs - File system operations
- std::io - Input/Output traits and types
- std::path - Path manipulation (extended from os_map.py)
"""

from __future__ import annotations

from spicycrab.codegen.stdlib.types import StdlibMapping

# =============================================================================
# std::fs - File system operations
# =============================================================================

FS_MAPPINGS: dict[str, StdlibMapping] = {
    # File type and constructors
    "rust_std.fs.File": StdlibMapping(
        python_module="rust_std.fs",
        python_func="File",
        rust_code="std::fs::File",
        rust_imports=["std::fs::File"],
    ),
    "rust_std.fs.File.open": StdlibMapping(
        python_module="rust_std.fs",
        python_func="File.open",
        rust_code="std::fs::File::open({args})?",
        rust_imports=["std::fs::File"],
        needs_result=True,
    ),
    "rust_std.fs.File.create": StdlibMapping(
        python_module="rust_std.fs",
        python_func="File.create",
        rust_code="std::fs::File::create({args})?",
        rust_imports=["std::fs::File"],
        needs_result=True,
    ),
    # OpenOptions builder
    "rust_std.fs.OpenOptions": StdlibMapping(
        python_module="rust_std.fs",
        python_func="OpenOptions",
        rust_code="std::fs::OpenOptions::new()",
        rust_imports=["std::fs::OpenOptions"],
    ),
    "rust_std.fs.OpenOptions.new": StdlibMapping(
        python_module="rust_std.fs",
        python_func="OpenOptions.new",
        rust_code="std::fs::OpenOptions::new()",
        rust_imports=["std::fs::OpenOptions"],
    ),
    # File reading functions
    "rust_std.fs.read_to_string": StdlibMapping(
        python_module="rust_std.fs",
        python_func="read_to_string",
        rust_code="std::fs::read_to_string({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "rust_std.fs.read": StdlibMapping(
        python_module="rust_std.fs",
        python_func="read",
        rust_code="std::fs::read({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    # File writing functions
    "rust_std.fs.write": StdlibMapping(
        python_module="rust_std.fs",
        python_func="write",
        rust_code="std::fs::write({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    # File operations
    "rust_std.fs.copy": StdlibMapping(
        python_module="rust_std.fs",
        python_func="copy",
        rust_code="std::fs::copy({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "rust_std.fs.rename": StdlibMapping(
        python_module="rust_std.fs",
        python_func="rename",
        rust_code="std::fs::rename({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "rust_std.fs.remove_file": StdlibMapping(
        python_module="rust_std.fs",
        python_func="remove_file",
        rust_code="std::fs::remove_file({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    # Directory operations
    "rust_std.fs.create_dir": StdlibMapping(
        python_module="rust_std.fs",
        python_func="create_dir",
        rust_code="std::fs::create_dir({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "rust_std.fs.create_dir_all": StdlibMapping(
        python_module="rust_std.fs",
        python_func="create_dir_all",
        rust_code="std::fs::create_dir_all({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "rust_std.fs.remove_dir": StdlibMapping(
        python_module="rust_std.fs",
        python_func="remove_dir",
        rust_code="std::fs::remove_dir({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "rust_std.fs.remove_dir_all": StdlibMapping(
        python_module="rust_std.fs",
        python_func="remove_dir_all",
        rust_code="std::fs::remove_dir_all({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "rust_std.fs.read_dir": StdlibMapping(
        python_module="rust_std.fs",
        python_func="read_dir",
        rust_code="std::fs::read_dir({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    # Metadata
    "rust_std.fs.metadata": StdlibMapping(
        python_module="rust_std.fs",
        python_func="metadata",
        rust_code="std::fs::metadata({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "rust_std.fs.symlink_metadata": StdlibMapping(
        python_module="rust_std.fs",
        python_func="symlink_metadata",
        rust_code="std::fs::symlink_metadata({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    # Permissions
    "rust_std.fs.set_permissions": StdlibMapping(
        python_module="rust_std.fs",
        python_func="set_permissions",
        rust_code="std::fs::set_permissions({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    # Canonicalize
    "rust_std.fs.canonicalize": StdlibMapping(
        python_module="rust_std.fs",
        python_func="canonicalize",
        rust_code="std::fs::canonicalize({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    # Hard/soft links
    "rust_std.fs.hard_link": StdlibMapping(
        python_module="rust_std.fs",
        python_func="hard_link",
        rust_code="std::fs::hard_link({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
    "rust_std.fs.soft_link": StdlibMapping(
        python_module="rust_std.fs",
        python_func="soft_link",
        rust_code="std::os::unix::fs::symlink({args})?",
        rust_imports=["std::os::unix::fs"],
        needs_result=True,
    ),
    "rust_std.fs.read_link": StdlibMapping(
        python_module="rust_std.fs",
        python_func="read_link",
        rust_code="std::fs::read_link({args})?",
        rust_imports=["std::fs"],
        needs_result=True,
    ),
}

# std::fs method mappings (for File instance methods)
FS_METHOD_MAPPINGS: dict[str, StdlibMapping] = {
    # OpenOptions builder methods
    "OpenOptions.read": StdlibMapping(
        python_module="rust_std.fs",
        python_func="read",
        rust_code="{self}.read({args})",
        rust_imports=[],
    ),
    "OpenOptions.write": StdlibMapping(
        python_module="rust_std.fs",
        python_func="write",
        rust_code="{self}.write({args})",
        rust_imports=[],
    ),
    "OpenOptions.append": StdlibMapping(
        python_module="rust_std.fs",
        python_func="append",
        rust_code="{self}.append({args})",
        rust_imports=[],
    ),
    "OpenOptions.truncate": StdlibMapping(
        python_module="rust_std.fs",
        python_func="truncate",
        rust_code="{self}.truncate({args})",
        rust_imports=[],
    ),
    "OpenOptions.create": StdlibMapping(
        python_module="rust_std.fs",
        python_func="create",
        rust_code="{self}.create({args})",
        rust_imports=[],
    ),
    "OpenOptions.create_new": StdlibMapping(
        python_module="rust_std.fs",
        python_func="create_new",
        rust_code="{self}.create_new({args})",
        rust_imports=[],
    ),
    "OpenOptions.open": StdlibMapping(
        python_module="rust_std.fs",
        python_func="open",
        rust_code="{self}.open({args})?",
        rust_imports=[],
        needs_result=True,
    ),
    # File methods
    "File.sync_all": StdlibMapping(
        python_module="rust_std.fs",
        python_func="sync_all",
        rust_code="{self}.sync_all()?",
        rust_imports=[],
        needs_result=True,
    ),
    "File.sync_data": StdlibMapping(
        python_module="rust_std.fs",
        python_func="sync_data",
        rust_code="{self}.sync_data()?",
        rust_imports=[],
        needs_result=True,
    ),
    "File.set_len": StdlibMapping(
        python_module="rust_std.fs",
        python_func="set_len",
        rust_code="{self}.set_len({args})?",
        rust_imports=[],
        needs_result=True,
    ),
    "File.metadata": StdlibMapping(
        python_module="rust_std.fs",
        python_func="metadata",
        rust_code="{self}.metadata()?",
        rust_imports=[],
        needs_result=True,
    ),
    # Metadata methods
    "Metadata.is_file": StdlibMapping(
        python_module="rust_std.fs",
        python_func="is_file",
        rust_code="{self}.is_file()",
        rust_imports=[],
    ),
    "Metadata.is_dir": StdlibMapping(
        python_module="rust_std.fs",
        python_func="is_dir",
        rust_code="{self}.is_dir()",
        rust_imports=[],
    ),
    "Metadata.is_symlink": StdlibMapping(
        python_module="rust_std.fs",
        python_func="is_symlink",
        rust_code="{self}.is_symlink()",
        rust_imports=[],
    ),
    "Metadata.len": StdlibMapping(
        python_module="rust_std.fs",
        python_func="len",
        rust_code="{self}.len()",
        rust_imports=[],
    ),
    "Metadata.permissions": StdlibMapping(
        python_module="rust_std.fs",
        python_func="permissions",
        rust_code="{self}.permissions()",
        rust_imports=[],
    ),
    "Metadata.modified": StdlibMapping(
        python_module="rust_std.fs",
        python_func="modified",
        rust_code="{self}.modified()?",
        rust_imports=[],
        needs_result=True,
    ),
    "Metadata.accessed": StdlibMapping(
        python_module="rust_std.fs",
        python_func="accessed",
        rust_code="{self}.accessed()?",
        rust_imports=[],
        needs_result=True,
    ),
    "Metadata.created": StdlibMapping(
        python_module="rust_std.fs",
        python_func="created",
        rust_code="{self}.created()?",
        rust_imports=[],
        needs_result=True,
    ),
    # DirEntry methods
    "DirEntry.path": StdlibMapping(
        python_module="rust_std.fs",
        python_func="path",
        rust_code="{self}.path()",
        rust_imports=[],
    ),
    "DirEntry.file_name": StdlibMapping(
        python_module="rust_std.fs",
        python_func="file_name",
        rust_code="{self}.file_name()",
        rust_imports=[],
    ),
    "DirEntry.metadata": StdlibMapping(
        python_module="rust_std.fs",
        python_func="metadata",
        rust_code="{self}.metadata()?",
        rust_imports=[],
        needs_result=True,
    ),
    "DirEntry.file_type": StdlibMapping(
        python_module="rust_std.fs",
        python_func="file_type",
        rust_code="{self}.file_type()?",
        rust_imports=[],
        needs_result=True,
    ),
}

# =============================================================================
# std::io - Input/Output operations
# =============================================================================

IO_MAPPINGS: dict[str, StdlibMapping] = {
    # Standard streams
    "rust_std.io.stdin": StdlibMapping(
        python_module="rust_std.io",
        python_func="stdin",
        rust_code="std::io::stdin()",
        rust_imports=["std::io"],
    ),
    "rust_std.io.stdout": StdlibMapping(
        python_module="rust_std.io",
        python_func="stdout",
        rust_code="std::io::stdout()",
        rust_imports=["std::io"],
    ),
    "rust_std.io.stderr": StdlibMapping(
        python_module="rust_std.io",
        python_func="stderr",
        rust_code="std::io::stderr()",
        rust_imports=["std::io"],
    ),
    # Stream types (for type annotations)
    "rust_std.io.Stdin": StdlibMapping(
        python_module="rust_std.io",
        python_func="Stdin",
        rust_code="std::io::Stdin",
        rust_imports=["std::io::Stdin"],
    ),
    "rust_std.io.Stdout": StdlibMapping(
        python_module="rust_std.io",
        python_func="Stdout",
        rust_code="std::io::Stdout",
        rust_imports=["std::io::Stdout"],
    ),
    "rust_std.io.Stderr": StdlibMapping(
        python_module="rust_std.io",
        python_func="Stderr",
        rust_code="std::io::Stderr",
        rust_imports=["std::io::Stderr"],
    ),
    # Buffered I/O
    "rust_std.io.BufReader": StdlibMapping(
        python_module="rust_std.io",
        python_func="BufReader",
        rust_code="std::io::BufReader::new({args})",
        rust_imports=["std::io::BufReader"],
    ),
    "rust_std.io.BufReader.new": StdlibMapping(
        python_module="rust_std.io",
        python_func="BufReader.new",
        rust_code="std::io::BufReader::new({args})",
        rust_imports=["std::io::BufReader"],
    ),
    "rust_std.io.BufWriter": StdlibMapping(
        python_module="rust_std.io",
        python_func="BufWriter",
        rust_code="std::io::BufWriter::new({args})",
        rust_imports=["std::io::BufWriter"],
    ),
    "rust_std.io.BufWriter.new": StdlibMapping(
        python_module="rust_std.io",
        python_func="BufWriter.new",
        rust_code="std::io::BufWriter::new({args})",
        rust_imports=["std::io::BufWriter"],
    ),
    # Cursor (in-memory I/O)
    "rust_std.io.Cursor": StdlibMapping(
        python_module="rust_std.io",
        python_func="Cursor",
        rust_code="std::io::Cursor::new({args})",
        rust_imports=["std::io::Cursor"],
    ),
    "rust_std.io.Cursor.new": StdlibMapping(
        python_module="rust_std.io",
        python_func="Cursor.new",
        rust_code="std::io::Cursor::new({args})",
        rust_imports=["std::io::Cursor"],
    ),
    # Empty/Sink/Repeat
    "rust_std.io.empty": StdlibMapping(
        python_module="rust_std.io",
        python_func="empty",
        rust_code="std::io::empty()",
        rust_imports=["std::io"],
    ),
    "rust_std.io.sink": StdlibMapping(
        python_module="rust_std.io",
        python_func="sink",
        rust_code="std::io::sink()",
        rust_imports=["std::io"],
    ),
    "rust_std.io.repeat": StdlibMapping(
        python_module="rust_std.io",
        python_func="repeat",
        rust_code="std::io::repeat({args})",
        rust_imports=["std::io"],
    ),
    # Copy
    "rust_std.io.copy": StdlibMapping(
        python_module="rust_std.io",
        python_func="copy",
        rust_code="std::io::copy({args})?",
        rust_imports=["std::io"],
        needs_result=True,
    ),
}

# std::io method mappings (for Read/Write trait methods)
IO_METHOD_MAPPINGS: dict[str, StdlibMapping] = {
    # Read trait methods
    "Read.read": StdlibMapping(
        python_module="rust_std.io",
        python_func="read",
        rust_code="{self}.read({args})?",
        rust_imports=["std::io::Read"],
        needs_result=True,
    ),
    "Read.read_to_end": StdlibMapping(
        python_module="rust_std.io",
        python_func="read_to_end",
        rust_code="{self}.read_to_end({args})?",
        rust_imports=["std::io::Read"],
        needs_result=True,
    ),
    "Read.read_to_string": StdlibMapping(
        python_module="rust_std.io",
        python_func="read_to_string",
        rust_code="{self}.read_to_string({args})?",
        rust_imports=["std::io::Read"],
        needs_result=True,
    ),
    "Read.read_exact": StdlibMapping(
        python_module="rust_std.io",
        python_func="read_exact",
        rust_code="{self}.read_exact({args})?",
        rust_imports=["std::io::Read"],
        needs_result=True,
    ),
    "Read.bytes": StdlibMapping(
        python_module="rust_std.io",
        python_func="bytes",
        rust_code="{self}.bytes()",
        rust_imports=["std::io::Read"],
    ),
    "Read.chain": StdlibMapping(
        python_module="rust_std.io",
        python_func="chain",
        rust_code="{self}.chain({args})",
        rust_imports=["std::io::Read"],
    ),
    "Read.take": StdlibMapping(
        python_module="rust_std.io",
        python_func="take",
        rust_code="{self}.take({args})",
        rust_imports=["std::io::Read"],
    ),
    # Write trait methods
    "Write.write": StdlibMapping(
        python_module="rust_std.io",
        python_func="write",
        rust_code="{self}.write({args})?",
        rust_imports=["std::io::Write"],
        needs_result=True,
    ),
    "Write.write_all": StdlibMapping(
        python_module="rust_std.io",
        python_func="write_all",
        rust_code="{self}.write_all({args})?",
        rust_imports=["std::io::Write"],
        needs_result=True,
    ),
    "Write.write_fmt": StdlibMapping(
        python_module="rust_std.io",
        python_func="write_fmt",
        rust_code="{self}.write_fmt({args})?",
        rust_imports=["std::io::Write"],
        needs_result=True,
    ),
    "Write.flush": StdlibMapping(
        python_module="rust_std.io",
        python_func="flush",
        rust_code="{self}.flush()?",
        rust_imports=["std::io::Write"],
        needs_result=True,
    ),
    # BufRead trait methods
    "BufRead.read_line": StdlibMapping(
        python_module="rust_std.io",
        python_func="read_line",
        rust_code="{self}.read_line({args})?",
        rust_imports=["std::io::BufRead"],
        needs_result=True,
    ),
    "BufRead.lines": StdlibMapping(
        python_module="rust_std.io",
        python_func="lines",
        rust_code="{self}.lines()",
        rust_imports=["std::io::BufRead"],
    ),
    "BufRead.split": StdlibMapping(
        python_module="rust_std.io",
        python_func="split",
        rust_code="{self}.split({args})",
        rust_imports=["std::io::BufRead"],
    ),
    "BufRead.fill_buf": StdlibMapping(
        python_module="rust_std.io",
        python_func="fill_buf",
        rust_code="{self}.fill_buf()?",
        rust_imports=["std::io::BufRead"],
        needs_result=True,
    ),
    "BufRead.consume": StdlibMapping(
        python_module="rust_std.io",
        python_func="consume",
        rust_code="{self}.consume({args})",
        rust_imports=["std::io::BufRead"],
    ),
    # Seek trait methods
    "Seek.seek": StdlibMapping(
        python_module="rust_std.io",
        python_func="seek",
        rust_code="{self}.seek({args})?",
        rust_imports=["std::io::Seek"],
        needs_result=True,
    ),
    "Seek.rewind": StdlibMapping(
        python_module="rust_std.io",
        python_func="rewind",
        rust_code="{self}.rewind()?",
        rust_imports=["std::io::Seek"],
        needs_result=True,
    ),
    "Seek.stream_position": StdlibMapping(
        python_module="rust_std.io",
        python_func="stream_position",
        rust_code="{self}.stream_position()?",
        rust_imports=["std::io::Seek"],
        needs_result=True,
    ),
    # BufReader/BufWriter specific methods
    "BufReader.buffer": StdlibMapping(
        python_module="rust_std.io",
        python_func="buffer",
        rust_code="{self}.buffer()",
        rust_imports=[],
    ),
    "BufReader.capacity": StdlibMapping(
        python_module="rust_std.io",
        python_func="capacity",
        rust_code="{self}.capacity()",
        rust_imports=[],
    ),
    "BufReader.into_inner": StdlibMapping(
        python_module="rust_std.io",
        python_func="into_inner",
        rust_code="{self}.into_inner()",
        rust_imports=[],
    ),
    "BufWriter.buffer": StdlibMapping(
        python_module="rust_std.io",
        python_func="buffer",
        rust_code="{self}.buffer()",
        rust_imports=[],
    ),
    "BufWriter.capacity": StdlibMapping(
        python_module="rust_std.io",
        python_func="capacity",
        rust_code="{self}.capacity()",
        rust_imports=[],
    ),
    "BufWriter.into_inner": StdlibMapping(
        python_module="rust_std.io",
        python_func="into_inner",
        rust_code="{self}.into_inner()?",
        rust_imports=[],
        needs_result=True,
    ),
    # Cursor methods
    "Cursor.into_inner": StdlibMapping(
        python_module="rust_std.io",
        python_func="into_inner",
        rust_code="{self}.into_inner()",
        rust_imports=[],
    ),
    "Cursor.get_ref": StdlibMapping(
        python_module="rust_std.io",
        python_func="get_ref",
        rust_code="{self}.get_ref()",
        rust_imports=[],
    ),
    "Cursor.get_mut": StdlibMapping(
        python_module="rust_std.io",
        python_func="get_mut",
        rust_code="{self}.get_mut()",
        rust_imports=[],
    ),
    "Cursor.position": StdlibMapping(
        python_module="rust_std.io",
        python_func="position",
        rust_code="{self}.position()",
        rust_imports=[],
    ),
    "Cursor.set_position": StdlibMapping(
        python_module="rust_std.io",
        python_func="set_position",
        rust_code="{self}.set_position({args})",
        rust_imports=[],
    ),
}

# =============================================================================
# std::path - Path manipulation (extended mappings)
# =============================================================================

PATH_MAPPINGS: dict[str, StdlibMapping] = {
    # Path constructors
    "rust_std.path.Path": StdlibMapping(
        python_module="rust_std.path",
        python_func="Path",
        rust_code="std::path::Path::new({args})",
        rust_imports=["std::path::Path"],
    ),
    "rust_std.path.Path.new": StdlibMapping(
        python_module="rust_std.path",
        python_func="Path.new",
        rust_code="std::path::Path::new({args})",
        rust_imports=["std::path::Path"],
    ),
    "rust_std.path.PathBuf": StdlibMapping(
        python_module="rust_std.path",
        python_func="PathBuf",
        rust_code="std::path::PathBuf::from({args})",
        rust_imports=["std::path::PathBuf"],
    ),
    "rust_std.path.PathBuf.new": StdlibMapping(
        python_module="rust_std.path",
        python_func="PathBuf.new",
        rust_code="std::path::PathBuf::new()",
        rust_imports=["std::path::PathBuf"],
    ),
    "rust_std.path.PathBuf.from": StdlibMapping(
        python_module="rust_std.path",
        python_func="PathBuf.from",
        rust_code="std::path::PathBuf::from({args})",
        rust_imports=["std::path::PathBuf"],
    ),
}

# std::path method mappings
PATH_METHOD_MAPPINGS: dict[str, StdlibMapping] = {
    # Path methods (also work on PathBuf via Deref)
    "Path.as_os_str": StdlibMapping(
        python_module="rust_std.path",
        python_func="as_os_str",
        rust_code="{self}.as_os_str()",
        rust_imports=[],
    ),
    "Path.to_str": StdlibMapping(
        python_module="rust_std.path",
        python_func="to_str",
        rust_code="{self}.to_str()",
        rust_imports=[],
    ),
    "Path.to_string_lossy": StdlibMapping(
        python_module="rust_std.path",
        python_func="to_string_lossy",
        rust_code="{self}.to_string_lossy().to_string()",
        rust_imports=[],
    ),
    "Path.to_path_buf": StdlibMapping(
        python_module="rust_std.path",
        python_func="to_path_buf",
        rust_code="{self}.to_path_buf()",
        rust_imports=[],
    ),
    "Path.is_absolute": StdlibMapping(
        python_module="rust_std.path",
        python_func="is_absolute",
        rust_code="{self}.is_absolute()",
        rust_imports=[],
    ),
    "Path.is_relative": StdlibMapping(
        python_module="rust_std.path",
        python_func="is_relative",
        rust_code="{self}.is_relative()",
        rust_imports=[],
    ),
    "Path.has_root": StdlibMapping(
        python_module="rust_std.path",
        python_func="has_root",
        rust_code="{self}.has_root()",
        rust_imports=[],
    ),
    "Path.parent": StdlibMapping(
        python_module="rust_std.path",
        python_func="parent",
        rust_code="{self}.parent()",
        rust_imports=[],
    ),
    "Path.ancestors": StdlibMapping(
        python_module="rust_std.path",
        python_func="ancestors",
        rust_code="{self}.ancestors()",
        rust_imports=[],
    ),
    "Path.file_name": StdlibMapping(
        python_module="rust_std.path",
        python_func="file_name",
        rust_code="{self}.file_name()",
        rust_imports=[],
    ),
    "Path.strip_prefix": StdlibMapping(
        python_module="rust_std.path",
        python_func="strip_prefix",
        rust_code="{self}.strip_prefix({args})",
        rust_imports=[],
    ),
    "Path.starts_with": StdlibMapping(
        python_module="rust_std.path",
        python_func="starts_with",
        rust_code="{self}.starts_with({args})",
        rust_imports=[],
    ),
    "Path.ends_with": StdlibMapping(
        python_module="rust_std.path",
        python_func="ends_with",
        rust_code="{self}.ends_with({args})",
        rust_imports=[],
    ),
    "Path.file_stem": StdlibMapping(
        python_module="rust_std.path",
        python_func="file_stem",
        rust_code="{self}.file_stem()",
        rust_imports=[],
    ),
    "Path.extension": StdlibMapping(
        python_module="rust_std.path",
        python_func="extension",
        rust_code="{self}.extension()",
        rust_imports=[],
    ),
    "Path.join": StdlibMapping(
        python_module="rust_std.path",
        python_func="join",
        rust_code="{self}.join({args})",
        rust_imports=[],
    ),
    "Path.with_file_name": StdlibMapping(
        python_module="rust_std.path",
        python_func="with_file_name",
        rust_code="{self}.with_file_name({args})",
        rust_imports=[],
    ),
    "Path.with_extension": StdlibMapping(
        python_module="rust_std.path",
        python_func="with_extension",
        rust_code="{self}.with_extension({args})",
        rust_imports=[],
    ),
    "Path.components": StdlibMapping(
        python_module="rust_std.path",
        python_func="components",
        rust_code="{self}.components()",
        rust_imports=[],
    ),
    "Path.iter": StdlibMapping(
        python_module="rust_std.path",
        python_func="iter",
        rust_code="{self}.iter()",
        rust_imports=[],
    ),
    "Path.display": StdlibMapping(
        python_module="rust_std.path",
        python_func="display",
        rust_code="{self}.display()",
        rust_imports=[],
    ),
    # Filesystem query methods (from Path)
    "Path.exists": StdlibMapping(
        python_module="rust_std.path",
        python_func="exists",
        rust_code="{self}.exists()",
        rust_imports=[],
    ),
    "Path.is_file": StdlibMapping(
        python_module="rust_std.path",
        python_func="is_file",
        rust_code="{self}.is_file()",
        rust_imports=[],
    ),
    "Path.is_dir": StdlibMapping(
        python_module="rust_std.path",
        python_func="is_dir",
        rust_code="{self}.is_dir()",
        rust_imports=[],
    ),
    "Path.is_symlink": StdlibMapping(
        python_module="rust_std.path",
        python_func="is_symlink",
        rust_code="{self}.is_symlink()",
        rust_imports=[],
    ),
    "Path.metadata": StdlibMapping(
        python_module="rust_std.path",
        python_func="metadata",
        rust_code="{self}.metadata()?",
        rust_imports=[],
        needs_result=True,
    ),
    "Path.symlink_metadata": StdlibMapping(
        python_module="rust_std.path",
        python_func="symlink_metadata",
        rust_code="{self}.symlink_metadata()?",
        rust_imports=[],
        needs_result=True,
    ),
    "Path.canonicalize": StdlibMapping(
        python_module="rust_std.path",
        python_func="canonicalize",
        rust_code="{self}.canonicalize()?",
        rust_imports=[],
        needs_result=True,
    ),
    "Path.read_link": StdlibMapping(
        python_module="rust_std.path",
        python_func="read_link",
        rust_code="{self}.read_link()?",
        rust_imports=[],
        needs_result=True,
    ),
    "Path.read_dir": StdlibMapping(
        python_module="rust_std.path",
        python_func="read_dir",
        rust_code="{self}.read_dir()?",
        rust_imports=[],
        needs_result=True,
    ),
    # PathBuf-specific methods
    "PathBuf.push": StdlibMapping(
        python_module="rust_std.path",
        python_func="push",
        rust_code="{self}.push({args})",
        rust_imports=[],
    ),
    "PathBuf.pop": StdlibMapping(
        python_module="rust_std.path",
        python_func="pop",
        rust_code="{self}.pop()",
        rust_imports=[],
    ),
    "PathBuf.set_file_name": StdlibMapping(
        python_module="rust_std.path",
        python_func="set_file_name",
        rust_code="{self}.set_file_name({args})",
        rust_imports=[],
    ),
    "PathBuf.set_extension": StdlibMapping(
        python_module="rust_std.path",
        python_func="set_extension",
        rust_code="{self}.set_extension({args})",
        rust_imports=[],
    ),
    "PathBuf.as_path": StdlibMapping(
        python_module="rust_std.path",
        python_func="as_path",
        rust_code="{self}.as_path()",
        rust_imports=[],
    ),
    "PathBuf.into_os_string": StdlibMapping(
        python_module="rust_std.path",
        python_func="into_os_string",
        rust_code="{self}.into_os_string()",
        rust_imports=[],
    ),
    "PathBuf.into_boxed_path": StdlibMapping(
        python_module="rust_std.path",
        python_func="into_boxed_path",
        rust_code="{self}.into_boxed_path()",
        rust_imports=[],
    ),
    "PathBuf.capacity": StdlibMapping(
        python_module="rust_std.path",
        python_func="capacity",
        rust_code="{self}.capacity()",
        rust_imports=[],
    ),
    "PathBuf.clear": StdlibMapping(
        python_module="rust_std.path",
        python_func="clear",
        rust_code="{self}.clear()",
        rust_imports=[],
    ),
    "PathBuf.reserve": StdlibMapping(
        python_module="rust_std.path",
        python_func="reserve",
        rust_code="{self}.reserve({args})",
        rust_imports=[],
    ),
    "PathBuf.reserve_exact": StdlibMapping(
        python_module="rust_std.path",
        python_func="reserve_exact",
        rust_code="{self}.reserve_exact({args})",
        rust_imports=[],
    ),
    "PathBuf.shrink_to_fit": StdlibMapping(
        python_module="rust_std.path",
        python_func="shrink_to_fit",
        rust_code="{self}.shrink_to_fit()",
        rust_imports=[],
    ),
}

# =============================================================================
# Type mappings for Rust std types (used by cookcrab stub generator)
# =============================================================================

RUST_STD_TYPE_MAPPINGS: dict[str, str] = {
    # std::fs types
    "fs::File": "File",
    "std::fs::File": "File",
    "fs::OpenOptions": "OpenOptions",
    "std::fs::OpenOptions": "OpenOptions",
    "fs::Metadata": "Metadata",
    "std::fs::Metadata": "Metadata",
    "fs::Permissions": "Permissions",
    "std::fs::Permissions": "Permissions",
    "fs::FileType": "FileType",
    "std::fs::FileType": "FileType",
    "fs::DirEntry": "DirEntry",
    "std::fs::DirEntry": "DirEntry",
    "fs::ReadDir": "ReadDir",
    "std::fs::ReadDir": "ReadDir",
    # std::io types
    "io::Stdin": "Stdin",
    "std::io::Stdin": "Stdin",
    "io::Stdout": "Stdout",
    "std::io::Stdout": "Stdout",
    "io::Stderr": "Stderr",
    "std::io::Stderr": "Stderr",
    "io::BufReader": "BufReader",
    "std::io::BufReader": "BufReader",
    "io::BufWriter": "BufWriter",
    "std::io::BufWriter": "BufWriter",
    "io::Cursor": "Cursor",
    "std::io::Cursor": "Cursor",
    "io::Error": "IoError",
    "std::io::Error": "IoError",
    "io::Result": "IoResult",
    "std::io::Result": "IoResult",
    "io::SeekFrom": "SeekFrom",
    "std::io::SeekFrom": "SeekFrom",
    # std::path types
    "path::Path": "Path",
    "std::path::Path": "Path",
    "path::PathBuf": "PathBuf",
    "std::path::PathBuf": "PathBuf",
    "path::Component": "Component",
    "std::path::Component": "Component",
    "path::Components": "Components",
    "std::path::Components": "Components",
    "path::Iter": "PathIter",
    "std::path::Iter": "PathIter",
    "path::Ancestors": "Ancestors",
    "std::path::Ancestors": "Ancestors",
    "path::Display": "PathDisplay",
    "std::path::Display": "PathDisplay",
    "path::StripPrefixError": "StripPrefixError",
    "std::path::StripPrefixError": "StripPrefixError",
}


def get_fs_mapping(key: str) -> StdlibMapping | None:
    """Get mapping for a std::fs function."""
    return FS_MAPPINGS.get(key)


def get_fs_method_mapping(type_name: str, method_name: str) -> StdlibMapping | None:
    """Get mapping for a std::fs method."""
    key = f"{type_name}.{method_name}"
    return FS_METHOD_MAPPINGS.get(key)


def get_io_mapping(key: str) -> StdlibMapping | None:
    """Get mapping for a std::io function."""
    return IO_MAPPINGS.get(key)


def get_io_method_mapping(type_name: str, method_name: str) -> StdlibMapping | None:
    """Get mapping for a std::io method."""
    key = f"{type_name}.{method_name}"
    return IO_METHOD_MAPPINGS.get(key)


def get_path_mapping(key: str) -> StdlibMapping | None:
    """Get mapping for a std::path function."""
    return PATH_MAPPINGS.get(key)


def get_path_method_mapping(type_name: str, method_name: str) -> StdlibMapping | None:
    """Get mapping for a std::path method."""
    key = f"{type_name}.{method_name}"
    return PATH_METHOD_MAPPINGS.get(key)


def get_rust_std_type(rust_type: str) -> str | None:
    """Get Python type name for a Rust std type.

    Used by cookcrab to convert Rust std types to Python stub types.
    """
    return RUST_STD_TYPE_MAPPINGS.get(rust_type)


def is_rust_std_type(rust_type: str) -> bool:
    """Check if a type is a known Rust std type."""
    # Direct match
    if rust_type in RUST_STD_TYPE_MAPPINGS:
        return True
    # Check without generics (e.g., BufReader<File> -> BufReader)
    base_type = rust_type.split("<")[0].strip()
    if base_type in RUST_STD_TYPE_MAPPINGS:
        return True
    # Also check if base type matches any Python type name (value side)
    # This handles short forms like "BufReader" without path prefix
    return base_type in RUST_STD_TYPE_MAPPINGS.values()
