"""Tests for stdlib mappings."""

import pytest

from spicycrab.codegen.stdlib import (
    get_stdlib_mapping,
    get_os_mapping,
    get_pathlib_mapping,
    get_sys_mapping,
    get_json_mapping,
    get_collections_mapping,
    get_logging_mapping,
    get_fs_mapping,
    get_fs_method_mapping,
    get_io_mapping,
    get_io_method_mapping,
    get_path_mapping,
    get_path_method_mapping,
    get_rust_std_type,
    is_rust_std_type,
    OS_MAPPINGS,
    SYS_MAPPINGS,
    PATHLIB_MAPPINGS,
    JSON_MAPPINGS,
    COLLECTIONS_MAPPINGS,
    LOGGING_MAPPINGS,
    FS_MAPPINGS,
    IO_MAPPINGS,
    PATH_MAPPINGS,
)


class TestOSMappings:
    """Tests for os module mappings."""

    def test_os_getcwd(self):
        """Test os.getcwd mapping."""
        mapping = get_stdlib_mapping("os", "getcwd")
        assert mapping is not None
        assert "current_dir" in mapping.rust_code
        # Uses fully qualified path, no import needed
        assert "std::env::current_dir" in mapping.rust_code

    def test_os_chdir(self):
        """Test os.chdir mapping."""
        mapping = get_stdlib_mapping("os", "chdir")
        assert mapping is not None
        assert "set_current_dir" in mapping.rust_code

    def test_os_listdir(self):
        """Test os.listdir mapping."""
        mapping = get_stdlib_mapping("os", "listdir")
        assert mapping is not None
        assert "read_dir" in mapping.rust_code
        assert "std::fs" in mapping.rust_imports

    def test_os_mkdir(self):
        """Test os.mkdir mapping."""
        mapping = get_stdlib_mapping("os", "mkdir")
        assert mapping is not None
        assert "create_dir" in mapping.rust_code

    def test_os_makedirs(self):
        """Test os.makedirs mapping."""
        mapping = get_stdlib_mapping("os", "makedirs")
        assert mapping is not None
        assert "create_dir_all" in mapping.rust_code

    def test_os_remove(self):
        """Test os.remove mapping."""
        mapping = get_stdlib_mapping("os", "remove")
        assert mapping is not None
        assert "remove_file" in mapping.rust_code

    def test_os_rmdir(self):
        """Test os.rmdir mapping."""
        mapping = get_stdlib_mapping("os", "rmdir")
        assert mapping is not None
        assert "remove_dir" in mapping.rust_code

    def test_os_rename(self):
        """Test os.rename mapping."""
        mapping = get_stdlib_mapping("os", "rename")
        assert mapping is not None
        assert "rename" in mapping.rust_code

    def test_os_getenv(self):
        """Test os.getenv mapping."""
        mapping = get_stdlib_mapping("os", "getenv")
        assert mapping is not None
        assert "env::var" in mapping.rust_code


class TestOSPathMappings:
    """Tests for os.path module mappings."""

    def test_os_path_exists(self):
        """Test os.path.exists mapping."""
        mapping = get_stdlib_mapping("os.path", "exists")
        assert mapping is not None
        assert "Path::new" in mapping.rust_code
        assert ".exists()" in mapping.rust_code

    def test_os_path_isfile(self):
        """Test os.path.isfile mapping."""
        mapping = get_stdlib_mapping("os.path", "isfile")
        assert mapping is not None
        assert ".is_file()" in mapping.rust_code

    def test_os_path_isdir(self):
        """Test os.path.isdir mapping."""
        mapping = get_stdlib_mapping("os.path", "isdir")
        assert mapping is not None
        assert ".is_dir()" in mapping.rust_code

    def test_os_path_join(self):
        """Test os.path.join mapping."""
        mapping = get_stdlib_mapping("os.path", "join")
        assert mapping is not None
        assert ".join(" in mapping.rust_code

    def test_os_path_basename(self):
        """Test os.path.basename mapping."""
        mapping = get_stdlib_mapping("os.path", "basename")
        assert mapping is not None
        assert "file_name()" in mapping.rust_code

    def test_os_path_dirname(self):
        """Test os.path.dirname mapping."""
        mapping = get_stdlib_mapping("os.path", "dirname")
        assert mapping is not None
        assert "parent()" in mapping.rust_code


