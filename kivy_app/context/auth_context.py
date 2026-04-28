"""
AuthContext: handles login, signup, logout, and session persistence.
Mirrors the React AuthContext + api.js login/signup/token logic.
"""

import os
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API = f"{BACKEND_URL}/api"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", ".session_token")


class AuthContext:
    def __init__(self):
        self.user = None
        self.token = None
        self.loading = True

    # ── helpers ──────────────────────────────────────────────────────────────

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _save_token(self, token):
        try:
            with open(TOKEN_FILE, "w") as f:
                f.write(token)
        except OSError:
            pass

    def _load_token(self):
        try:
            with open(TOKEN_FILE) as f:
                return f.read().strip()
        except OSError:
            return None

    def _delete_token(self):
        try:
            os.remove(TOKEN_FILE)
        except OSError:
            pass

    # ── public API ───────────────────────────────────────────────────────────

    def restore_session(self):
        """Called at startup. Returns True if a valid saved session exists."""
        token = self._load_token()
        if not token:
            self.loading = False
            return False
        try:
            resp = requests.get(
                f"{API}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            if resp.status_code == 200:
                self.token = token
                self.user = resp.json()
                self.loading = False
                return True
        except Exception:
            pass
        self.loading = False
        return False

    def login(self, email, password):
        """Synchronous login. Raises on failure."""
        resp = requests.post(
            f"{API}/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        self.user = data["user"]
        self._save_token(self.token)

    def signup(self, username, email, password):
        """Synchronous signup. Raises on failure."""
        resp = requests.post(
            f"{API}/auth/signup",
            json={"username": username, "email": email, "password": password},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data["access_token"]
        self.user = data["user"]
        self._save_token(self.token)

    def logout(self):
        self.token = None
        self.user = None
        self._delete_token()

    def update_profile(self, username=None, avatar_url=None):
        payload = {}
        if username is not None:
            payload["username"] = username
        if avatar_url is not None:
            payload["avatar_url"] = avatar_url
        resp = requests.patch(
            f"{API}/auth/profile",
            json=payload,
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        self.user = resp.json()
        return self.user

    def delete_account(self, password):
        resp = requests.request(
            "DELETE",
            f"{API}/auth/account",
            json={"password": password},
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        self.logout()
        return resp.json()

    # ── task API ─────────────────────────────────────────────────────────────

    def get_tasks(self):
        resp = requests.get(f"{API}/tasks", headers=self._auth_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def create_task(self, task_data):
        resp = requests.post(
            f"{API}/tasks", json=task_data, headers=self._auth_headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def update_task(self, task_id, task_data):
        resp = requests.put(
            f"{API}/tasks/{task_id}",
            json=task_data,
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def complete_task(self, task_id):
        resp = requests.patch(
            f"{API}/tasks/{task_id}/complete",
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def delete_task(self, task_id):
        resp = requests.delete(
            f"{API}/tasks/{task_id}", headers=self._auth_headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    # ── stats API ────────────────────────────────────────────────────────────

    def get_stats(self):
        resp = requests.get(f"{API}/stats", headers=self._auth_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    # ── friends API ──────────────────────────────────────────────────────────

    def get_friends(self):
        resp = requests.get(f"{API}/friends", headers=self._auth_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_friend_requests(self):
        resp = requests.get(
            f"{API}/friends/requests", headers=self._auth_headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def send_friend_request(self, friend_email):
        resp = requests.post(
            f"{API}/friends/request",
            json={"friend_email": friend_email},
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def accept_friend_request(self, friendship_id):
        resp = requests.patch(
            f"{API}/friends/{friendship_id}/accept",
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def get_friend_garden(self, friend_email):
        resp = requests.get(
            f"{API}/friends/{friend_email}/garden",
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    # ── family API ───────────────────────────────────────────────────────────

    def get_family_groups(self):
        resp = requests.get(
            f"{API}/family/groups", headers=self._auth_headers(), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def create_family_group(self, group_data):
        resp = requests.post(
            f"{API}/family/groups",
            json=group_data,
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def assign_group_task(self, group_id, task_data):
        resp = requests.post(
            f"{API}/family/groups/{group_id}/tasks",
            json=task_data,
            headers=self._auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
