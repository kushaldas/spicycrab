"""Mappings for Python subprocess module to Rust std::process."""

from __future__ import annotations

from spicycrab.codegen.stdlib.types import StdlibMapping

# subprocess module mappings
SUBPROCESS_MAPPINGS: dict[str, StdlibMapping] = {
    # subprocess.run(args) -> run command and return CompletedProcess
    # Simplified: returns exit status as i64
    "subprocess.run": StdlibMapping(
        python_module="subprocess",
        python_func="run",
        rust_code="std::process::Command::new({arg0}).args(&{arg1}).status().unwrap().code().unwrap_or(-1) as i64",
        rust_imports=[],
        needs_result=False,
    ),
    # subprocess.call(args) -> run command and return exit code
    "subprocess.call": StdlibMapping(
        python_module="subprocess",
        python_func="call",
        rust_code="std::process::Command::new({arg0}).args(&{arg1}).status().unwrap().code().unwrap_or(-1) as i64",
        rust_imports=[],
        needs_result=False,
    ),
    # subprocess.check_call(args) -> run command, raise on non-zero exit
    "subprocess.check_call": StdlibMapping(
        python_module="subprocess",
        python_func="check_call",
        rust_code=(
            "{{ let s = std::process::Command::new({arg0}).args(&{arg1}).status().unwrap(); "
            'if !s.success() {{ panic!("Command failed"); }} s.code().unwrap_or(0) as i64 }}'
        ),
        rust_imports=[],
        needs_result=False,
    ),
    # subprocess.check_output(args) -> run command and return stdout
    "subprocess.check_output": StdlibMapping(
        python_module="subprocess",
        python_func="check_output",
        rust_code="String::from_utf8_lossy(&std::process::Command::new({arg0}).args(&{arg1}).output().unwrap().stdout).to_string()",
        rust_imports=[],
        needs_result=False,
    ),
    # subprocess.getoutput(cmd) -> run shell command and return output
    "subprocess.getoutput": StdlibMapping(
        python_module="subprocess",
        python_func="getoutput",
        rust_code='String::from_utf8_lossy(&std::process::Command::new("sh").arg("-c").arg({args}).output().unwrap().stdout).to_string()',
        rust_imports=[],
        needs_result=False,
    ),
    # subprocess.getstatusoutput(cmd) -> run shell command, return (status, output)
    "subprocess.getstatusoutput": StdlibMapping(
        python_module="subprocess",
        python_func="getstatusoutput",
        rust_code=(
            '{{ let o = std::process::Command::new("sh").arg("-c").arg({args}).output().unwrap(); '
            "(o.status.code().unwrap_or(-1) as i64, String::from_utf8_lossy(&o.stdout).to_string()) }}"
        ),
        rust_imports=[],
        needs_result=False,
    ),
}


def get_subprocess_mapping(func_name: str) -> StdlibMapping | None:
    """Get mapping for a subprocess module function."""
    return SUBPROCESS_MAPPINGS.get(func_name)
