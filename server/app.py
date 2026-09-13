import hashlib
import os
import secrets
import base64
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel, EmailStr

try:
    from google import genai
except Exception:
    genai = None

APP_VERSION = "1.16.7"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
FOUNDER_USERNAME = os.getenv("ORBIT_FOUNDER_USERNAME", "Larsenda").strip() or "Larsenda"
FOUNDER_EMAIL = os.getenv("ORBIT_FOUNDER_EMAIL", "").strip().lower()
FOUNDER_PASSWORD = os.getenv("ORBIT_FOUNDER_PASSWORD", "")
ANALYTICS_SECRET = os.getenv("ORBIT_ANALYTICS_SECRET", "orbit-dev-analytics-change-me")
DOWNLOAD_URL = os.getenv("ORBIT_DOWNLOAD_URL", "").strip()
RELEASE_URL = os.getenv("ORBIT_RELEASE_URL", "https://github.com/larsendars-maker/OrbitBrowsers/releases/latest").strip()
DOWNLOAD_VERSION = os.getenv("ORBIT_DOWNLOAD_VERSION", APP_VERSION).strip()
DOWNLOAD_FILE_NAME = os.getenv("ORBIT_DOWNLOAD_FILE_NAME", "OrbitBrowser-Setup.exe").strip()
WEB_ORIGINS = [x.strip() for x in os.getenv("ORBIT_WEB_ORIGINS", "").split(",") if x.strip()]
SITE_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="Orbit API", version=APP_VERSION)
if WEB_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=WEB_ORIGINS, allow_credentials=True,
                       allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["Authorization", "Content-Type"])


def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL)


def pw_hash(password: str) -> str:
    salt = os.urandom(16)
    value = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=64)
    return f"{salt.hex()}:{value.hex()}"


def pw_verify(password: str, saved: str) -> bool:
    try:
        salt_hex, hash_hex = saved.split(":", 1)
        value = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=16384, r=8, p=1, dklen=64)
        return secrets.compare_digest(value, bytes.fromhex(hash_hex))
    except Exception:
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def bearer(auth: str | None) -> str:
    if not auth:
        raise HTTPException(401, "Authorization header is missing")
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(401, "Invalid authorization header")
    return parts[1].strip()


def row_user(row):
    return {
        "id": row[0], "username": row[1], "display_name": row[3] or row[1],
        "bio": row[4] or "", "title": row[5] or "Explorer", "xp": row[6] or 0,
        "profile_theme": row[7] or "VOID", "role": (row[8] or "user").lower(),
        "created_at": row[9].isoformat(),
    }


def current_user(token: str):
    with db() as conn, conn.cursor() as cur:
        cur.execute("""SELECT u.id,u.username,u.email,u.display_name,u.bio,u.title,u.xp,u.profile_theme,u.role,u.created_at
                      FROM users u JOIN sessions s ON s.user_id=u.id
                      WHERE s.token_hash=%s LIMIT 1""", (token_hash(token),))
        return cur.fetchone()


def require_user(auth):
    row = current_user(bearer(auth))
    if not row:
        raise HTTPException(401, "Session expired or invalid")
    return row


def require_admin(auth):
    row = require_user(auth)
    if row[8].lower() != "admin":
        raise HTTPException(403, "Admin role required")
    return row


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    display_name: str
    bio: str
    profile_theme: str


class RoleUpdate(BaseModel):
    role: str


class TitleEquipRequest(BaseModel):
    title_key: str


class AchievementClaimRequest(BaseModel):
    achievement_key: str


class AdminTitleGrantRequest(BaseModel):
    title_key: str


class SupportTicketCreate(BaseModel):
    subject: str
    message: str


class SupportTicketReply(BaseModel):
    message: str
    status: str = "open"

class GeminiImage(BaseModel):
    mime_type: str
    data: str


class GeminiChatRequest(BaseModel):
    model: str = "gemini-3.8-flash"
    message: str = ""
    previous_interaction_id: str | None = None
    images: list[GeminiImage] = []


