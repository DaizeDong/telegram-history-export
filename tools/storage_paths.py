"""Shared companion selection; import has no account or directory writes."""
from functools import lru_cache
from pathlib import Path

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
    root = _resolver().resolve_companion_root(TOOL)
    if root is None:
        raise RuntimeError("Private companion missing; clone %s-config beside this repo or set %s_CONFIG"
                           % (TOOL, TOOL.upper().replace("-", "_")))
    return Path(root).resolve()

def writable_config_root():
    root = config_root()
    if not root.is_dir():
        raise RuntimeError("Private companion missing; restore its Git checkout before writing")
    return root
