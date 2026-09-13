import hashlib
import os
import secrets

import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, EmailStr


APP_VERSION = "0.3.0"

DATABASE_URL = os.getenv("DATABASE_URL")
FOUNDER_EMAIL = os.getenv("ORBIT_FOUNDER_EMAIL", "").strip().lower()

app = FastAPI(
    title="Orbit API",
    version=APP_VERSION,
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    return psycopg.connect(DATABASE_URL)


def init_database():
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(32) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            # НОВЫЕ ПОЛЯ ПРОФИЛЯ
            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS display_name VARCHAR(64)
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS bio VARCHAR(300) DEFAULT ''
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS title VARCHAR(64) DEFAULT 'Explorer'
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS profile_theme VARCHAR(32) DEFAULT 'VOID'
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS role VARCHAR(32) DEFAULT 'user'
                """
            )

            # Старым пользователям добавляем display_name
            cur.execute(
                """
                UPDATE users
                SET display_name = username
                WHERE display_name IS NULL
                """
            )

            # Пользователю-основателю назначаем Founder
            if FOUNDER_EMAIL:
                cur.execute(
                    """
                    UPDATE users
                    SET role = 'founder',
                        title = 'Creator of Orbit'
                    WHERE LOWER(email) = %s
                    """,
                    (FOUNDER_EMAIL,),
                )

        conn.commit()


# ============================================================
# PASSWORDS
# ============================================================

def hash_password(password: str) -> str:
    salt = os.urandom(16)

    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=64,
    )

    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(":", 1)

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1,
            dklen=64,
        )

        return secrets.compare_digest(
            actual_hash,
            expected_hash,
        )

    except Exception:
        return False


# ============================================================
# SESSIONS
# ============================================================

def hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    token_hash = hash_token(token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (
                    user_id,
                    token_hash
                )
                VALUES (%s, %s)
                """,
                (user_id, token_hash),
            )

        conn.commit()

    return token


def get_user_by_token(token: str):
    token_hash = hash_token(token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    display_name,
                    bio,
                    title,
                    xp,
                    profile_theme,
                    role,
                    created_at
                FROM users
                INNER JOIN sessions
                    ON users.id = sessions.user_id
                WHERE sessions.token_hash = %s
                LIMIT 1
                """,
                (token_hash,),
            )

            return cur.fetchone()


def get_bearer_token(
    authorization: str | None,
) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is missing",
        )

    parts = authorization.split(" ", 1)

    if len(parts) != 2:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
        )

    scheme, token = parts

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization scheme",
        )

    token = token.strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Token is empty",
        )

    return token


# ============================================================
# MODELS
# ============================================================

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    display_name: str
    bio: str
    title: str
    profile_theme: str


# ============================================================
# USER SERIALIZATION
# ============================================================

def user_to_dict(row):
    (
        user_id,
        username,
        email,
        display_name,
        bio,
        title,
        xp,
        profile_theme,
        role,
        created_at,
    ) = row

    return {
        "id": user_id,
        "username": username,
        "email": email,
        "display_name": display_name or username,
        "bio": bio or "",
        "title": title or "Explorer",
        "xp": xp or 0,
        "profile_theme": profile_theme or "VOID",
        "role": role or "user",
        "created_at": created_at.isoformat(),
    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    init_database()


# ============================================================
# ROOT / HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "ok": True,
        "service": "orbit-api",
        "version": APP_VERSION,
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "orbit-api",
        "version": APP_VERSION,
    }


# ============================================================
# REGISTER
# ============================================================

@app.post("/api/auth/register")
def register(data: RegisterRequest):
    username = data.username.strip()
    email = str(data.email).strip().lower()
    password = data.password

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must contain at least 3 characters",
        )

    if len(username) > 32:
        raise HTTPException(
            status_code=400,
            detail="Username is too long",
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters",
        )

    password_hash = hash_password(password)

    role = "user"
    title = "Explorer"

    if FOUNDER_EMAIL and email == FOUNDER_EMAIL:
        role = "founder"
        title = "Creator of Orbit"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (
                        username,
                        email,
                        password_hash,
                        display_name,
                        bio,
                        title,
                        xp,
                        profile_theme,
                        role
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING
                        id,
                        username,
                        email,
                        display_name,
                        bio,
                        title,
                        xp,
                        profile_theme,
                        role,
                        created_at
                    """,
                    (
                        username,
                        email,
                        password_hash,
                        username,
                        "",
                        title,
                        0,
                        "VOID",
                        role,
                    ),
                )

                user = cur.fetchone()

            conn.commit()

    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists",
        )

    user_id = user[0]

    token = create_session(user_id)

    return {
        "ok": True,
        "token": token,
        "user": user_to_dict(user),
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/auth/login")
def login(data: LoginRequest):
    email = str(data.email).strip().lower()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    display_name,
                    bio,
                    title,
                    xp,
                    profile_theme,
                    role,
                    password_hash,
                    created_at
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,),
            )

            user = cur.fetchone()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    (
        user_id,
        username,
        user_email,
        display_name,
        bio,
        title,
        xp,
        profile_theme,
        role,
        password_hash,
        created_at,
    ) = user

    if not verify_password(
        data.password,
        password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_session(user_id)

    return {
        "ok": True,
        "token": token,
        "user": {
            "id": user_id,
            "username": username,
            "email": user_email,
            "display_name": display_name or username,
            "bio": bio or "",
            "title": title or "Explorer",
            "xp": xp or 0,
            "profile_theme": profile_theme or "VOID",
            "role": role or "user",
            "created_at": created_at.isoformat(),
        },
    }


# ============================================================
# SESSION
# ============================================================

@app.get("/api/auth/session")
def session(
    authorization: str | None = Header(default=None),
):
    token = get_bearer_token(authorization)

    user = get_user_by_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
        )

    return {
        "ok": True,
        "user": user_to_dict(user),
    }