GEMINI_MODELS = [
    {"id": "gemini-3.8-flash", "name": "Gemini 3.8 Flash", "description": "Самый универсальный быстрый вариант для обычного общения, кода и анализа фото."},
    {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash", "description": "Сильная модель для сложных запросов, кода и многошаговых задач."},
    {"id": "gemini-3.6-flash", "name": "Gemini 3.6 Flash", "description": "Хороший баланс скорости и мультимодального анализа."},
    {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash", "description": "Быстрый универсальный чат."},
    {"id": "gemini-3.5-flash-lite", "name": "Gemini 3.5 Flash-Lite", "description": "Максимально лёгкий и быстрый вариант."},
    {"id": "gemini-3.1-pro-preview", "name": "Gemini 3.1 Pro Preview", "description": "Для самых сложных задач, анализа и кода."},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "description": "Продвинутая модель для сложного reasoning и анализа."},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": "Стабильный быстрый вариант предыдущего поколения."},
]


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


def enforce_cooldown(user_id: int, action: str, seconds: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT last_at FROM rate_limits WHERE user_id=%s AND action=%s", (user_id, action))
        row = cur.fetchone()
        now = datetime.now(timezone.utc)
        if row:
            elapsed = (now - row[0]).total_seconds()
            if elapsed < seconds:
                raise HTTPException(429, f"Please wait {max(1, int(seconds-elapsed))} seconds before trying again.")
            cur.execute("UPDATE rate_limits SET last_at=%s WHERE user_id=%s AND action=%s", (now, user_id, action))
        else:
            cur.execute("INSERT INTO rate_limits(user_id,action,last_at) VALUES(%s,%s,%s)", (user_id, action, now))
        conn.commit()


def is_helper_or_admin(row):
    return row[8].lower() in {"helper", "admin"}



def analytics_key(request: Request) -> str:
    visitor_id = request.cookies.get("orbit_visitor_id", "").strip()
    if visitor_id:
        raw = f"cookie:{visitor_id}"
    else:
        ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "unknown")[:300]
        raw = f"fallback:{ip}|{ua}"
    return hashlib.sha256((ANALYTICS_SECRET + "|" + raw).encode("utf-8", "ignore")).hexdigest()


def ensure_visitor_cookie(response, request: Request):
    if not request.cookies.get("orbit_visitor_id"):
        response.set_cookie(
            "orbit_visitor_id", secrets.token_urlsafe(24), max_age=60*60*24*365*5,
            httponly=True, samesite="lax", secure=request.url.scheme == "https"
        )
    return response


def record_event(request: Request, event_type: str):
    key = analytics_key(request)
    with db() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO site_events(event_type, visitor_key) VALUES(%s,%s)", (event_type, key))
        conn.commit()


def site_stats():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM site_events WHERE event_type='view'")
        views = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT visitor_key) FROM site_events WHERE event_type='view'")
        unique_views = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM site_events WHERE event_type='download'")
        downloads = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT visitor_key) FROM site_events WHERE event_type='download'")
        unique_downloads = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
    return {"views": views, "unique_views": unique_views, "downloads": downloads,
            "unique_downloads": unique_downloads, "users": users}

