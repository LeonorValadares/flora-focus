"""
Flora Focus — Backend (SQLite edition)
=======================================
Zero external database required. All data is stored in a single file
called  flora_focus.db  created automatically next to this script.

Install dependencies once, then run:
    python server.py
"""

import os
import sqlite3
import uuid
import logging
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr
from starlette.middleware.cors import CORSMiddleware

# ── Config ────────────────────────────────────────────────────────────────────

ROOT_DIR = Path(__file__).parent
FLORA_ENV = os.environ.get("FLORA_ENV", "development").lower()
DEFAULT_SECRET_KEY = "flora-focus-dev-secret-change-me"
DB_ENV_PATH = os.environ.get("FLORA_DB_PATH")
if DB_ENV_PATH:
    DB_PATH = Path(DB_ENV_PATH)
    if not DB_PATH.is_absolute():
        DB_PATH = ROOT_DIR / DB_PATH
else:
    DB_PATH = ROOT_DIR / "flora_focus.db"
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", DEFAULT_SECRET_KEY)
ALGORITHM = "HS256"
TOKEN_DAYS = 30
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security    = HTTPBearer()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

if FLORA_ENV == "production" and SECRET_KEY == DEFAULT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY must be set in production.")


def allowed_origins():
    raw = os.environ.get("ALLOWED_ORIGINS", "").strip()
    if not raw:
        return DEFAULT_ALLOWED_ORIGINS
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

# ── Database ──────────────────────────────────────────────────────────────────

