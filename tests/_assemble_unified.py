"""
Test assembler for the unified battery-optimiser module.

Concatenates the four pure fragments from
``static/python_scripts/src/unified/`` in numeric order (10_helpers,
20_dp, 30_events, 40_api) and compiles+execs them into a fresh
module-like namespace that test files can import from.

Usage::

    from tests._assemble_unified import UNIFIED
    UNIFIED.compute_unified_schedule(...)
    UNIFIED._solve_dp(...)
"""

import pathlib
import types

_cache = None


def load_unified_module():
    """Return the assembled unified module, cached after first call."""
    global _cache
    if _cache is not None:
        return _cache

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    fragments_dir = repo_root / "static" / "python_scripts" / "src" / "unified"

    # Explicit order — these are the four pure fragments, all < 90.
    # 90_glue.py is deliberately excluded (HA-specific; cannot run in pytest).
    fragment_names = [
        "10_helpers.py",
        "20_dp.py",
        "30_events.py",
        "40_api.py",
    ]

    parts = []
    for name in fragment_names:
        path = fragments_dir / name
        parts.append(path.read_text(encoding="utf-8"))

    src = "\n".join(parts)

    module = types.ModuleType("unified")
    module.__file__ = "<unified-assembled>"
    exec(compile(src, "<unified-assembled>", "exec"), module.__dict__)

    _cache = module
    return module


# Module-level singleton so repeated imports are cheap
UNIFIED = load_unified_module()
