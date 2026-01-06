"""Tests for stdlib mappings."""

import pytest

from spicycrab.codegen.stdlib import (
    get_stdlib_mapping,
    get_os_mapping,
    get_pathlib_mapping,
    get_sys_mapping,
    get_json_mapping,
    get_collections_mapping,
    OS_MAPPINGS,
    SYS_MAPPINGS,
    PATHLIB_MAPPINGS,
    JSON_MAPPINGS,
    COLLECTIONS_MAPPINGS,
)


class TestOSMappings:
    """Tests for os module mappings."""

    def test_os_getcwd(self):
        """Test os.getcwd mapping."""
        mapping = get_stdlib_mapping("os", "getcwd")
        assert mapping is not None
        assert "current_dir" in mapping.rust_code
        assert "std::env" in mapping.rust_imports

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
        assert "std::env" in mapping.rust_imports

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

    def test_nonexistent_mapping_returns_none(self):
        """Test that nonexistent mappings return None."""
        assert get_stdlib_mapping("os", "nonexistent") is None
        assert get_stdlib_mapping("nonexistent", "func") is None
        assert get_pathlib_mapping("nonexistent") is None
        assert get_json_mapping("nonexistent") is None
        assert get_collections_mapping("nonexistent") is None
