"""Mappings for Python collections module to Rust std::collections."""

from __future__ import annotations

from spicycrab.codegen.stdlib.types import StdlibMapping

# collections module mappings
COLLECTIONS_MAPPINGS: dict[str, StdlibMapping] = {
    "collections.defaultdict": StdlibMapping(
        python_module="collections",
        python_func="defaultdict",
        rust_code="HashMap::new()",  # Use .entry().or_default() pattern
        rust_imports=["std::collections::HashMap"],
    ),
    "collections.Counter": StdlibMapping(
        python_module="collections",
        python_func="Counter",
        rust_code="HashMap::new()",  # Count with .entry().or_insert(0) += 1
        rust_imports=["std::collections::HashMap"],
    ),
    "collections.deque": StdlibMapping(
        python_module="collections",
        python_func="deque",
        rust_code="VecDeque::new()",
        rust_imports=["std::collections::VecDeque"],
    ),
    "collections.OrderedDict": StdlibMapping(
        python_module="collections",
        python_func="OrderedDict",
        rust_code="IndexMap::new()",
        rust_imports=["indexmap::IndexMap"],
        cargo_deps=['indexmap = "2.0"'],
    ),
    "collections.namedtuple": StdlibMapping(
        python_module="collections",
        python_func="namedtuple",
        rust_code="/* namedtuple -> use struct */",
        rust_imports=[],
    ),
}

# deque method mappings
DEQUE_METHOD_MAPPINGS: dict[str, str] = {
    "append": "push_back",
    "appendleft": "push_front",
    "pop": "pop_back",
    "popleft": "pop_front",
    "extend": "extend",
    "extendleft": "extend",  # Note: reverses order in Python
    "rotate": "rotate_left",  # Needs custom impl for negative
    "clear": "clear",
}

# Counter method mappings (HashMap-based)
COUNTER_METHOD_MAPPINGS: dict[str, str] = {
    "most_common": "/* use .iter().sorted_by() */",
    "elements": "/* use .iter().flat_map() */",
    "update": "/* use .entry().or_insert(0) pattern */",
}


def get_collections_mapping(name: str) -> StdlibMapping | None:
    """Get mapping for a collections type."""
    return COLLECTIONS_MAPPINGS.get(name)


def get_deque_method(method: str) -> str | None:
    """Get Rust VecDeque method for deque method."""
    return DEQUE_METHOD_MAPPINGS.get(method)
