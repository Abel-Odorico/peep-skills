---
name: fastapi-auth
description: >
  Complete auth system for FastAPI: JWT + bcrypt login/register, forgot/reset-password
  email flow (antisnoop 202, 60min token, RFC headers), rate limiting, Alembic migrations
  alongside legacy DDL, and the gotchas that cause prod incidents.
  Use when building auth for any FastAPI project, or when asked about password reset, JWT,
  bcrypt, or email verification flows.
---

# FastAPI Auth

Production-grade auth: register, login, JWT, profile update, password change, forgot/reset password with email, rate limiting.

---

## Dependencies

```bash
pip install \
  fastapi \
  sqlalchemy \
  psycopg2-binary \
  python-jose[cryptography] \
  passlib[bcrypt] \
  python-multipart \        # ← REQUIRED for OAuth2PasswordRequestForm
  pydantic-settings \
  slowapi \                 # rate limiting
  httpx \                   # async email or webhook calls
  alembic
```

`python-multipart` is non-obvious — without it every `POST /auth/login` returns 422.

---

## Models

```python
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

def _utcnow():
    # datetime.utcnow() deprecated in Python 3.12+
    return datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC

class UserRole(enum.Enum):
    user = "user"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    name          = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(Enum(UserRole), default=UserRole.user)
    created_at    = Column(DateTime, default=_utcnow)
    updated_at    = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token      = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at    = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
```

---

## Auth utils

```python
from jose import JWTError, ExpiredSignatureError, jwt
from passlib.context import CryptContext
from datetime import timedelta
import secrets

SECRET_KEY = settings.secret_key     # from .env, long random string
ALGORITHM = "HS256"
EXPIRE_MINUTES = 10080               # 7 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: int) -> str:
    expire = _utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except ExpiredSignatureError:
        raise HTTPException(401, "Token expirado")
    except JWTError:
        raise HTTPException(401, "Token inválido")
    # ↑ Catch ExpiredSignatureError BEFORE JWTError — it's a subclass
```

---

## Dependency: get current user

```python
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)) -> User:
    user_id = decode_token(token)
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(401, "Usuário não encontrado")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(403, "Acesso negado")
    return user
```

---

## Register + Login

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/auth")
limiter = Limiter(key_func=get_remote_address)

@router.post("/register", status_code=201)
def register(data: RegisterRequest, db=Depends(get_db)):
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(400, "Email já cadastrado")
    user = User(
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id), "user": UserResponse.from_orm(user)}

@router.post("/login")
@limiter.limit("10/minute")          # rate limit by IP
def login(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db), request=None):
    user = db.query(User).filter_by(email=form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Credenciais inválidas")
    return {"access_token": create_token(user.id), "token_type": "bearer"}
```

---

## Forgot / Reset Password

The complete antisnoop flow: never reveal if an email exists.

```python
import secrets, uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
import smtplib, html

RESET_EXPIRE_MINUTES = 60
FRONTEND_URL = "https://yourapp.com"

@router.post("/forgot-password", status_code=202)
def forgot_password(data: ForgotRequest, background_tasks: BackgroundTasks, db=Depends(get_db)):
    # Always 202 — antisnoop: don't reveal if email exists
    user = db.query(User).filter_by(email=data.email).first()
    if user:
        # Delete previous unused tokens (avoid accumulation + race conditions)
        db.query(PasswordResetToken).filter_by(user_id=user.id, used_at=None).delete()
        token_str = secrets.token_urlsafe(48)   # 64 chars base64url
        db.add(PasswordResetToken(
            user_id=user.id,
            token=token_str,
            expires_at=_utcnow() + timedelta(minutes=RESET_EXPIRE_MINUTES),
        ))
        db.commit()
        background_tasks.add_task(send_reset_email, user.email, user.name, token_str)
    return {"message": "Se o email existir, você receberá as instruções."}

@router.get("/reset-password/validate")
def validate_reset_token(token: str, db=Depends(get_db)):
    row = db.query(PasswordResetToken).filter_by(token=token, used_at=None).first()
    if not row or row.expires_at < _utcnow():
        raise HTTPException(400, "Token inválido ou expirado")
    return {"valid": True}

@router.post("/reset-password")
def reset_password(data: ResetRequest, db=Depends(get_db)):
    row = db.query(PasswordResetToken).filter_by(token=data.token, used_at=None).first()
    if not row or row.expires_at < _utcnow():
        raise HTTPException(400, "Token inválido ou expirado")
    user = db.query(User).filter_by(id=row.user_id).first()
    user.password_hash = hash_password(data.new_password)
    row.used_at = _utcnow()
    db.commit()
    return {"message": "Senha redefinida com sucesso."}
```

---

## Email — RFC headers required for Gmail delivery

Missing `Date`, `Message-ID`, `Reply-To`, or `X-Mailer` → Gmail classifies as spam or rejects.

```python
def send_reset_email(to_email: str, name: str, token: str):
    reset_url = f"{FRONTEND_URL}/redefinir-senha?token={token}"
    name_safe = html.escape(name)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Redefinição de senha"
    msg["From"] = f"App <{settings.mail_from}>"
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=False)                    # ← required
    msg["Message-ID"] = make_msgid(domain="yourapp.com")         # ← required
    msg["Reply-To"] = settings.mail_from                         # ← required
    msg["X-Mailer"] = "YourApp/1.0"                              # ← required

    text = f"Acesse o link para redefinir sua senha:\n{reset_url}\n\nExpira em {RESET_EXPIRE_MINUTES} minutos."
    html_body = f"""
    <html><body style="font-family:sans-serif;background:#0d1b2a;color:#e2e8f0;padding:2rem">
      <h2>Redefinir senha</h2>
      <p>Olá, <strong>{name_safe}</strong>!</p>
      <a href="{reset_url}" style="background:#0f7a78;color:#fff;padding:12px 24px;
         border-radius:6px;text-decoration:none;display:inline-block">Redefinir Senha</a>
      <p style="color:#94a3b8;font-size:12px">Link expira em {RESET_EXPIRE_MINUTES} minutos.</p>
    </body></html>"""

    msg.attach(MIMEText(text, "plain"))        # text/plain FIRST
    msg.attach(MIMEText(html_body, "html"))    # text/html SECOND
    # multipart/alternative with both parts = critical for Gmail delivery

    with smtplib.SMTP(settings.mail_host, 587) as s:  # STARTTLS, not SSL
        s.starttls()
        s.login(settings.mail_username, settings.mail_password)
        s.send_message(msg)