@app.on_event("startup")
def startup():
    with db() as conn, conn.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY, username VARCHAR(32) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW())""")
        cur.execute("""CREATE TABLE IF NOT EXISTS sessions(
            id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            token_hash TEXT UNIQUE NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW())""")
        for q in [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(64)",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR(300) DEFAULT ''",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS title VARCHAR(64) DEFAULT 'Explorer'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_theme VARCHAR(32) DEFAULT 'VOID'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(16) DEFAULT 'user'",
        ]:
            cur.execute(q)
        cur.execute("UPDATE users SET display_name=username WHERE display_name IS NULL OR display_name=''")
        cur.execute("UPDATE users SET role='user' WHERE role IS NULL OR role NOT IN ('user','helper','admin')")
        cur.execute("""CREATE TABLE IF NOT EXISTS rate_limits(
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            action VARCHAR(32) NOT NULL,
            last_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(user_id, action))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS support_tickets(
            id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            subject VARCHAR(120) NOT NULL, message TEXT NOT NULL, status VARCHAR(16) NOT NULL DEFAULT 'open',
            helper_id INTEGER REFERENCES users(id) ON DELETE SET NULL, reply TEXT DEFAULT '',
            created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW())""")
        cur.execute("""CREATE INDEX IF NOT EXISTS support_tickets_status_idx ON support_tickets(status,updated_at DESC)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS site_events(
            id BIGSERIAL PRIMARY KEY, event_type VARCHAR(24) NOT NULL, visitor_key CHAR(64) NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW())""")
        cur.execute("""CREATE INDEX IF NOT EXISTS site_events_type_idx ON site_events(event_type,created_at DESC)""")
        cur.execute("""CREATE INDEX IF NOT EXISTS site_events_unique_idx ON site_events(event_type,visitor_key)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS download_files(
            key VARCHAR(64) PRIMARY KEY, name VARCHAR(160) NOT NULL, version VARCHAR(32) NOT NULL,
            file_name VARCHAR(255) NOT NULL, url TEXT NOT NULL, is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW())""")

        cur.execute("""CREATE TABLE IF NOT EXISTS titles(
            id SERIAL PRIMARY KEY, key VARCHAR(64) UNIQUE NOT NULL,
            name_ru VARCHAR(64) NOT NULL, name_en VARCHAR(64) NOT NULL,
            description VARCHAR(300) NOT NULL, achievement_key VARCHAR(64),
            role_required VARCHAR(16), is_active BOOLEAN DEFAULT TRUE)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS user_titles(
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            title_key VARCHAR(64) REFERENCES titles(key) ON DELETE CASCADE,
            unlocked_at TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(user_id,title_key))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS user_achievements(
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            achievement_key VARCHAR(64), unlocked_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY(user_id,achievement_key))""")
        titles = [
            ("explorer", "Исследователь", "Explorer", "Открывайте страницы и изучайте интернет.", "explorer", None),
            ("newcomer", "Новичок", "Newcomer", "Первый запуск Orbit.", "first_launch", None),
            ("collector", "Коллекционер", "Collector", "Собирайте полезные страницы в закладки.", "collector", None),
            ("navigator", "Навигатор", "Navigator", "Настройте быстрый доступ.", "navigator", None),
            ("archivist", "Архивариус", "Archivist", "Сохраняйте заметки и идеи.", "notes", None),
            ("helper", "Помощник", "Helper", "Служебный титул роли Helper.", None, "helper"),
            ("admin", "Администратор", "Administrator", "Служебный титул роли Admin.", None, "admin"),
            ("creator", "Создатель Orbit", "Orbit Creator", "Особый титул владельца проекта.", "founder", "admin"),
        ]
        for t in titles:
            cur.execute("""INSERT INTO titles(key,name_ru,name_en,description,achievement_key,role_required)
                           VALUES(%s,%s,%s,%s,%s,%s)
                           ON CONFLICT(key) DO UPDATE SET name_ru=EXCLUDED.name_ru,name_en=EXCLUDED.name_en,
                           description=EXCLUDED.description,achievement_key=EXCLUDED.achievement_key,
                           role_required=EXCLUDED.role_required,is_active=TRUE""", t)

        if FOUNDER_EMAIL and FOUNDER_PASSWORD:
            cur.execute("SELECT id FROM users WHERE LOWER(email)=LOWER(%s) OR LOWER(username)=LOWER(%s) LIMIT 1", (FOUNDER_EMAIL, FOUNDER_USERNAME))
            found = cur.fetchone()
            if found:
                uid = found[0]
                cur.execute("UPDATE users SET username=%s,display_name=%s,role='admin',title='Создатель Orbit' WHERE id=%s", (FOUNDER_USERNAME, FOUNDER_USERNAME, uid))
            else:
                cur.execute("""INSERT INTO users(username,email,password_hash,display_name,title,xp,profile_theme,role)
                               VALUES(%s,%s,%s,%s,'Создатель Orbit',0,'VOID','admin') RETURNING id""",
                            (FOUNDER_USERNAME, FOUNDER_EMAIL, pw_hash(FOUNDER_PASSWORD), FOUNDER_USERNAME))
                uid = cur.fetchone()[0]
            for key in ("creator", "admin"):
                cur.execute("INSERT INTO user_titles(user_id,title_key) VALUES(%s,%s) ON CONFLICT DO NOTHING", (uid, key))
        elif FOUNDER_EMAIL:
            cur.execute("UPDATE users SET role='admin',title='Создатель Orbit' WHERE LOWER(email)=LOWER(%s)", (FOUNDER_EMAIL,))
            cur.execute("INSERT INTO user_titles(user_id,title_key) SELECT id,'creator' FROM users WHERE LOWER(email)=LOWER(%s) ON CONFLICT DO NOTHING", (FOUNDER_EMAIL,))
        if DOWNLOAD_URL:
            cur.execute("""INSERT INTO download_files(key,name,version,file_name,url,is_active)
                           VALUES('orbit-browser','Orbit Browser',%s,%s,%s,TRUE)
                           ON CONFLICT(key) DO UPDATE SET name=EXCLUDED.name,version=EXCLUDED.version,
                           file_name=EXCLUDED.file_name,url=EXCLUDED.url,is_active=TRUE""",
                        (DOWNLOAD_VERSION, DOWNLOAD_FILE_NAME, DOWNLOAD_URL or RELEASE_URL))
        conn.commit()


@app.get("/")
def root(request: Request):
    record_event(request, "view")
    response = FileResponse(SITE_DIR / "index.html")
    return ensure_visitor_cookie(response, request)


@app.get("/admin")
def admin_page():
    return FileResponse(SITE_DIR / "admin.html")

@app.get("/assets/{name}")
def site_asset(name: str):
    path = SITE_DIR / "assets" / name
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "Asset not found")
    return FileResponse(path)




@app.get("/health")
def health():
    return {"ok": True, "service": "orbit-api", "version": APP_VERSION}


@app.post("/api/auth/register")
def register(data: RegisterRequest):
    username = data.username.strip()
    email = str(data.email).lower().strip()
    if not 3 <= len(username) <= 32:
        raise HTTPException(400, "Username must contain 3-32 characters")
    if len(data.password) < 8:
        raise HTTPException(400, "Password must contain at least 8 characters")
    if username.lower() == FOUNDER_USERNAME.lower() and (not FOUNDER_EMAIL or email != FOUNDER_EMAIL):
        raise HTTPException(403, "This username is reserved")
    try:
        with db() as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO users(username,email,password_hash,display_name,title,xp,profile_theme,role)
                           VALUES(%s,%s,%s,%s,'Explorer',0,'VOID','user')
                           RETURNING id,username,email,display_name,bio,title,xp,profile_theme,role,created_at""",
                        (username, email, pw_hash(data.password), username))
            row = cur.fetchone()
            cur.execute("INSERT INTO user_titles(user_id,title_key) VALUES(%s,'explorer') ON CONFLICT DO NOTHING", (row[0],))
            conn.commit()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "Username or email already exists")
    token = secrets.token_urlsafe(48)
    with db() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO sessions(user_id,token_hash) VALUES(%s,%s)", (row[0], token_hash(token)))
        conn.commit()
    return {"ok": True, "token": token, "user": row_user(row)}


