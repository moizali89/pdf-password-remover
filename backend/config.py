import os
import yaml

DEFAULTS = {
    "server": {"host": "127.0.0.1", "port": 5000, "debug": False},
    "uploads": {"max_file_size_mb": 500, "allowed_extensions": ["pdf"]},
    "behavior": {"passthrough_unencrypted": True, "output_prefix": "unlocked-"},
    "security": {"enable_csp": True},
    "ui": {"min_loader_seconds": 2},
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(path: str = None) -> dict:
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

    cfg = dict(DEFAULTS)
    try:
        with open(path) as f:
            user_cfg = yaml.safe_load(f) or {}
        cfg = _deep_merge(DEFAULTS, user_cfg)
    except FileNotFoundError:
        pass

    return cfg
