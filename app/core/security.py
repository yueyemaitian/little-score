import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import jwt

from app.core.config import get_settings


def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": datetime.now(timezone.utc) + expires_delta,
        "sub": str(subject),
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def _prepare_password_for_bcrypt(password: str) -> bytes:
    """
    处理密码长度限制：bcrypt 最多支持 72 字节
    如果密码超过 72 字节，先用 SHA256 哈希（返回 32 字节）
    这样可以保持安全性，同时避免长度限制
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # 如果超过 72 字节，先用 SHA256 哈希（返回 32 字节）
        sha256_hash = hashlib.sha256(password_bytes).digest()  # 使用 digest() 而不是 hexdigest()，返回 32 字节
        return sha256_hash
    return password_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码：需要处理可能被 SHA256 预处理过的密码
    """
    prepared_password = _prepare_password_for_bcrypt(plain_password)
    # bcrypt.checkpw 接受 bytes
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(prepared_password, hashed_bytes)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希：处理 bcrypt 的 72 字节限制
    """
    prepared_password = _prepare_password_for_bcrypt(password)
    # bcrypt.hashpw 接受 bytes，返回 bytes
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared_password, salt)
    return hashed.decode('utf-8')