@app.post("/api/auth/login")
def login(data: LoginRequest):
    email = str(data.email).lower().strip()
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id,username,email,display_name,bio,title,xp,profile_theme,role,password_hash,created_at FROM users WHERE LOWER(email)=LOWER(%s) LIMIT 1", (email,))
        row = cur.fetchone()
    if not row or not pw_verify(data.password, row[9]):
        raise HTTPException(401, "Invalid email or password")
    token = secrets.token_urlsafe(48)
    with db() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO sessions(user_id,token_hash) VALUES(%s,%s)", (row[0], token_hash(token)))
        conn.commit()
    return {"ok": True, "token": token, "user": row_user(row)}


@app.get("/api/auth/session")
def session(authorization: str | None = Header(default=None)):
    return {"ok": True, "user": row_user(require_user(authorization))}


@app.patch("/api/profile")
def profile(data: ProfileUpdate, authorization: str | None = Header(default=None)):
    row = require_user(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("UPDATE users SET display_name=%s,bio=%s,profile_theme=%s WHERE id=%s",
                    ((data.display_name.strip() or row[1])[:64], data.bio.strip()[:300], data.profile_theme.strip().upper()[:32], row[0]))
        conn.commit()
    return {"ok": True, "user": row_user(current_user(bearer(authorization)))}


@app.get("/api/profile/titles")
def profile_titles(authorization: str | None = Header(default=None)):
    row = require_user(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT key,name_ru,name_en,description,achievement_key,role_required FROM titles WHERE is_active=TRUE ORDER BY id")
        all_titles = cur.fetchall()
        cur.execute("SELECT title_key FROM user_titles WHERE user_id=%s", (row[0],))
        unlocked = {x[0] for x in cur.fetchall()}
    return {"ok": True, "equipped": row[5] or "Explorer", "titles": [
        {"key": t[0], "name_ru": t[1], "name_en": t[2], "description": t[3], "achievement_key": t[4],
         "role_required": t[5], "unlocked": t[0] in unlocked} for t in all_titles]}


@app.post("/api/profile/achievements/claim")
def claim_achievement(data: AchievementClaimRequest, authorization: str | None = Header(default=None)):
    row = require_user(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT key,role_required FROM titles WHERE achievement_key=%s AND is_active=TRUE LIMIT 1", (data.achievement_key,))
        title = cur.fetchone()
        if not title:
            raise HTTPException(404, "Achievement reward not found")
        if title[1] and row[8].lower() not in {title[1].lower(), "admin"}:
            raise HTTPException(403, "Role required")
        cur.execute("INSERT INTO user_achievements(user_id,achievement_key) VALUES(%s,%s) ON CONFLICT DO NOTHING", (row[0], data.achievement_key))
        cur.execute("INSERT INTO user_titles(user_id,title_key) VALUES(%s,%s) ON CONFLICT DO NOTHING", (row[0], title[0]))
        conn.commit()
    return {"ok": True, "title_key": title[0]}


@app.post("/api/profile/title")
def equip_title(data: TitleEquipRequest, authorization: str | None = Header(default=None)):
    row = require_user(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("""SELECT t.key,t.name_ru,t.role_required FROM titles t JOIN user_titles ut ON ut.title_key=t.key
                       WHERE ut.user_id=%s AND t.key=%s AND t.is_active=TRUE""", (row[0], data.title_key))
        title = cur.fetchone()
        if not title:
            raise HTTPException(403, "Title is not unlocked")
        if title[2] and row[8].lower() not in {title[2].lower(), "admin"}:
            raise HTTPException(403, "Role required")
        cur.execute("UPDATE users SET title=%s WHERE id=%s", (title[1], row[0]))
        conn.commit()
    return {"ok": True, "title": title[1], "user": row_user(current_user(bearer(authorization)))}


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    token = bearer(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM sessions WHERE token_hash=%s", (token_hash(token),))
        conn.commit()
    return {"ok": True}


@app.post("/api/support/tickets")
def create_support_ticket(data: SupportTicketCreate, authorization: str | None = Header(default=None)):
    row = require_user(authorization)
    enforce_cooldown(row[0], "support_ticket", 30)
    subject = data.subject.strip()[:120]
    message = data.message.strip()[:4000]
    if not subject or not message:
        raise HTTPException(400, "Subject and message are required")
    with db() as conn, conn.cursor() as cur:
        cur.execute("""INSERT INTO support_tickets(user_id,subject,message) VALUES(%s,%s,%s)
                       RETURNING id,subject,message,status,created_at,updated_at""", (row[0], subject, message))
        t = cur.fetchone()
        conn.commit()
    return {"ok": True, "ticket": dict(id=t[0], subject=t[1], message=t[2], status=t[3], created_at=t[4].isoformat(), updated_at=t[5].isoformat())}


@app.get("/api/support/my")
def my_support_tickets(authorization: str | None = Header(default=None)):
    row = require_user(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("""SELECT id,subject,message,status,reply,created_at,updated_at FROM support_tickets
                       WHERE user_id=%s ORDER BY updated_at DESC LIMIT 50""", (row[0],))
        rows = cur.fetchall()
    return {"ok": True, "tickets": [dict(id=r[0],subject=r[1],message=r[2],status=r[3],reply=r[4] or "",created_at=r[5].isoformat(),updated_at=r[6].isoformat()) for r in rows]}


@app.get("/api/support/tickets")
def support_tickets(authorization: str | None = Header(default=None)):
    row = require_user(authorization)
    if not is_helper_or_admin(row):
        raise HTTPException(403, "Helper or Admin role required")
    with db() as conn, conn.cursor() as cur:
        cur.execute("""SELECT t.id,t.subject,t.message,t.status,t.reply,t.created_at,t.updated_at,
                              u.username,u.display_name,t.helper_id
                       FROM support_tickets t JOIN users u ON u.id=t.user_id
                       ORDER BY CASE WHEN t.status='open' THEN 0 ELSE 1 END, t.updated_at DESC LIMIT 200""")
        rows = cur.fetchall()
    return {"ok": True, "tickets": [dict(id=r[0],subject=r[1],message=r[2],status=r[3],reply=r[4] or "",created_at=r[5].isoformat(),updated_at=r[6].isoformat(),username=r[7],display_name=r[8] or r[7],helper_id=r[9]) for r in rows]}


@app.patch("/api/support/tickets/{ticket_id}")
def reply_support_ticket(ticket_id: int, data: SupportTicketReply, authorization: str | None = Header(default=None)):
    row = require_user(authorization)
    if not is_helper_or_admin(row):
        raise HTTPException(403, "Helper or Admin role required")
    enforce_cooldown(row[0], "support_reply", 2)
    status = data.status.lower().strip()
    if status not in {"open", "pending", "closed"}:
        raise HTTPException(400, "Invalid ticket status")
    reply = data.message.strip()[:4000]
    with db() as conn, conn.cursor() as cur:
        cur.execute("""UPDATE support_tickets SET reply=%s,status=%s,helper_id=%s,updated_at=NOW()
                       WHERE id=%s RETURNING id,subject,message,status,reply,created_at,updated_at""", (reply, status, row[0], ticket_id))
        t = cur.fetchone()
        if not t:
            raise HTTPException(404, "Ticket not found")
        conn.commit()
    return {"ok": True, "ticket": dict(id=t[0],subject=t[1],message=t[2],status=t[3],reply=t[4] or "",created_at=t[5].isoformat(),updated_at=t[6].isoformat())}


@app.get("/api/helper/overview")
def helper_overview(authorization: str | None = Header(default=None)):
    row = require_user(authorization)
    if not is_helper_or_admin(row):
        raise HTTPException(403, "Helper or Admin role required")
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM support_tickets WHERE status='open'")
        open_tickets = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM support_tickets")
        total_tickets = cur.fetchone()[0]
    return {"ok": True, "open_tickets": open_tickets, "total_tickets": total_tickets}


@app.get("/api/admin/users")
def admin_users(authorization: str | None = Header(default=None)):
    require_admin(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id,username,display_name,role,title,created_at FROM users ORDER BY created_at DESC LIMIT 200")
        rows = cur.fetchall()
    return {"ok": True, "users": [dict(id=r[0], username=r[1], display_name=r[2] or r[1], role=r[3] or "user", title=r[4] or "Explorer", created_at=r[5].isoformat()) for r in rows]}


@app.patch("/api/admin/users/{user_id}/role")
def admin_set_role(user_id: int, data: RoleUpdate, authorization: str | None = Header(default=None)):
    admin = require_admin(authorization)
    role = data.role.lower().strip()
    if role not in {"user", "helper", "admin"}:
        raise HTTPException(400, "Role must be user, helper or admin")
    if user_id == admin[0] and role != "admin":
        raise HTTPException(400, "You cannot demote yourself")
    with db() as conn, conn.cursor() as cur:
        cur.execute("UPDATE users SET role=%s WHERE id=%s RETURNING id,username,display_name,role,title", (role, user_id))
        updated = cur.fetchone()
        if not updated:
            raise HTTPException(404, "User not found")
        if role in {"helper", "admin"}:
            cur.execute("INSERT INTO user_titles(user_id,title_key) VALUES(%s,%s) ON CONFLICT DO NOTHING", (user_id, role))
        conn.commit()
    return {"ok": True, "user": dict(id=updated[0], username=updated[1], display_name=updated[2], role=updated[3], title=updated[4])}


@app.patch("/api/admin/users/{user_id}/title")
def admin_set_title(user_id: int, data: AdminTitleGrantRequest, authorization: str | None = Header(default=None)):
    require_admin(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT key,name_ru,name_en,role_required FROM titles WHERE key=%s AND is_active=TRUE LIMIT 1", (data.title_key.strip(),))
        title = cur.fetchone()
        if not title:
            raise HTTPException(404, "Title not found")
        cur.execute("SELECT id,username,display_name,role,title FROM users WHERE id=%s LIMIT 1", (user_id,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(404, "User not found")
        cur.execute("INSERT INTO user_titles(user_id,title_key) VALUES(%s,%s) ON CONFLICT DO NOTHING", (user_id, title[0]))
        cur.execute("UPDATE users SET title=%s WHERE id=%s", (title[1], user_id))
        conn.commit()
    return {"ok": True, "title_key": title[0], "title": title[1]}


@app.get("/api/admin/titles")
def admin_titles(authorization: str | None = Header(default=None)):
    require_admin(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT key,name_ru,name_en,description,achievement_key,role_required,is_active FROM titles ORDER BY id")
        rows = cur.fetchall()
    return {"ok": True, "titles": [dict(key=r[0], name_ru=r[1], name_en=r[2], description=r[3], achievement_key=r[4], role_required=r[5], is_active=r[6]) for r in rows]}


@app.get("/api/ai/models")
def ai_models(authorization: str | None = Header(default=None)):
    require_user(authorization)
    if not GEMINI_API_KEY:
        return {"ok": True, "configured": False, "models": GEMINI_MODELS}
    return {"ok": True, "configured": True, "models": GEMINI_MODELS}


@app.post("/api/ai/chat")
def ai_chat(data: GeminiChatRequest, authorization: str | None = Header(default=None)):
    require_user(authorization)
    if not GEMINI_API_KEY:
        raise HTTPException(503, "Gemini API is not configured. Add GEMINI_API_KEY to Render Environment Variables.")
    if genai is None:
        raise HTTPException(500, "google-genai is not installed on the server")
    model_ids = {m["id"] for m in GEMINI_MODELS}
    if data.model not in model_ids:
        raise HTTPException(400, "Unsupported Gemini model")
    prompt = data.message.strip()
    if not prompt and not data.images:
        raise HTTPException(400, "Message or image is required")
    if len(data.images) > 4:
        raise HTTPException(400, "Up to 4 images can be attached")
    inputs = []
    if prompt:
        inputs.append({"type": "text", "text": prompt})
    for image in data.images:
        try:
            raw = base64.b64decode(image.data, validate=True)
        except Exception:
            raise HTTPException(400, "Invalid image data")
        if len(raw) > 12 * 1024 * 1024:
            raise HTTPException(413, "Image is too large")
        inputs.append({"type": "image", "data": base64.b64encode(raw).decode("ascii"), "mime_type": image.mime_type})
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        kwargs = {"model": data.model, "input": inputs}
        if data.previous_interaction_id:
            kwargs["previous_interaction_id"] = data.previous_interaction_id
        interaction = client.interactions.create(**kwargs)
        text = getattr(interaction, "output_text", None) or ""
        if not text:
            outputs = getattr(interaction, "outputs", None) or []
            parts = []
            for output in outputs:
                value = getattr(output, "text", None)
                if value:
                    parts.append(value)
            text = "\n".join(parts).strip()
        return {"ok": True, "text": text, "interaction_id": getattr(interaction, "id", None), "model": data.model}
    except Exception as exc:
        message = str(exc)
        raise HTTPException(502, f"Gemini request failed: {message[:500]}")



@app.get("/api/site/stats")
def public_site_stats():
    stats = site_stats()
    return {"ok": True, "views": stats["views"], "unique_views": stats["unique_views"],
            "downloads": stats["downloads"], "unique_downloads": stats["unique_downloads"]}


@app.get("/api/downloads")
def download_catalog():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT key,name,version,file_name,is_active FROM download_files WHERE is_active=TRUE ORDER BY name")
        rows = cur.fetchall()
    return {"ok": True, "files": [dict(key=r[0],name=r[1],version=r[2],file_name=r[3],download_url=f"/download/{r[0]}") for r in rows]}


@app.get("/download/{file_key}")
def download_file(file_key: str, request: Request):
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT key,url,is_active FROM download_files WHERE key=%s LIMIT 1", (file_key,))
        row = cur.fetchone()
    if not row or not row[2] or not row[1]:
        raise HTTPException(404, "Download is not configured yet")
    record_event(request, "download")
    response = RedirectResponse(row[1] or RELEASE_URL, status_code=302)
    return ensure_visitor_cookie(response, request)


@app.get("/api/admin/overview")
def admin_overview(authorization: str | None = Header(default=None)):
    require_admin(authorization)
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE role='helper'")
        helpers = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        admins = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM support_tickets WHERE status='open'")
        open_tickets = cur.fetchone()[0]
    return {"ok": True, "users": users, "helpers": helpers, "admins": admins, "open_tickets": open_tickets}


@app.get("/api/admin/site/stats")
def admin_site_stats(authorization: str | None = Header(default=None)):
    require_admin(authorization)
    return {"ok": True, **site_stats()}

@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return "User-agent: *\nDisallow: /api/\nDisallow: /admin\n"
