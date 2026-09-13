import hashlib
import os
import secrets
from datetime import datetime, timezone

import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, EmailStr


APP_VERSION = "0.2.1"

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(
    title="Orbit API",
    version=APP_VERSION,
)


# =========================
# DATABASE
# =========================

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

        conn.commit()


# =========================
# PASSWORDS
# =========================

def hash_password(password: str) -> str:
    salt = os.urandom(16)

    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=64,
    )

    return (
        salt.hex()
        + ":"
        + derived_key.hex()
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(":", 1)

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        derived_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1,
            dklen=64,
        )

        return secrets.compare_digest(
            derived_key,
            expected_hash,
        )

    except Exception:
        return False


# =========================
# SESSIONS
# =========================

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
                (
                    user_id,
                    token_hash,
                ),
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
                    users.id,
                    users.username,
                    users.email,
                    users.created_at
                FROM sessions
                INNER JOIN users
                    ON users.id = sessions.user_id
                WHERE sessions.token_hash = %s
                LIMIT 1
                """,
                (token_hash,),
            )

            return cur.fetchone()


def extract_bearer_token(authorization: str | None) -> str:
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

    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
        )

    return token.strip()


# =========================
# MODELS
# =========================

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# =========================
# STARTUP
# =========================

@app.on_event("startup")
def startup():
    init_database()


# =========================
# HEALTH
# =========================

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "orbit-api",
        "version": APP_VERSION,
    }


# =========================
# REGISTER
# =========================

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

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (
                        username,
                        email,
                        password_hash
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id, username, email, created_at
                    """,
                    (
                        username,
                        email,
                        password_hash,
                    ),
                )

                user = cur.fetchone()

            conn.commit()

    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists",
        )

    user_id, user_username, user_email, created_at = user

    token = create_session(user_id)

    return {
        "ok": True,
        "token": token,
        "user": {
            "id": user_id,
            "username": user_username,
            "email": user_email,
            "created_at": created_at.isoformat(),
        },
    }


# =========================
# LOGIN
# =========================

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
            "created_at": created_at.isoformat(),
        },
    }


# =========================
# CURRENT SESSION
# =========================

@app.get("/api/auth/session")
def session(
    authorization: str | None = Header(default=None)
):
    token = extract_bearer_token(authorization)

    user = get_user_by_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid",
        )

    (
        user_id,
        username,
        email,
        created_at,
    ) = user

    return {
        "ok": True,
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
            "created_at": created_at.isoformat(),
        },
    }


# =========================
# LOGOUT
# =========================

@app.post("/api/auth/logout")
def logout(
    authorization: str | None = Header(default=None)
):
    token = extract_bearer_token(authorization)
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
        "ok": True
    }