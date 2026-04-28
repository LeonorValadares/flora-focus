"""
Flora Focus - Kivy App
A gamified task manager where completing tasks grows a garden.

Requirements:
    pip install kivy requests

Run:
    python main.py
"""

import os
import subprocess
import sys
import time
import ctypes
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_ICON = PROJECT_ROOT / "FloraFocus.png"
KIVY_HOME = PROJECT_ROOT / ".kivy"
KIVY_HOME.mkdir(parents=True, exist_ok=True)
(KIVY_HOME / "logs").mkdir(parents=True, exist_ok=True)

# Must be set BEFORE any other Kivy imports
os.environ.setdefault("KIVY_HOME", str(KIVY_HOME))
os.environ.setdefault("KIVY_LOG_LEVEL", "warning")
if sys.platform == "win32":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "FloraFocus.DesktopApp"
    )

from kivy.config import Config
Config.set("kivy", "window_icon", str(APP_ICON))
Config.set("input", "mouse", "mouse,multitouch_on_demand")
Config.set("graphics", "multisamples", "0")
Config.set("graphics", "position", "custom")
Config.set("graphics", "left", "120")
Config.set("graphics", "top", "60")
Config.set("graphics", "width", "400")
Config.set("graphics", "height", "750")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition, NoTransition
from kivy.core.window import Window
from kivy.clock import Clock

from context.auth_context import AuthContext, BACKEND_URL, using_local_backend
from context.language_context import LanguageContext
from screens.login_screen import LoginScreen
from screens.signup_screen import SignupScreen
from screens.garden_screen import GardenScreen
from screens.stats_screen import StatsScreen
from screens.friends_screen import FriendsScreen
from screens.family_screen import FamilyScreen

# Mobile-style window size
Window.size = (400, 750)
Window.left = 120
Window.top = 60
if APP_ICON.exists():
    Window.set_icon(str(APP_ICON))

BACKEND_DIR = PROJECT_ROOT / "backend"
BACKEND_SERVER = BACKEND_DIR / "server.py"
BACKEND_HEALTH_URL = f"{BACKEND_URL}/api/health"
BACKEND_IMPORT_CHECK = (
    "import fastapi, uvicorn, passlib, jose, pydantic; print('ok')"
)


def _candidate_backend_pythons():
    candidates = []
    env_python = os.environ.get("FLORA_BACKEND_PYTHON")
    if env_python:
        candidates.append(Path(env_python))

    candidates.extend([
        PROJECT_ROOT / "backend_runtime" / "python.exe",
        PROJECT_ROOT / "venv" / "Scripts" / "python.exe",
        Path(sys.executable),
        Path.home() / "AppData" / "Local" / "Python" / "pythoncore-3.14-64" / "python.exe",
        Path.home() / "AppData" / "Local" / "Python" / "pythoncore-3.11-64" / "python.exe",
    ])

    seen = set()
    for candidate in candidates:
        resolved = str(candidate)
        if resolved in seen or not candidate.exists():
            continue
        seen.add(resolved)
        yield resolved


def _backend_python():
    for python_path in _candidate_backend_pythons():
        probe = subprocess.run(
            [python_path, "-c", BACKEND_IMPORT_CHECK],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        if probe.returncode == 0:
            return python_path

    raise RuntimeError(
        "Flora Focus could not find a Python interpreter with the backend dependencies installed."
    )


class BackendManager:
    def __init__(self):
        self.process = None
        self.enabled = using_local_backend()

    def ensure_running(self, timeout=12):
        if not self.enabled:
            return
        if self._is_ready():
            return

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.process = subprocess.Popen(
            [_backend_python(), str(BACKEND_SERVER)],
            cwd=str(BACKEND_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError("Backend stopped during startup")
            if self._is_ready():
                return
            time.sleep(0.2)
        raise RuntimeError("Backend did not become ready in time")

    def stop(self):
        if not self.enabled:
            return
        if not self.process or self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def _is_ready(self):
        try:
            with urlopen(BACKEND_HEALTH_URL, timeout=1):
                return True
        except (URLError, TimeoutError, OSError):
            return False


class FloraFocusApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.backend = BackendManager()

    def build(self):
        self.title = "Flora Focus"
        if APP_ICON.exists():
            self.icon = str(APP_ICON)
        self.backend.ensure_running()

        # Shared contexts
        self.auth = AuthContext()
        self.lang = LanguageContext()

        self.sm = ScreenManager(transition=SlideTransition())

        # Create all screens (passing contexts)
        self.login_screen = LoginScreen(
            name="login", auth=self.auth, lang=self.lang, sm=self.sm
        )
        self.signup_screen = SignupScreen(
            name="signup", auth=self.auth, lang=self.lang, sm=self.sm
        )
        self.garden_screen = GardenScreen(
            name="garden", auth=self.auth, lang=self.lang, sm=self.sm
        )
        self.stats_screen = StatsScreen(
            name="stats", auth=self.auth, lang=self.lang, sm=self.sm
        )
        self.friends_screen = FriendsScreen(
            name="friends", auth=self.auth, lang=self.lang, sm=self.sm
        )
        self.family_screen = FamilyScreen(
            name="family", auth=self.auth, lang=self.lang, sm=self.sm
        )

        for screen in [
            self.login_screen,
            self.signup_screen,
            self.garden_screen,
            self.stats_screen,
            self.friends_screen,
            self.family_screen,
        ]:
            self.sm.add_widget(screen)

        # Restore session or show login
        Clock.schedule_once(self._check_session, 0.1)

        return self.sm

    def _check_session(self, dt):
        if self.auth.restore_session():
            self.sm.transition = NoTransition()
            self.sm.current = "garden"
            self.sm.transition = SlideTransition()
        else:
            self.sm.current = "login"

    def refresh_language(self):
        current = self.sm.current
        for screen in self.sm.screens:
            if hasattr(screen, "refresh_language"):
                screen.refresh_language()
        self.sm.current = current

    def on_stop(self):
        self.backend.stop()


if __name__ == "__main__":
    FloraFocusApp().run()
