"""Mappings for Python random module to Rust rand crate."""

from __future__ import annotations

from spicycrab.codegen.stdlib.types import StdlibMapping

# random module mappings
# Note: We don't use `use rand;` because we use fully qualified paths like `rand::random()`
# This avoids clippy::single_component_path_imports warning
RANDOM_MAPPINGS: dict[str, StdlibMapping] = {
    # random.random() -> random float in [0.0, 1.0)
    "random.random": StdlibMapping(
        python_module="random",
        python_func="random",
        rust_code="rand::random::<f64>()",
        rust_imports=[],  # Using fully qualified path
        needs_result=False,
    ),
    # random.randint(a, b) -> random integer in [a, b] (inclusive)
    "random.randint": StdlibMapping(
        python_module="random",
        python_func="randint",
        rust_code="rand::thread_rng().gen_range({arg0}..={arg1})",
        rust_imports=["rand::Rng"],  # Need Rng trait for gen_range
        needs_result=False,
    ),
    # random.randrange(stop) or random.randrange(start, stop) -> random int in range
    "random.randrange": StdlibMapping(
        python_module="random",
        python_func="randrange",
        rust_code="rand::thread_rng().gen_range({arg0}..{arg1})",
        rust_imports=["rand::Rng"],
        needs_result=False,
    ),
    # random.uniform(a, b) -> random float in [a, b]
    "random.uniform": StdlibMapping(
        python_module="random",
        python_func="uniform",
        rust_code="rand::thread_rng().gen_range({arg0}..={arg1})",
        rust_imports=["rand::Rng"],
        needs_result=False,
    ),
    # random.choice(seq) -> random element from sequence
    "random.choice": StdlibMapping(
        python_module="random",
        python_func="choice",
        rust_code="{args}.choose(&mut rand::thread_rng()).cloned().unwrap()",
        rust_imports=["rand::seq::SliceRandom"],
        needs_result=False,
    ),
    # random.shuffle(seq) -> shuffle sequence in place
    "random.shuffle": StdlibMapping(
        python_module="random",
        python_func="shuffle",
        rust_code="{args}.shuffle(&mut rand::thread_rng())",
        rust_imports=["rand::seq::SliceRandom"],
        needs_result=False,
    ),
    # random.sample(seq, k) -> k unique random elements
    "random.sample": StdlibMapping(
        python_module="random",
        python_func="sample",
        rust_code="{arg0}.choose_multiple(&mut rand::thread_rng(), {arg1}).cloned().collect::<Vec<_>>()",
        rust_imports=["rand::seq::SliceRandom"],
        needs_result=False,
    ),
    # random.choices(seq, k=n) -> k random elements with replacement
    "random.choices": StdlibMapping(
        python_module="random",
        python_func="choices",
        rust_code="(0..{arg1}).map(|_| {arg0}.choose(&mut rand::thread_rng()).cloned().unwrap()).collect::<Vec<_>>()",
        rust_imports=["rand::seq::SliceRandom"],
        needs_result=False,
    ),
    # random.gauss(mu, sigma) -> gaussian distribution
    "random.gauss": StdlibMapping(
        python_module="random",
        python_func="gauss",
        rust_code=(
            "{{ use rand_distr::{{Distribution, Normal}}; "
            "Normal::new({arg0}, {arg1}).unwrap().sample(&mut rand::thread_rng()) }}"
        ),
        rust_imports=[],  # Inline use statement in block
        needs_result=False,
    ),
    # random.seed(n) -> seed the RNG (note: thread_rng can't be seeded, use StdRng for reproducibility)
    # This is a simplified version that doesn't actually seed thread_rng
    "random.seed": StdlibMapping(
        python_module="random",
        python_func="seed",
        rust_code="/* random.seed() - thread_rng cannot be seeded; use StdRng::seed_from_u64() for reproducibility */",
        rust_imports=[],
        needs_result=False,
    ),
}


def get_random_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a random module function."""
    return RANDOM_MAPPINGS.get(func_name)