class TestSysMappings:
    """Tests for sys module mappings."""

    def test_sys_argv(self):
        """Test sys.argv mapping."""
        mapping = get_stdlib_mapping("sys", "argv")
        assert mapping is not None
        assert "args()" in mapping.rust_code
        # Uses fully qualified path, no import needed
        assert "std::env::args" in mapping.rust_code

    def test_sys_exit(self):
        """Test sys.exit mapping."""
        mapping = get_stdlib_mapping("sys", "exit")
        assert mapping is not None
        assert "process::exit" in mapping.rust_code

    def test_sys_platform(self):
        """Test sys.platform mapping."""
        mapping = get_stdlib_mapping("sys", "platform")
        assert mapping is not None
        assert "consts::OS" in mapping.rust_code

    def test_sys_stdin(self):
        """Test sys.stdin mapping."""
        mapping = get_stdlib_mapping("sys", "stdin")
        assert mapping is not None
        assert "stdin()" in mapping.rust_code

    def test_sys_stdout(self):
        """Test sys.stdout mapping."""
        mapping = get_stdlib_mapping("sys", "stdout")
        assert mapping is not None
        assert "stdout()" in mapping.rust_code

    def test_sys_stderr(self):
        """Test sys.stderr mapping."""
        mapping = get_stdlib_mapping("sys", "stderr")
        assert mapping is not None
        assert "stderr()" in mapping.rust_code


class TestPathlibMappings:
    """Tests for pathlib.Path mappings."""

    def test_path_constructor(self):
        """Test Path constructor mapping."""
        mapping = get_pathlib_mapping("Path")
        assert mapping is not None
        assert "PathBuf::from" in mapping.rust_code

    def test_path_read_text(self):
        """Test Path.read_text mapping."""
        mapping = get_pathlib_mapping("Path.read_text")
        assert mapping is not None
        assert "read_to_string" in mapping.rust_code

    def test_path_read_bytes(self):
        """Test Path.read_bytes mapping."""
        mapping = get_pathlib_mapping("Path.read_bytes")
        assert mapping is not None
        assert "fs::read" in mapping.rust_code

    def test_path_write_text(self):
        """Test Path.write_text mapping."""
        mapping = get_pathlib_mapping("Path.write_text")
        assert mapping is not None
        assert "fs::write" in mapping.rust_code

    def test_path_exists(self):
        """Test Path.exists mapping."""
        mapping = get_pathlib_mapping("Path.exists")
        assert mapping is not None
        assert ".exists()" in mapping.rust_code

    def test_path_is_file(self):
        """Test Path.is_file mapping."""
        mapping = get_pathlib_mapping("Path.is_file")
        assert mapping is not None
        assert ".is_file()" in mapping.rust_code

    def test_path_is_dir(self):
        """Test Path.is_dir mapping."""
        mapping = get_pathlib_mapping("Path.is_dir")
        assert mapping is not None
        assert ".is_dir()" in mapping.rust_code

    def test_path_mkdir(self):
        """Test Path.mkdir mapping."""
        mapping = get_pathlib_mapping("Path.mkdir")
        assert mapping is not None
        assert "create_dir_all" in mapping.rust_code

    def test_path_unlink(self):
        """Test Path.unlink mapping."""
        mapping = get_pathlib_mapping("Path.unlink")
        assert mapping is not None
        assert "remove_file" in mapping.rust_code

    def test_path_parent(self):
        """Test Path.parent mapping."""
        mapping = get_pathlib_mapping("Path.parent")
        assert mapping is not None
        assert ".parent()" in mapping.rust_code

    def test_path_name(self):
        """Test Path.name mapping."""
        mapping = get_pathlib_mapping("Path.name")
        assert mapping is not None
        assert "file_name()" in mapping.rust_code

    def test_path_stem(self):
        """Test Path.stem mapping."""
        mapping = get_pathlib_mapping("Path.stem")
        assert mapping is not None
        assert "file_stem()" in mapping.rust_code

    def test_path_joinpath(self):
        """Test Path.joinpath mapping."""
        mapping = get_pathlib_mapping("Path.joinpath")
        assert mapping is not None
        assert ".join(" in mapping.rust_code