# ============================================================
# PROFILE
# ============================================================

@app.get("/api/profile")
def profile(
    authorization: str | None = Header(default=None),
):
    token = get_bearer_token(authorization)

    user = get_user_by_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
        )

    return {
        "ok": True,
        "user": user_to_dict(user),
    }


@app.patch("/api/profile")
def update_profile(
    data: ProfileUpdateRequest,
    authorization: str | None = Header(default=None),
):
    token = get_bearer_token(authorization)

    user = get_user_by_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
        )

    user_id = user[0]

    display_name = data.display_name.strip()
    bio = data.bio.strip()
    title = data.title.strip()
    profile_theme = data.profile_theme.strip().upper()

    if not display_name:
        display_name = user[1]

    if len(display_name) > 64:
        raise HTTPException(
            status_code=400,
            detail="Display name is too long",
        )

    if len(bio) > 300:
        raise HTTPException(
            status_code=400,
            detail="Bio is too long",
        )

    if len(title) > 64:
        raise HTTPException(
            status_code=400,
            detail="Title is too long",
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET
                    display_name = %s,
                    bio = %s,
                    title = %s,
                    profile_theme = %s
                WHERE id = %s
                """,
                (
                    display_name,
                    bio,
                    title,
                    profile_theme,
                    user_id,
                ),
            )

        conn.commit()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    display_name,
                    bio,
                    title,
                    xp,
                    profile_theme,
                    role,
                    created_at
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )

            updated_user = cur.fetchone()

    return {
        "ok": True,
        "user": user_to_dict(updated_user),
    }


# ============================================================
# LOGOUT
# ============================================================

@app.post("/api/auth/logout")
def logout(
    authorization: str | None = Header(default=None),
):
    token = get_bearer_token(authorization)

    token_hash = hash_token(token)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM sessions
                WHERE token_hash = %s
                """,
                (token_hash,),
            )

        conn.commit()

    return {
        "ok": True,
    }