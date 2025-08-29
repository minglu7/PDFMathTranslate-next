from __future__ import annotations

import sys
from typing import List, Tuple

try:
    from importlib.metadata import Distribution, distributions, EntryPoint
except Exception:  # pragma: no cover
    from importlib_metadata import Distribution, distributions, EntryPoint  # type: ignore

from pdf2zh_next.translator.plugin_loader import ENTRYPOINT_GROUP, PluginLoader


def _discover_plugins() -> List[Tuple[EntryPoint, Distribution]]:
    items: List[Tuple[EntryPoint, Distribution]] = []
    for dist in distributions():
        try:
            for ep in getattr(dist, "entry_points", []):
                if getattr(ep, "group", None) == ENTRYPOINT_GROUP:
                    items.append((ep, dist))
        except Exception:
            continue
    return items


def doctor() -> int:
    loader = PluginLoader()
    eps = _discover_plugins()
    if not eps:
        print("No plugin entry points found.")
        return 0

    print("Discovered plugin entry points (group: pdf2zh_next.translators):")
    print()
    all_ok = True
    for ep, dist in eps:
        name = dist.metadata.get("Name", "<unknown>")
        version = dist.version or "<unknown>"
        ok, warnings = loader._precheck_distribution(dist)  # type: ignore[attr-defined]
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

