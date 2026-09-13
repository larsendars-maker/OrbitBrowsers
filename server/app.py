import hashlib, os, secrets
import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, EmailStr

APP_VERSION = "0.4.0"
DATABASE_URL = os.getenv("DATABASE_URL")
FOUNDER_EMAIL = os.getenv("ORBIT_FOUNDER_EMAIL", "").strip().lower()
app = FastAPI(title="Orbit API", version=APP_VERSION)

def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL)

def pw_hash(p):
    s=os.urandom(16); h=hashlib.scrypt(p.encode(),salt=s,n=16384,r=8,p=1,dklen=64); return f"{s.hex()}:{h.hex()}"

def pw_verify(p,saved):
    try:
        sh,hh=saved.split(":",1); s=bytes.fromhex(sh); expected=bytes.fromhex(hh); actual=hashlib.scrypt(p.encode(),salt=s,n=16384,r=8,p=1,dklen=64); return secrets.compare_digest(actual,expected)
    except Exception: return False

def th(t): return hashlib.sha256(t.encode()).hexdigest()

def bearer(auth):
    if not auth: raise HTTPException(401,"Authorization header is missing")
    parts=auth.split(" ",1)
    if len(parts)!=2 or parts[0].lower()!="bearer": raise HTTPException(401,"Invalid authorization header")
    return parts[1].strip()

def serialize(r):
    return {"id":r[0],"username":r[1],"email":r[2],"display_name":r[3] or r[1],"bio":r[4] or "","title":r[5] or "Explorer","xp":r[6] or 0,"profile_theme":r[7] or "VOID","role":r[8] or "user","created_at":r[9].isoformat()}

def current(t):
    with db() as c:
        with c.cursor() as x:
            x.execute("SELECT u.id,u.username,u.email,u.display_name,u.bio,u.title,u.xp,u.profile_theme,u.role,u.created_at FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=%s LIMIT 1",(th(t),)); return x.fetchone()

class RegisterRequest(BaseModel):
    username:str; email:EmailStr; password:str
class LoginRequest(BaseModel):
    email:EmailStr; password:str
class ProfileUpdate(BaseModel):
    display_name:str; bio:str; title:str; profile_theme:str

@app.on_event("startup")
def startup():
    with db() as c:
        with c.cursor() as x:
            x.execute("CREATE TABLE IF NOT EXISTS users(id SERIAL PRIMARY KEY,username VARCHAR(32) UNIQUE NOT NULL,email VARCHAR(255) UNIQUE NOT NULL,password_hash TEXT NOT NULL,created_at TIMESTAMPTZ DEFAULT NOW())")
            x.execute("CREATE TABLE IF NOT EXISTS sessions(id SERIAL PRIMARY KEY,user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,token_hash TEXT UNIQUE NOT NULL,created_at TIMESTAMPTZ DEFAULT NOW())")
            for q in ["ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(64)","ALTER TABLE users ADD COLUMN IF NOT EXISTS bio VARCHAR(300) DEFAULT ''","ALTER TABLE users ADD COLUMN IF NOT EXISTS title VARCHAR(64) DEFAULT 'Explorer'","ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0","ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_theme VARCHAR(32) DEFAULT 'VOID'","ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(32) DEFAULT 'user'"]: x.execute(q)
            x.execute("UPDATE users SET display_name=username WHERE display_name IS NULL")
            if FOUNDER_EMAIL: x.execute("UPDATE users SET role='founder',title='Creator of Orbit' WHERE LOWER(email)=%s",(FOUNDER_EMAIL,))
        c.commit()

@app.get("/")
@app.get("/health")
def health(): return {"ok":True,"service":"orbit-api","version":APP_VERSION}

@app.post("/api/auth/register")
def register(d:RegisterRequest):
    u=d.username.strip(); e=str(d.email).lower().strip()
    if not 3<=len(u)<=32: raise HTTPException(400,"Username must contain 3-32 characters")
    if len(d.password)<6: raise HTTPException(400,"Password must contain at least 6 characters")
    role="founder" if FOUNDER_EMAIL and e==FOUNDER_EMAIL else "user"; title="Creator of Orbit" if role=="founder" else "Explorer"
    try:
        with db() as c:
            with c.cursor() as x:
                x.execute("INSERT INTO users(username,email,password_hash,display_name,title,xp,profile_theme,role) VALUES(%s,%s,%s,%s,%s,0,'VOID',%s) RETURNING id,username,email,display_name,bio,title,xp,profile_theme,role,created_at",(u,e,pw_hash(d.password),u,title,role)); r=x.fetchone()
            c.commit()
    except psycopg.errors.UniqueViolation: raise HTTPException(409,"Username or email already exists")
    t=secrets.token_urlsafe(48)
    with db() as c:
        with c.cursor() as x: x.execute("INSERT INTO sessions(user_id,token_hash) VALUES(%s,%s)",(r[0],th(t)))
        c.commit()
    return {"ok":True,"token":t,"user":serialize(r)}

@app.post("/api/auth/login")
def login(d:LoginRequest):
    e=str(d.email).lower().strip()
    with db() as c:
        with c.cursor() as x: x.execute("SELECT id,username,email,display_name,bio,title,xp,profile_theme,role,password_hash,created_at FROM users WHERE email=%s LIMIT 1",(e,)); r=x.fetchone()
    if not r or not pw_verify(d.password,r[9]): raise HTTPException(401,"Invalid email or password")
    t=secrets.token_urlsafe(48)
    with db() as c:
        with c.cursor() as x: x.execute("INSERT INTO sessions(user_id,token_hash) VALUES(%s,%s)",(r[0],th(t)))
        c.commit()
    user={"id":r[0],"username":r[1],"email":r[2],"display_name":r[3] or r[1],"bio":r[4] or "","title":r[5] or "Explorer","xp":r[6] or 0,"profile_theme":r[7] or "VOID","role":r[8] or "user","created_at":r[10].isoformat()}
    return {"ok":True,"token":t,"user":user}

@app.get("/api/auth/session")
def session(authorization:str|None=Header(default=None)):
    r=current(bearer(authorization))
    if not r: raise HTTPException(401,"Session expired or invalid")
    return {"ok":True,"user":serialize(r)}

@app.patch("/api/profile")
def profile(d:ProfileUpdate,authorization:str|None=Header(default=None)):
    t=bearer(authorization); r=current(t)
    if not r: raise HTTPException(401,"Session expired or invalid")
    with db() as c:
        with c.cursor() as x: x.execute("UPDATE users SET display_name=%s,bio=%s,title=%s,profile_theme=%s WHERE id=%s",((d.display_name.strip() or r[1]),d.bio.strip()[:300],d.title.strip()[:64] or "Explorer",d.profile_theme.strip().upper()[:32],r[0]))
        c.commit()
    return {"ok":True,"user":serialize(current(t))}

@app.post("/api/auth/logout")
def logout(authorization:str|None=Header(default=None)):
    with db() as c:
        with c.cursor() as x: x.execute("DELETE FROM sessions WHERE token_hash=%s",(th(bearer(authorization)),))
        c.commit()
    return {"ok":True}
