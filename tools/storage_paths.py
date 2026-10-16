"""Shared companion selection; import has no account or directory writes."""
from functools import lru_cache
from pathlib import Path
import os

SOURCE = Path(__file__).resolve().parents[1]
TOOL = "telegram-history-export"

@lru_cache(maxsize=None)
def _resolver():
    try:
        from fleet_guards.runtime import companion_resolver
    except ImportError as exc:
        raise RuntimeError('fleet_guards is not installed; run: pip install -e "$(git config --get fleet.guards)"') from exc
    return companion_resolver(source_root=SOURCE)

def config_root():
    stem = TOOL.upper().replace("-", "_")
    selected = os.environ.get(stem + "_CONFIG") or os.environ.get(stem + "_CONFIG_DIR")
    if selected:
        candidate = Path(selected).expanduser()
        if not candidate.is_absolute():
            raise ValueError("Configuration override must be an absolute directory")
        root = candidate.resolve()
    else:
        root = _resolver().resolve_companion_root(TOOL)
        root = Path(root).resolve() if root else SOURCE.with_name(TOOL + "-config")
    if root == SOURCE or root.is_relative_to(SOURCE):
        raise ValueError("Configuration cannot be inside the tool source repository")
    return root

def writable_config_root():
    root = config_root()
    if not root.is_dir():
        raise RuntimeError("Private companion missing; restore its Git checkout before writing")
    return root
