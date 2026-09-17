import os
import secrets
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

ACCESS_TOKEN_EXPIRE_MINUTES = 30

if not SECRET_KEY or len(SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError("SECRET_KEY must contain at least 32 bytes.")

if ALGORITHM != "HS256":
    raise RuntimeError("This application expects ALGORITHM=HS256.")

if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
    raise RuntimeError(
        "Set ADMIN_USERNAME and ADMIN_PASSWORD_HASH."
    )

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def authenticate_admin(username: str, password: str) -> bool:
    # Verify the password even if the username is incorrect.
    password_valid = password_hash.verify(
        password,
        ADMIN_PASSWORD_HASH,
    )

    username_valid = secrets.compare_digest(
        username.encode("utf-8"),
        ADMIN_USERNAME.encode("utf-8"),
    )

    return username_valid and password_valid


def create_token(username: str) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_token(
    token: str = Depends(oauth2_scheme),
) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "require_exp": True,
                "require_sub": True,
            },
        )

        if payload.get("sub") != ADMIN_USERNAME:
            raise credentials_error

        return payload

    except JWTError:
        raise credentials_error
