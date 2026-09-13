```python
import hashlib
import os
import secrets

import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, EmailStr


app = FastAPI(
    title="Orbit API",
    version="0.2.0",
)

DATABASE_URL = os.getenv("DATABASE_URL")


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL не настроен в Environment Variables Render."
        )

    return psycopg.connect(DATABASE_URL)


def init_database():
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            conn.commit()


# ============================================================
# PASSWORD
# ============================================================

def hash_password(
    password: str,
    salt: bytes | None = None,
):
    if salt is None:
        salt = secrets.token_bytes(16)

    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def verify_password(
    password: str,
    stored_hash: str,
):
    try:
        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)

        password_hash = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
        )

        return secrets.compare_digest(
            password_hash.hex(),
            hash_hex,
        )

    except Exception:
        return False


# ============================================================
# SESSION
# ============================================================

def create_session(user_id: int):
    token = secrets.token_urlsafe(48)

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

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

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    users.id,
                    users.username,
                    users.email
                FROM sessions
                JOIN users
                    ON users.id = sessions.user_id
                WHERE sessions.token_hash = %s
                """,
                (token_hash,),
            )

            return cur.fetchone()


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


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    init_database()


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "orbit-api",
        "version": "0.2.0",
    }


# ============================================================
# REGISTER
# ============================================================

@app.post("/api/auth/register")
def register(data: RegisterRequest):

    username = data.username.strip()
    email = data.email.lower().strip()
    password = data.password

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Имя пользователя должно содержать минимум 3 символа.",
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Пароль должен содержать минимум 6 символов.",
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
                    RETURNING id, username, email
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
            detail="Пользователь с таким email или именем уже существует.",
        )

    token = create_session(user[0])

    return {
        "token": token,
        "user": {
            "id": user[0],
            "username": user[1],
            "email": user[2],
        },
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/api/auth/login")
def login(data: LoginRequest):

    email = data.email.lower().strip()

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    username,
                    email,
                    password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )

            user = cur.fetchone()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль.",
        )

    if not verify_password(
        data.password,
        user[3],
    ):
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль.",
        )

    token = create_session(user[0])

    return {
        "token": token,
        "user": {
            "id": user[0],
            "username": user[1],
            "email": user[2],
        },
    }


# ============================================================
# SESSION CHECK
# ============================================================

@app.get("/api/auth/session")
def check_session(
    authorization: str = Header(default=""),
):

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Сессия отсутствует.",
        )

    token = authorization[7:].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Сессия отсутствует.",
        )

    user = get_user_by_token(token)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Сессия недействительна.",
        )

    return {
        "ok": True,
        "user": {
            "id": user[0],
            "username": user[1],
            "email": user[2],
        },
    }


# ============================================================
# LOGOUT
# ============================================================

@app.post("/api/auth/logout")
def logout(
    authorization: str = Header(default=""),
):

    if not authorization.startswith("Bearer "):
        return {
            "ok": True,
        }

    token = authorization[7:].strip()

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

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
```