```

**STARTTLS pattern:** `SMTP(host, 587)` + `starttls()` — do NOT use `SMTP_SSL(host, 587)`. SMTP_SSL on port 587 fails silently or with a confusing timeout.

---

## Alembic alongside legacy DDL

When migrating an existing project to Alembic while keeping old DDL migrations:

```python
# main.py — lifespan
from alembic.config import Config
from alembic import command

def _alembic_upgrade():
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

def _run_migrations(engine):
    # Legacy DDL — runs AFTER Alembic
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(60)"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS theme VARCHAR(10) DEFAULT 'system'"))
        conn.commit()

@asynccontextmanager
async def lifespan(app):
    _alembic_upgrade()    # ← FIRST: Alembic creates base tables
    _run_migrations(engine)  # ← SECOND: DDL adds columns Alembic doesn't know about
    yield
```

Migration path: move DDL one-by-one to Alembic migrations, remove from `_run_migrations()`, eventually delete the function.

---

## Gotchas

### 1. `python-multipart` missing → 422 on all login attempts

`OAuth2PasswordRequestForm` is form-encoded, not JSON. FastAPI needs `python-multipart` to parse form data. Without it, every `POST /auth/login` returns 422 with no clear error message.

### 2. `ExpiredSignatureError` must be caught before `JWTError`

`ExpiredSignatureError` is a subclass of `JWTError`. If you catch `JWTError` first, expired tokens return 401 "invalid token" instead of 401 "token expirado". Catch the specific subclass first:

```python
except ExpiredSignatureError:
    raise HTTPException(401, "Token expirado")
except JWTError:
    raise HTTPException(401, "Token inválido")
```

### 3. bcrypt rounds slow in tests

`bcrypt` with 12+ rounds takes ~500ms per hash. Test suites with 50+ users = minutes. Configure test env to use 4 rounds:

```python
# conftest.py
from passlib.context import CryptContext
import auth_utils
auth_utils.pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=4)
```

### 4. `unique=True` without `index=True` is slow on large tables

SQLAlchemy's `unique=True` creates a unique constraint but not necessarily an index in all databases. Add `index=True` on frequently queried columns:

```python
email = Column(String(255), unique=True, nullable=False, index=True)
```

### 5. Token delete-before-create prevents race condition

If two `POST /auth/forgot-password` arrive simultaneously, both would create tokens. One token would win the unique constraint, the other would fail. Delete first, then create — atomic within the transaction:

```python
db.query(PasswordResetToken).filter_by(user_id=user.id, used_at=None).delete()
db.add(PasswordResetToken(...))
db.commit()
```

### 6. `_utcnow()` — never `datetime.utcnow()` directly

`datetime.utcnow()` is deprecated since Python 3.12 and produces naive UTC datetimes. Use a helper:

```python
def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)
```

The `.replace(tzinfo=None)` keeps it naive (consistent with naive columns in PostgreSQL). Don't mix naive and aware datetimes in the same app.

---

## Checklist

- [ ] `python-multipart` in requirements (OAuth2PasswordRequestForm)
- [ ] `ExpiredSignatureError` caught before `JWTError`
- [ ] `_utcnow()` helper used everywhere (not `datetime.utcnow()`)
- [ ] Forgot-password deletes old tokens before creating new (race-safe)
- [ ] Always returns 202 on forgot-password (antisnoop)
- [ ] Email has `Date`, `Message-ID`, `Reply-To`, `X-Mailer` headers
- [ ] `multipart/alternative` with `text/plain` + `text/html` (both required for Gmail)
- [ ] SMTP uses STARTTLS on 587 (not SMTP_SSL)
- [ ] Rate limit on `/auth/login` (slowapi, 10/min per IP)
- [ ] `email` column has `index=True` (not just `unique=True`)
- [ ] Alembic runs before legacy DDL migrations in lifespan
- [ ] bcrypt rounds set to 4 in test configuration
