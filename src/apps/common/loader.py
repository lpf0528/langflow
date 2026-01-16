import os


def get_bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name, str(default)).lower() in ("true", "1", "t")
    return val