class TestJsonMappings:
    """Tests for json module mappings."""

    def test_json_loads(self):
        """Test json.loads mapping."""
        mapping = get_json_mapping("json.loads")
        assert mapping is not None
        assert "from_str" in mapping.rust_code
        assert "serde_json" in mapping.rust_imports
        assert mapping.cargo_deps is not None
        assert any("serde_json" in dep for dep in mapping.cargo_deps)

    def test_json_dumps(self):
        """Test json.dumps mapping."""
        mapping = get_json_mapping("json.dumps")
        assert mapping is not None
        assert "to_string" in mapping.rust_code

    def test_json_load(self):
        """Test json.load mapping."""
        mapping = get_json_mapping("json.load")
        assert mapping is not None
        assert "from_reader" in mapping.rust_code

    def test_json_dump(self):
        """Test json.dump mapping."""
        mapping = get_json_mapping("json.dump")
        assert mapping is not None
        assert "to_writer" in mapping.rust_code


class TestCollectionsMappings:
    """Tests for collections module mappings."""

    def test_defaultdict(self):
        """Test collections.defaultdict mapping."""
        mapping = get_collections_mapping("collections.defaultdict")
        assert mapping is not None
        assert "HashMap" in mapping.rust_code

    def test_counter(self):
        """Test collections.Counter mapping."""
        mapping = get_collections_mapping("collections.Counter")
        assert mapping is not None
        assert "HashMap" in mapping.rust_code

    def test_deque(self):
        """Test collections.deque mapping."""
        mapping = get_collections_mapping("collections.deque")
        assert mapping is not None
        assert "VecDeque" in mapping.rust_code
        assert "std::collections::VecDeque" in mapping.rust_imports

    def test_ordereddict(self):
        """Test collections.OrderedDict mapping."""
        mapping = get_collections_mapping("collections.OrderedDict")
        assert mapping is not None
        assert "IndexMap" in mapping.rust_code
        assert mapping.cargo_deps is not None
        assert any("indexmap" in dep for dep in mapping.cargo_deps)