@contextmanager
def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            email         TEXT PRIMARY KEY,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar_url    TEXT,
            created_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id                     TEXT PRIMARY KEY,
            user_id                TEXT NOT NULL,
            title                  TEXT NOT NULL,
            description            TEXT,
            category               TEXT NOT NULL DEFAULT 'general',
            priority               TEXT NOT NULL DEFAULT 'medium',
            deadline               TEXT NOT NULL,
            time_remaining_seconds INTEGER NOT NULL,
            status                 TEXT NOT NULL DEFAULT 'active',
            created_at             TEXT NOT NULL,
            group_id               TEXT,
            assigned_by            TEXT
        );

        CREATE TABLE IF NOT EXISTS friendships (
            id           TEXT PRIMARY KEY,
            user_email   TEXT NOT NULL,
            friend_email TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'pending',
            created_at   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS family_groups (
            id         TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS family_members (
            group_id TEXT NOT NULL,
            user_id  TEXT NOT NULL,
            username TEXT NOT NULL,
            email    TEXT NOT NULL,
            role     TEXT NOT NULL DEFAULT 'member',
            PRIMARY KEY (group_id, user_id)
        );
        """)
    log.info("Database ready: %s", DB_PATH)

# ── Models ────────────────────────────────────────────────────────────────────

class UserSignup(BaseModel):
    username: str
    email:    EmailStr
    password: str

class UserLogin(BaseModel):
    email:    EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    username:   str
    email:      str
    avatar_url: Optional[str] = None
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type:   str
    user:         UserResponse

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None

class DeleteAccountRequest(BaseModel):
    password: str

class TaskCreate(BaseModel):
    title:                  str
    description:            Optional[str] = None
    category:               Optional[str] = "general"
    priority:               Optional[str] = "medium"
    deadline:               str
    time_remaining_seconds: int

class TaskUpdate(BaseModel):
    title:                  Optional[str] = None
    description:            Optional[str] = None
    category:               Optional[str] = None
    priority:               Optional[str] = None
    deadline:               Optional[str] = None
    time_remaining_seconds: Optional[int] = None
    status:                 Optional[str] = None

class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id:                     str
    user_id:                str
    title:                  str
    description:            Optional[str] = None
    category:               str
    priority:               str
    deadline:               str
    time_remaining_seconds: int
    status:                 str
    created_at:             str

class FriendRequest(BaseModel):
    friend_email: str

class FamilyGroupCreate(BaseModel):
    name:          str
    member_emails: List[str]

class FamilyMember(BaseModel):
    user_id:  str
    username: str
    email:    str
    role:     str

class FamilyGroupResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id:         str
    name:       str
    members:    List[FamilyMember]
    created_by: str
    created_at: str

class GroupTaskCreate(BaseModel):
    group_id:               str
    assigned_to_email:      str
    title:                  str
    description:            Optional[str] = None
    category:               Optional[str] = "general"
    priority:               Optional[str] = "medium"
    deadline:               str
    time_remaining_seconds: int

class StatsResponse(BaseModel):
    total_tasks:     int
    completed_tasks: int
    active_tasks:    int
    expired_tasks:   int
    completion_rate: float
    total_flowers:   int
    wilted_flowers:  int

# ── Auth helpers ──────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def make_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=TOKEN_DAYS)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    exc = HTTPException(status_code=401, detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise exc
    except JWTError:
        raise exc
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not row:
        raise exc
    return dict(row)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _cleanup_empty_groups(conn):
    empty_groups = conn.execute(
        "SELECT fg.id FROM family_groups fg "
        "LEFT JOIN family_members fm ON fg.id = fm.group_id "
        "GROUP BY fg.id HAVING COUNT(fm.user_id)=0"
    ).fetchall()
    for row in empty_groups:
        gid = row["id"]
        conn.execute("DELETE FROM tasks WHERE group_id=?", (gid,))
        conn.execute("DELETE FROM family_groups WHERE id=?", (gid,))

# ── App ───────────────────────────────────────────────────────────────────────

app        = FastAPI(title="Flora Focus API")
api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_router.get("/health")
def healthcheck():
    return {"status": "ok"}

# ── Auth endpoints ────────────────────────────────────────────────────────────

@api_router.post("/auth/signup", response_model=Token)
def signup(data: UserSignup):
    with db_conn() as conn:
        if conn.execute("SELECT 1 FROM users WHERE email=?", (data.email,)).fetchone():
            raise HTTPException(400, "Email already registered")
        if conn.execute("SELECT 1 FROM users WHERE username=?", (data.username,)).fetchone():
            raise HTTPException(400, "Username already taken")
        created = now_iso()
        conn.execute(
            "INSERT INTO users (email,username,password_hash,avatar_url,created_at) VALUES (?,?,?,?,?)",
            (data.email, data.username, hash_password(data.password), None, created),
        )
    user = UserResponse(username=data.username, email=data.email,
                        avatar_url=None, created_at=created)
    return Token(access_token=make_token(data.email), token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
def login(data: UserLogin):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (data.email,)).fetchone()
    if not row or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    return Token(access_token=make_token(data.email), token_type="bearer",
                 user=UserResponse(**dict(row)))

@api_router.get("/auth/me", response_model=UserResponse)
def get_me(cu: dict = Depends(get_current_user)):
    return UserResponse(**cu)

@api_router.patch("/auth/profile", response_model=UserResponse)
def update_profile(data: ProfileUpdate, cu: dict = Depends(get_current_user)):
    updates = {}
    if data.username is not None:
        updates["username"] = data.username.strip()
    if data.avatar_url is not None:
        updates["avatar_url"] = data.avatar_url.strip() or None
    if not updates:
        return UserResponse(**cu)

    with db_conn() as conn:
        if "username" in updates:
            if not updates["username"]:
                raise HTTPException(400, "Username cannot be empty")
            existing = conn.execute(
                "SELECT 1 FROM users WHERE username=? AND email<>?",
                (updates["username"], cu["email"])
            ).fetchone()
            if existing:
                raise HTTPException(400, "Username already taken")
        sets = ", ".join(f"{field}=?" for field in updates)
        conn.execute(
            f"UPDATE users SET {sets} WHERE email=?",
            list(updates.values()) + [cu["email"]],
        )
        if "username" in updates:
            conn.execute(
                "UPDATE family_members SET username=? WHERE user_id=?",
                (updates["username"], cu["email"])
            )
        row = conn.execute("SELECT * FROM users WHERE email=?", (cu["email"],)).fetchone()
    return UserResponse(**dict(row))

@api_router.delete("/auth/account")
def delete_account(data: DeleteAccountRequest, cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=?", (cu["email"],)).fetchone()
        if not row or not verify_password(data.password, row["password_hash"]):
            raise HTTPException(401, "Invalid credentials")
        conn.execute("DELETE FROM tasks WHERE user_id=?", (cu["email"],))
        conn.execute("UPDATE tasks SET assigned_by=NULL WHERE assigned_by=?", (cu["email"],))
        conn.execute("DELETE FROM friendships WHERE user_email=? OR friend_email=?", (cu["email"], cu["email"]))
        conn.execute("DELETE FROM family_members WHERE user_id=?", (cu["email"],))
        _cleanup_empty_groups(conn)
        conn.execute("DELETE FROM users WHERE email=?", (cu["email"],))
    return {"message": "Account deleted"}

# ── Task endpoints ────────────────────────────────────────────────────────────

@api_router.post("/tasks", response_model=TaskResponse)
def create_task(data: TaskCreate, cu: dict = Depends(get_current_user)):
    tid = str(uuid.uuid4())
    with db_conn() as conn:
        conn.execute(
            "INSERT INTO tasks (id,user_id,title,description,category,priority,"
            "deadline,time_remaining_seconds,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (tid, cu["email"], data.title, data.description, data.category,
             data.priority, data.deadline, data.time_remaining_seconds, "active", now_iso()),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    return TaskResponse(**dict(row))

@api_router.get("/tasks", response_model=List[TaskResponse])
def get_tasks(cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id=? ORDER BY created_at DESC",
            (cu["email"],)
        ).fetchall()
    return [TaskResponse(**dict(r)) for r in rows]

@api_router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, data: TaskUpdate, cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        if not conn.execute("SELECT 1 FROM tasks WHERE id=? AND user_id=?",
                            (task_id, cu["email"])).fetchone():
            raise HTTPException(404, "Task not found")
        fields = {k: v for k, v in data.model_dump().items() if v is not None}
        if fields:
            sets = ", ".join(f"{k}=?" for k in fields)
            conn.execute(f"UPDATE tasks SET {sets} WHERE id=?",
                         list(fields.values()) + [task_id])
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return TaskResponse(**dict(row))

@api_router.delete("/tasks/{task_id}")
def delete_task(task_id: str, cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        r = conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?",
                         (task_id, cu["email"]))
    if r.rowcount == 0:
        raise HTTPException(404, "Task not found")
    return {"message": "Task deleted"}

@api_router.patch("/tasks/{task_id}/complete")
def complete_task(task_id: str, cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        r = conn.execute(
            "UPDATE tasks SET status='completed' WHERE id=? AND user_id=?",
            (task_id, cu["email"]))
    if r.rowcount == 0:
        raise HTTPException(404, "Task not found")
    return {"message": "Task completed"}

# ── Friends endpoints ─────────────────────────────────────────────────────────

@api_router.post("/friends/request")
def send_friend_request(req: FriendRequest, cu: dict = Depends(get_current_user)):
    if req.friend_email == cu["email"]:
        raise HTTPException(400, "Cannot add yourself as friend")
    with db_conn() as conn:
        if not conn.execute("SELECT 1 FROM users WHERE email=?",
                            (req.friend_email,)).fetchone():
            raise HTTPException(404, "User not found")
        if conn.execute(
            "SELECT 1 FROM friendships WHERE "
            "(user_email=? AND friend_email=?) OR (user_email=? AND friend_email=?)",
            (cu["email"], req.friend_email, req.friend_email, cu["email"])
        ).fetchone():
            raise HTTPException(400, "Friendship already exists or pending")
        conn.execute(
            "INSERT INTO friendships (id,user_email,friend_email,status,created_at) VALUES (?,?,?,?,?)",
            (str(uuid.uuid4()), cu["email"], req.friend_email, "pending", now_iso())
        )
    return {"message": "Friend request sent"}

@api_router.patch("/friends/{friendship_id}/accept")
def accept_friend_request(friendship_id: str, cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        r = conn.execute(
            "UPDATE friendships SET status='accepted' WHERE id=? AND friend_email=? AND status='pending'",
            (friendship_id, cu["email"]))
    if r.rowcount == 0:
        raise HTTPException(404, "Friend request not found")
    return {"message": "Friend request accepted"}

@api_router.get("/friends")
def get_friends(cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM friendships WHERE (user_email=? OR friend_email=?) AND status='accepted'",
            (cu["email"], cu["email"])
        ).fetchall()
        result = []
        for row in rows:
            other = row["friend_email"] if row["user_email"] == cu["email"] else row["user_email"]
            u = conn.execute("SELECT * FROM users WHERE email=?", (other,)).fetchone()
            if u:
                result.append({"friendship_id": row["id"],
                                "user": UserResponse(**dict(u)).model_dump()})
    return result

@api_router.get("/friends/requests")
def get_friend_requests(cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM friendships WHERE friend_email=? AND status='pending'",
            (cu["email"],)
        ).fetchall()
        result = []
        for row in rows:
            u = conn.execute("SELECT * FROM users WHERE email=?",
                             (row["user_email"],)).fetchone()
            if u:
                result.append({"friendship_id": row["id"],
                                "user": UserResponse(**dict(u)).model_dump(),
                                "created_at": row["created_at"]})
    return result

@api_router.get("/friends/{friend_email}/garden")
def get_friend_garden(friend_email: str, cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        if not conn.execute(
            "SELECT 1 FROM friendships WHERE "
            "((user_email=? AND friend_email=?) OR (user_email=? AND friend_email=?)) "
            "AND status='accepted'",
            (cu["email"], friend_email, friend_email, cu["email"])
        ).fetchone():
            raise HTTPException(403, "Not friends with this user")
        tasks = conn.execute("SELECT * FROM tasks WHERE user_id=?",
                             (friend_email,)).fetchall()
        fu = conn.execute("SELECT * FROM users WHERE email=?",
                          (friend_email,)).fetchone()
    return {
        "user":  UserResponse(**dict(fu)).model_dump() if fu else None,
        "tasks": [TaskResponse(**dict(t)).model_dump() for t in tasks],
    }

# ── Family endpoints ──────────────────────────────────────────────────────────

def _load_group(conn, group_id: str):
    grp = conn.execute("SELECT * FROM family_groups WHERE id=?", (group_id,)).fetchone()
    if not grp:
        return None
    members = conn.execute("SELECT * FROM family_members WHERE group_id=?",
                           (group_id,)).fetchall()
    d = dict(grp)
    d["members"] = [dict(m) for m in members]
    return d

@api_router.post("/family/groups", response_model=FamilyGroupResponse)
def create_family_group(data: FamilyGroupCreate, cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        new_members = []
        for email in data.member_emails:
            u = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            if not u:
                raise HTTPException(404, f"User {email} not found")
            new_members.append(dict(u))

        all_members = [{"user_id": cu["email"], "username": cu["username"],
                        "email": cu["email"], "role": "admin"}]
        for u in new_members:
            all_members.append({"user_id": u["email"], "username": u["username"],
                                 "email": u["email"], "role": "member"})
        if len(all_members) > 8:
            raise HTTPException(400, "Maximum 8 members allowed")

        gid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO family_groups (id,name,created_by,created_at) VALUES (?,?,?,?)",
            (gid, data.name, cu["email"], now_iso()))
        for m in all_members:
            conn.execute(
                "INSERT INTO family_members (group_id,user_id,username,email,role) VALUES (?,?,?,?,?)",
                (gid, m["user_id"], m["username"], m["email"], m["role"]))
        group = _load_group(conn, gid)
    return FamilyGroupResponse(**group)

@api_router.get("/family/groups", response_model=List[FamilyGroupResponse])
def get_family_groups(cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT fg.id FROM family_groups fg "
            "JOIN family_members fm ON fg.id=fm.group_id WHERE fm.user_id=?",
            (cu["email"],)
        ).fetchall()
        groups = [_load_group(conn, r["id"]) for r in rows]
    return [FamilyGroupResponse(**g) for g in groups if g]

@api_router.post("/family/groups/{group_id}/tasks")
def assign_group_task(group_id: str, data: GroupTaskCreate,
                      cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        group = _load_group(conn, group_id)
        if not group:
            raise HTTPException(404, "Group not found")
        me = next((m for m in group["members"] if m["user_id"] == cu["email"]), None)
        if not me or me["role"] != "admin":
            raise HTTPException(403, "Only admins can assign tasks")
        if not next((m for m in group["members"] if m["email"] == data.assigned_to_email), None):
            raise HTTPException(404, "Assigned user not in group")
        tid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO tasks (id,user_id,title,description,category,priority,"
            "deadline,time_remaining_seconds,status,created_at,group_id,assigned_by)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (tid, data.assigned_to_email, f"[{group['name']}] {data.title}",
             data.description, data.category, data.priority, data.deadline,
             data.time_remaining_seconds, "active", now_iso(), group_id, cu["email"]))
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    return {"message": "Task assigned", "task": TaskResponse(**dict(row)).model_dump()}

# ── Stats endpoint ────────────────────────────────────────────────────────────

@api_router.get("/stats", response_model=StatsResponse)
def get_stats(cu: dict = Depends(get_current_user)):
    with db_conn() as conn:
        rows = conn.execute("SELECT status, deadline FROM tasks WHERE user_id=?",
                            (cu["email"],)).fetchall()
    total     = len(rows)
    completed = sum(1 for r in rows if r["status"] == "completed")
    expired   = sum(1 for r in rows if r["status"] != "completed" and _is_expired(r["deadline"]))
    active    = total - completed - expired
    return StatsResponse(
        total_tasks=total, completed_tasks=completed,
        active_tasks=active, expired_tasks=expired,
        completion_rate=round(completed / total * 100, 1) if total else 0.0,
        total_flowers=completed, wilted_flowers=expired,
    )

def _is_expired(deadline: str) -> bool:
    try:
        return datetime.fromisoformat(deadline.replace("Z", "+00:00")) <= datetime.now(timezone.utc)
    except ValueError:
        return False

# ── Start ─────────────────────────────────────────────────────────────────────

app.include_router(api_router)
init_db()

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=host, port=port, reload=False)
