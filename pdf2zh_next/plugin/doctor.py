from __future__ import annotations

import sys
from typing import List, Tuple

try:
    from importlib.metadata import Distribution, distributions, EntryPoint
except Exception:  # pragma: no cover
    from importlib_metadata import Distribution, distributions, EntryPoint  # type: ignore

from pdf2zh_next.plugin.loader import ENTRYPOINT_GROUP, PluginLoader


def _discover_plugins() -> List[Tuple[EntryPoint, Distribution]]:
    # Reuse loader's public discovery API to avoid drift
    loader = PluginLoader()
    return loader.discover_entry_points()


def doctor() -> int:
    loader = PluginLoader()
    eps = _discover_plugins()
    if not eps:
        print("No plugin entry points found.")
        return 0

    print(f"Discovered plugin entry points (group: {ENTRYPOINT_GROUP}):")
    print()
    all_ok = True
    for ep, dist in eps:
        name = dist.metadata.get("Name", "<unknown>")
        version = dist.version or "<unknown>"
        ok, warnings = loader.precheck_distribution(dist)
        status = "OK" if ok else "UNMET"
        print(f"- {ep.name:20s} from {name}=={version}: {status}")
        if not ok:
            all_ok = False
            for msg in warnings:
                print(f"    • {msg}")
    print()
    if all_ok:
        print("All plugins satisfy their requirements.")
        return 0
    else:
        print("Some plugins have unmet requirements. See suggestions above.")
        return 1


def cli() -> None:
    sys.exit(doctor())
