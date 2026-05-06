import os
import sys
from pathlib import Path


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    if sys.platform == "win32":
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "FloraFocus",
            Path.home() / ".florafocus",
            app_root() / ".florafocus",
        ]
    else:
        candidates = [Path.home() / ".florafocus", app_root() / ".florafocus"]

    for data_dir in candidates:
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir
        except OSError:
            continue
    raise RuntimeError("Flora Focus could not create a writable user data directory.")
