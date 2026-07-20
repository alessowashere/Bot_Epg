"""Reglas de contraseña y control de acceso durante el cambio obligatorio."""

from __future__ import annotations

import re
from datetime import datetime

from fastapi import HTTPException

from auth import hashear_password, verificar_password


RUTAS_PERMITIDAS_CAMBIO = {"/api/auth/me", "/api/auth/cambiar-password"}
PATRON_CAMBIO_PASSWORD_USUARIO = re.compile(r"^/api/usuarios/\d+/cambiar-password$")


def validar_nueva_password(password: str) -> None:
    if len(password) < 12:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 12 caracteres.")
    if not re.search(r"[a-z]", password):
        raise HTTPException(status_code=400, detail="La contraseña debe incluir una letra minúscula.")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="La contraseña debe incluir una letra mayúscula.")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="La contraseña debe incluir un número.")


def requiere_bloqueo_por_cambio(usuario, path: str, method: str) -> bool:
    if not getattr(usuario, "debe_cambiar_password", False):
        return False
    if path in RUTAS_PERMITIDAS_CAMBIO:
        return False
    return not (method.upper() == "PUT" and PATRON_CAMBIO_PASSWORD_USUARIO.match(path))


def cambiar_password_propia(usuario, password_actual: str | None, nueva_password: str) -> None:
    validar_nueva_password(nueva_password)
    if usuario.password_hash:
        if not password_actual or not verificar_password(password_actual, usuario.password_hash):
            raise HTTPException(status_code=400, detail="La contraseña actual no es correcta.")
        if verificar_password(nueva_password, usuario.password_hash):
            raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente de la actual.")
    usuario.password_hash = hashear_password(nueva_password)
    usuario.debe_cambiar_password = False
    usuario.fecha_cambio_password = datetime.utcnow()


def restablecer_password_por_admin(usuario, nueva_password: str) -> None:
    validar_nueva_password(nueva_password)
    usuario.password_hash = hashear_password(nueva_password)
    usuario.debe_cambiar_password = True
    usuario.fecha_cambio_password = None