class TestLoggingMappings:
    """Tests for logging module mappings."""

    def test_logging_debug(self):
        """Test logging.debug mapping to log::debug! macro."""
        mapping = get_logging_mapping("logging.debug")
        assert mapping is not None
        assert "log::debug!" in mapping.rust_code
        assert mapping.cargo_deps is not None
        assert "log" in mapping.cargo_deps
        assert "env_logger" in mapping.cargo_deps

    def test_logging_info(self):
        """Test logging.info mapping to log::info! macro."""
        mapping = get_logging_mapping("logging.info")
        assert mapping is not None
        assert "log::info!" in mapping.rust_code
        assert mapping.cargo_deps is not None
        assert "log" in mapping.cargo_deps

    def test_logging_warning(self):
        """Test logging.warning mapping to log::warn! macro."""
        mapping = get_logging_mapping("logging.warning")
        assert mapping is not None
        assert "log::warn!" in mapping.rust_code
        # Also test the deprecated 'warn' alias
        warn_mapping = get_logging_mapping("logging.warn")
        assert warn_mapping is not None
        assert "log::warn!" in warn_mapping.rust_code

    def test_logging_error_and_critical(self):
        """Test logging.error and logging.critical mappings."""
        error_mapping = get_logging_mapping("logging.error")
        assert error_mapping is not None
        assert "log::error!" in error_mapping.rust_code

        # Critical maps to error in Rust (no critical level)
        critical_mapping = get_logging_mapping("logging.critical")
        assert critical_mapping is not None
        assert "log::error!" in critical_mapping.rust_code

    def test_logging_basicconfig(self):
        """Test logging.basicConfig mapping to env_logger::init()."""
        mapping = get_logging_mapping("logging.basicConfig")
        assert mapping is not None
        assert "env_logger::init()" in mapping.rust_code
        assert mapping.cargo_deps is not None
        assert "env_logger" in mapping.cargo_deps

    def test_logging_level_constants(self):
        """Test logging level constants mapping to log::LevelFilter."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in levels:
            mapping = get_logging_mapping(f"logging.{level}")
            assert mapping is not None, f"Missing logging.{level}"
            assert "log::LevelFilter::" in mapping.rust_code

    def test_logging_via_get_stdlib_mapping(self):
        """Test logging mappings are accessible via get_stdlib_mapping."""
        mapping = get_stdlib_mapping("logging", "info")
        assert mapping is not None
        assert "log::info!" in mapping.rust_code


class TestMappingCoverage:
    """Tests to ensure all expected mappings exist."""

    def test_os_mappings_count(self):
        """Verify expected number of os mappings."""
        os_funcs = ["getcwd", "chdir", "listdir", "mkdir", "makedirs",
                    "remove", "rmdir", "rename", "getenv"]
        for func in os_funcs:
            assert get_stdlib_mapping("os", func) is not None, f"Missing os.{func}"

    def test_os_path_mappings_count(self):
        """Verify expected number of os.path mappings."""
        path_funcs = ["exists", "isfile", "isdir", "join", "basename", "dirname"]
        for func in path_funcs:
            assert get_stdlib_mapping("os.path", func) is not None, f"Missing os.path.{func}"

    def test_sys_mappings_count(self):
        """Verify expected number of sys mappings."""
        sys_attrs = ["argv", "exit", "platform", "stdin", "stdout", "stderr"]
        for attr in sys_attrs:
            assert get_stdlib_mapping("sys", attr) is not None, f"Missing sys.{attr}"

    def test_logging_mappings_count(self):
        """Verify expected number of logging mappings."""
        log_funcs = ["debug", "info", "warning", "warn", "error", "critical", "exception", "basicConfig"]
        for func in log_funcs:
            assert get_stdlib_mapping("logging", func) is not None, f"Missing logging.{func}"

    def test_nonexistent_mapping_returns_none(self):
        """Test that nonexistent mappings return None."""
        assert get_stdlib_mapping("os", "nonexistent") is None
        assert get_stdlib_mapping("nonexistent", "func") is None
        assert get_pathlib_mapping("nonexistent") is None
        assert get_json_mapping("nonexistent") is None
        assert get_collections_mapping("nonexistent") is None
        assert get_logging_mapping("nonexistent") is None


class TestRustStdFsMappings:
    """Tests for Rust std::fs module mappings."""

    def test_fs_file_type(self):
        """Test std::fs::File type mapping."""
        mapping = get_fs_mapping("rust_std.fs.File")
        assert mapping is not None
        assert "std::fs::File" in mapping.rust_code
        assert "std::fs::File" in mapping.rust_imports

    def test_fs_file_open(self):
        """Test std::fs::File::open mapping."""
        mapping = get_fs_mapping("rust_std.fs.File.open")
        assert mapping is not None
        assert "std::fs::File::open" in mapping.rust_code
        assert "?" in mapping.rust_code  # Error propagation
        assert mapping.needs_result

    def test_fs_file_create(self):
        """Test std::fs::File::create mapping."""
        mapping = get_fs_mapping("rust_std.fs.File.create")
        assert mapping is not None
        assert "std::fs::File::create" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_read_to_string(self):
        """Test std::fs::read_to_string mapping."""
        mapping = get_fs_mapping("rust_std.fs.read_to_string")
        assert mapping is not None
        assert "std::fs::read_to_string" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_write(self):
        """Test std::fs::write mapping."""
        mapping = get_fs_mapping("rust_std.fs.write")
        assert mapping is not None
        assert "std::fs::write" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_copy(self):
        """Test std::fs::copy mapping."""
        mapping = get_fs_mapping("rust_std.fs.copy")
        assert mapping is not None
        assert "std::fs::copy" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_rename(self):
        """Test std::fs::rename mapping."""
        mapping = get_fs_mapping("rust_std.fs.rename")
        assert mapping is not None
        assert "std::fs::rename" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_remove_file(self):
        """Test std::fs::remove_file mapping."""
        mapping = get_fs_mapping("rust_std.fs.remove_file")
        assert mapping is not None
        assert "std::fs::remove_file" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_create_dir(self):
        """Test std::fs::create_dir mapping."""
        mapping = get_fs_mapping("rust_std.fs.create_dir")
        assert mapping is not None
        assert "std::fs::create_dir" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_create_dir_all(self):
        """Test std::fs::create_dir_all mapping."""
        mapping = get_fs_mapping("rust_std.fs.create_dir_all")
        assert mapping is not None
        assert "std::fs::create_dir_all" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_remove_dir(self):
        """Test std::fs::remove_dir mapping."""
        mapping = get_fs_mapping("rust_std.fs.remove_dir")
        assert mapping is not None
        assert "std::fs::remove_dir" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_read_dir(self):
        """Test std::fs::read_dir mapping."""
        mapping = get_fs_mapping("rust_std.fs.read_dir")
        assert mapping is not None
        assert "std::fs::read_dir" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_metadata(self):
        """Test std::fs::metadata mapping."""
        mapping = get_fs_mapping("rust_std.fs.metadata")
        assert mapping is not None
        assert "std::fs::metadata" in mapping.rust_code
        assert mapping.needs_result

    def test_fs_canonicalize(self):
        """Test std::fs::canonicalize mapping."""
        mapping = get_fs_mapping("rust_std.fs.canonicalize")
        assert mapping is not None
        assert "std::fs::canonicalize" in mapping.rust_code
        assert mapping.needs_result


class TestRustStdFsMethodMappings:
    """Tests for Rust std::fs method mappings."""

    def test_open_options_read(self):
        """Test OpenOptions.read method mapping."""
        mapping = get_fs_method_mapping("OpenOptions", "read")
        assert mapping is not None
        assert ".read(" in mapping.rust_code

    def test_open_options_write(self):
        """Test OpenOptions.write method mapping."""
        mapping = get_fs_method_mapping("OpenOptions", "write")
        assert mapping is not None
        assert ".write(" in mapping.rust_code

    def test_open_options_open(self):
        """Test OpenOptions.open method mapping."""
        mapping = get_fs_method_mapping("OpenOptions", "open")
        assert mapping is not None
        assert ".open(" in mapping.rust_code
        assert mapping.needs_result

    def test_file_sync_all(self):
        """Test File.sync_all method mapping."""
        mapping = get_fs_method_mapping("File", "sync_all")
        assert mapping is not None
        assert ".sync_all()" in mapping.rust_code
        assert mapping.needs_result

    def test_metadata_is_file(self):
        """Test Metadata.is_file method mapping."""
        mapping = get_fs_method_mapping("Metadata", "is_file")
        assert mapping is not None
        assert ".is_file()" in mapping.rust_code

    def test_metadata_is_dir(self):
        """Test Metadata.is_dir method mapping."""
        mapping = get_fs_method_mapping("Metadata", "is_dir")
        assert mapping is not None
        assert ".is_dir()" in mapping.rust_code

    def test_metadata_len(self):
        """Test Metadata.len method mapping."""
        mapping = get_fs_method_mapping("Metadata", "len")
        assert mapping is not None
        assert ".len()" in mapping.rust_code

    def test_dir_entry_path(self):
        """Test DirEntry.path method mapping."""
        mapping = get_fs_method_mapping("DirEntry", "path")
        assert mapping is not None
        assert ".path()" in mapping.rust_code


class TestRustStdIoMappings:
    """Tests for Rust std::io module mappings."""

    def test_io_stdin(self):
        """Test std::io::stdin mapping."""
        mapping = get_io_mapping("rust_std.io.stdin")
        assert mapping is not None
        assert "std::io::stdin()" in mapping.rust_code

    def test_io_stdout(self):
        """Test std::io::stdout mapping."""
        mapping = get_io_mapping("rust_std.io.stdout")
        assert mapping is not None
        assert "std::io::stdout()" in mapping.rust_code

    def test_io_stderr(self):
        """Test std::io::stderr mapping."""
        mapping = get_io_mapping("rust_std.io.stderr")
        assert mapping is not None
        assert "std::io::stderr()" in mapping.rust_code

    def test_io_bufreader(self):
        """Test std::io::BufReader mapping."""
        mapping = get_io_mapping("rust_std.io.BufReader")
        assert mapping is not None
        assert "std::io::BufReader::new" in mapping.rust_code
        assert "std::io::BufReader" in mapping.rust_imports

    def test_io_bufwriter(self):
        """Test std::io::BufWriter mapping."""
        mapping = get_io_mapping("rust_std.io.BufWriter")
        assert mapping is not None
        assert "std::io::BufWriter::new" in mapping.rust_code
        assert "std::io::BufWriter" in mapping.rust_imports

    def test_io_cursor(self):
        """Test std::io::Cursor mapping."""
        mapping = get_io_mapping("rust_std.io.Cursor")
        assert mapping is not None
        assert "std::io::Cursor::new" in mapping.rust_code
        assert "std::io::Cursor" in mapping.rust_imports

    def test_io_empty(self):
        """Test std::io::empty mapping."""
        mapping = get_io_mapping("rust_std.io.empty")
        assert mapping is not None
        assert "std::io::empty()" in mapping.rust_code

    def test_io_sink(self):
        """Test std::io::sink mapping."""
        mapping = get_io_mapping("rust_std.io.sink")
        assert mapping is not None
        assert "std::io::sink()" in mapping.rust_code

    def test_io_copy(self):
        """Test std::io::copy mapping."""
        mapping = get_io_mapping("rust_std.io.copy")
        assert mapping is not None
        assert "std::io::copy" in mapping.rust_code
        assert mapping.needs_result


class TestRustStdIoMethodMappings:
    """Tests for Rust std::io trait method mappings."""

    def test_read_trait_read(self):
        """Test Read.read method mapping."""
        mapping = get_io_method_mapping("Read", "read")
        assert mapping is not None
        assert ".read(" in mapping.rust_code
        assert "std::io::Read" in mapping.rust_imports
        assert mapping.needs_result

    def test_read_trait_read_to_end(self):
        """Test Read.read_to_end method mapping."""
        mapping = get_io_method_mapping("Read", "read_to_end")
        assert mapping is not None
        assert ".read_to_end(" in mapping.rust_code
        assert mapping.needs_result

    def test_read_trait_read_to_string(self):
        """Test Read.read_to_string method mapping."""
        mapping = get_io_method_mapping("Read", "read_to_string")
        assert mapping is not None
        assert ".read_to_string(" in mapping.rust_code
        assert mapping.needs_result

    def test_write_trait_write(self):
        """Test Write.write method mapping."""
        mapping = get_io_method_mapping("Write", "write")
        assert mapping is not None
        assert ".write(" in mapping.rust_code
        assert "std::io::Write" in mapping.rust_imports
        assert mapping.needs_result

    def test_write_trait_write_all(self):
        """Test Write.write_all method mapping."""
        mapping = get_io_method_mapping("Write", "write_all")
        assert mapping is not None
        assert ".write_all(" in mapping.rust_code
        assert mapping.needs_result

    def test_write_trait_flush(self):
        """Test Write.flush method mapping."""
        mapping = get_io_method_mapping("Write", "flush")
        assert mapping is not None
        assert ".flush()" in mapping.rust_code
        assert mapping.needs_result

    def test_bufread_read_line(self):
        """Test BufRead.read_line method mapping."""
        mapping = get_io_method_mapping("BufRead", "read_line")
        assert mapping is not None
        assert ".read_line(" in mapping.rust_code
        assert mapping.needs_result

    def test_bufread_lines(self):
        """Test BufRead.lines method mapping."""
        mapping = get_io_method_mapping("BufRead", "lines")
        assert mapping is not None
        assert ".lines()" in mapping.rust_code

    def test_seek_trait_seek(self):
        """Test Seek.seek method mapping."""
        mapping = get_io_method_mapping("Seek", "seek")
        assert mapping is not None
        assert ".seek(" in mapping.rust_code
        assert mapping.needs_result

    def test_seek_trait_rewind(self):
        """Test Seek.rewind method mapping."""
        mapping = get_io_method_mapping("Seek", "rewind")
        assert mapping is not None
        assert ".rewind()" in mapping.rust_code
        assert mapping.needs_result

    def test_cursor_position(self):
        """Test Cursor.position method mapping."""
        mapping = get_io_method_mapping("Cursor", "position")
        assert mapping is not None
        assert ".position()" in mapping.rust_code


class TestRustStdPathMappings:
    """Tests for Rust std::path module mappings."""

    def test_path_constructor(self):
        """Test std::path::Path constructor mapping."""
        mapping = get_path_mapping("rust_std.path.Path")
        assert mapping is not None
        assert "std::path::Path::new" in mapping.rust_code
        assert "std::path::Path" in mapping.rust_imports

    def test_pathbuf_constructor(self):
        """Test std::path::PathBuf constructor mapping."""
        mapping = get_path_mapping("rust_std.path.PathBuf")
        assert mapping is not None
        assert "std::path::PathBuf::from" in mapping.rust_code
        assert "std::path::PathBuf" in mapping.rust_imports

    def test_pathbuf_new(self):
        """Test std::path::PathBuf::new mapping."""
        mapping = get_path_mapping("rust_std.path.PathBuf.new")
        assert mapping is not None
        assert "std::path::PathBuf::new()" in mapping.rust_code


class TestRustStdPathMethodMappings:
    """Tests for Rust std::path method mappings."""

    def test_path_to_str(self):
        """Test Path.to_str method mapping."""
        mapping = get_path_method_mapping("Path", "to_str")
        assert mapping is not None
        assert ".to_str()" in mapping.rust_code

    def test_path_to_string_lossy(self):
        """Test Path.to_string_lossy method mapping."""
        mapping = get_path_method_mapping("Path", "to_string_lossy")
        assert mapping is not None
        assert ".to_string_lossy()" in mapping.rust_code

    def test_path_to_path_buf(self):
        """Test Path.to_path_buf method mapping."""
        mapping = get_path_method_mapping("Path", "to_path_buf")
        assert mapping is not None
        assert ".to_path_buf()" in mapping.rust_code

    def test_path_is_absolute(self):
        """Test Path.is_absolute method mapping."""
        mapping = get_path_method_mapping("Path", "is_absolute")
        assert mapping is not None
        assert ".is_absolute()" in mapping.rust_code

    def test_path_is_relative(self):
        """Test Path.is_relative method mapping."""
        mapping = get_path_method_mapping("Path", "is_relative")
        assert mapping is not None
        assert ".is_relative()" in mapping.rust_code

    def test_path_parent(self):
        """Test Path.parent method mapping."""
        mapping = get_path_method_mapping("Path", "parent")
        assert mapping is not None
        assert ".parent()" in mapping.rust_code

    def test_path_file_name(self):
        """Test Path.file_name method mapping."""
        mapping = get_path_method_mapping("Path", "file_name")
        assert mapping is not None
        assert ".file_name()" in mapping.rust_code

    def test_path_extension(self):
        """Test Path.extension method mapping."""
        mapping = get_path_method_mapping("Path", "extension")
        assert mapping is not None
        assert ".extension()" in mapping.rust_code

    def test_path_join(self):
        """Test Path.join method mapping."""
        mapping = get_path_method_mapping("Path", "join")
        assert mapping is not None
        assert ".join(" in mapping.rust_code

    def test_path_exists(self):
        """Test Path.exists method mapping."""
        mapping = get_path_method_mapping("Path", "exists")
        assert mapping is not None
        assert ".exists()" in mapping.rust_code

    def test_path_is_file(self):
        """Test Path.is_file method mapping."""
        mapping = get_path_method_mapping("Path", "is_file")
        assert mapping is not None
        assert ".is_file()" in mapping.rust_code

    def test_path_is_dir(self):
        """Test Path.is_dir method mapping."""
        mapping = get_path_method_mapping("Path", "is_dir")
        assert mapping is not None
        assert ".is_dir()" in mapping.rust_code

    def test_path_canonicalize(self):
        """Test Path.canonicalize method mapping."""
        mapping = get_path_method_mapping("Path", "canonicalize")
        assert mapping is not None
        assert ".canonicalize()" in mapping.rust_code
        assert mapping.needs_result

    def test_pathbuf_push(self):
        """Test PathBuf.push method mapping."""
        mapping = get_path_method_mapping("PathBuf", "push")
        assert mapping is not None
        assert ".push(" in mapping.rust_code

    def test_pathbuf_pop(self):
        """Test PathBuf.pop method mapping."""
        mapping = get_path_method_mapping("PathBuf", "pop")
        assert mapping is not None
        assert ".pop()" in mapping.rust_code

    def test_pathbuf_set_extension(self):
        """Test PathBuf.set_extension method mapping."""
        mapping = get_path_method_mapping("PathBuf", "set_extension")
        assert mapping is not None
        assert ".set_extension(" in mapping.rust_code


class TestRustStdTypeHelpers:
    """Tests for Rust std type helper functions."""

    def test_get_rust_std_type_fs_file(self):
        """Test getting Python type for std::fs::File."""
        assert get_rust_std_type("std::fs::File") == "File"
        assert get_rust_std_type("fs::File") == "File"

    def test_get_rust_std_type_io_bufreader(self):
        """Test getting Python type for std::io::BufReader."""
        assert get_rust_std_type("std::io::BufReader") == "BufReader"
        assert get_rust_std_type("io::BufReader") == "BufReader"

    def test_get_rust_std_type_path_pathbuf(self):
        """Test getting Python type for std::path::PathBuf."""
        assert get_rust_std_type("std::path::PathBuf") == "PathBuf"
        assert get_rust_std_type("path::PathBuf") == "PathBuf"

    def test_get_rust_std_type_unknown(self):
        """Test unknown type returns None."""
        assert get_rust_std_type("unknown::Type") is None

    def test_is_rust_std_type_known(self):
        """Test is_rust_std_type returns True for known types."""
        assert is_rust_std_type("std::fs::File")
        assert is_rust_std_type("io::BufWriter")
        assert is_rust_std_type("path::Path")

    def test_is_rust_std_type_with_generic(self):
        """Test is_rust_std_type handles generic types."""
        assert is_rust_std_type("BufReader<File>")
        assert is_rust_std_type("std::io::BufReader<std::fs::File>")

    def test_is_rust_std_type_unknown(self):
        """Test is_rust_std_type returns False for unknown types."""
        assert not is_rust_std_type("unknown::Type")
        assert not is_rust_std_type("SomeRandomType")


class TestRustStdViaGetStdlibMapping:
    """Tests for Rust std mappings via get_stdlib_mapping."""

    def test_fs_via_get_stdlib_mapping(self):
        """Test rust_std.fs mappings accessible via get_stdlib_mapping."""
        mapping = get_stdlib_mapping("rust_std.fs", "read_to_string")
        assert mapping is not None
        assert "std::fs::read_to_string" in mapping.rust_code

    def test_io_via_get_stdlib_mapping(self):
        """Test rust_std.io mappings accessible via get_stdlib_mapping."""
        mapping = get_stdlib_mapping("rust_std.io", "stdin")
        assert mapping is not None
        assert "std::io::stdin()" in mapping.rust_code

    def test_path_via_get_stdlib_mapping(self):
        """Test rust_std.path mappings accessible via get_stdlib_mapping."""
        mapping = get_stdlib_mapping("rust_std.path", "PathBuf")
        assert mapping is not None
        assert "std::path::PathBuf" in mapping.rust_code


class TestRustStdMappingCoverage:
    """Tests to ensure comprehensive coverage of Rust std mappings."""

    def test_fs_mappings_count(self):
        """Verify expected number of fs mappings."""
        # Should have File, OpenOptions, and various functions
        assert len(FS_MAPPINGS) >= 20
        fs_funcs = [
            "rust_std.fs.File",
            "rust_std.fs.File.open",
            "rust_std.fs.File.create",
            "rust_std.fs.read_to_string",
            "rust_std.fs.write",
            "rust_std.fs.copy",
            "rust_std.fs.rename",
            "rust_std.fs.remove_file",
            "rust_std.fs.create_dir",
            "rust_std.fs.create_dir_all",
            "rust_std.fs.read_dir",
        ]
        for func in fs_funcs:
            assert func in FS_MAPPINGS, f"Missing {func}"

    def test_io_mappings_count(self):
        """Verify expected number of io mappings."""
        assert len(IO_MAPPINGS) >= 10
        io_funcs = [
            "rust_std.io.stdin",
            "rust_std.io.stdout",
            "rust_std.io.stderr",
            "rust_std.io.BufReader",
            "rust_std.io.BufWriter",
            "rust_std.io.Cursor",
        ]
        for func in io_funcs:
            assert func in IO_MAPPINGS, f"Missing {func}"

    def test_path_mappings_count(self):
        """Verify expected number of path mappings."""
        assert len(PATH_MAPPINGS) >= 4
        path_funcs = [
            "rust_std.path.Path",
            "rust_std.path.PathBuf",
            "rust_std.path.PathBuf.new",
            "rust_std.path.PathBuf.from",
        ]
        for func in path_funcs:
            assert func in PATH_MAPPINGS, f"Missing {func}"
