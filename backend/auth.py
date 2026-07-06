"""
Módulo de autenticación JWT para EPG-UAC.
Usa python-jose para firmar tokens y passlib[bcrypt] para hashes de contraseñas.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import SessionLocal

# ── Configuración ──────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CAMBIA_ESTO_EN_PRODUCCION_CLAVE_INSEGURA")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 horas

# ── Herramientas criptográficas ────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Funciones de contraseña ────────────────────────────────────────────────────
def verificar_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


# ── Funciones de token JWT ─────────────────────────────────────────────────────
def crear_token_acceso(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Dependencia para rutas protegidas ──────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.UsuarioSistema:
    payload = decodificar_token(token)
    id_usuario: int = payload.get("sub")
    if id_usuario is None:
        raise HTTPException(status_code=401, detail="Token sin identificador de usuario")

    usuario = db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.id_usuario == int(id_usuario),
        models.UsuarioSistema.activo == True,
    ).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    return usuario


def get_current_admin(current_user: models.UsuarioSistema = Depends(get_current_user)):
    if current_user.rol != "Administrador":
        raise HTTPException(status_code=403, detail="Se requiere rol Administrador")
    return current_user


def get_current_directora_o_admin(current_user: models.UsuarioSistema = Depends(get_current_user)):
    if current_user.rol not in ("Administrador", "Directora"):
        raise HTTPException(status_code=403, detail="Se requiere rol Directora o Administrador")
    return current_user
