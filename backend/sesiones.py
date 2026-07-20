"""Sesiones revocables y ligadas a dispositivo para la API institucional."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException

import models
from auth import crear_token_acceso


TIPO_NORMAL = "normal"
TIPO_VISTA_ROL = "vista_rol"


def hash_dispositivo(dispositivo: str | None) -> str:
    if not dispositivo or len(dispositivo) < 20 or len(dispositivo) > 200:
        raise HTTPException(status_code=401, detail="Dispositivo de sesión no válido.")
    return hashlib.sha256(dispositivo.encode("utf-8")).hexdigest()


def revocar_sesiones(db, id_usuario, motivo, *, excluir_jti=None, tipo=None, id_administrador_origen=None):
    consulta = db.query(models.SesionUsuario).filter(
        models.SesionUsuario.id_usuario == id_usuario,
        models.SesionUsuario.activa == True,
    )
    if excluir_jti:
        consulta = consulta.filter(models.SesionUsuario.jti != excluir_jti)
    if tipo:
        consulta = consulta.filter(models.SesionUsuario.tipo == tipo)
    if id_administrador_origen is not None:
        consulta = consulta.filter(models.SesionUsuario.id_administrador_origen == id_administrador_origen)
    ahora = datetime.utcnow()
    return consulta.update(
        {
            models.SesionUsuario.activa: False,
            models.SesionUsuario.fecha_revocacion: ahora,
            models.SesionUsuario.motivo_revocacion: motivo,
        },
        synchronize_session=False,
    )


def iniciar_sesion(
    db,
    usuario,
    dispositivo,
    *,
    tipo=TIPO_NORMAL,
    minutos=480,
    administrador_origen=None,
    origen_autenticacion="local",
):
    """Crea token y registro de manera atómica; una cuenta conserva una sesión normal."""
    dispositivo_hash = hash_dispositivo(dispositivo)
    if tipo == TIPO_NORMAL:
        revocar_sesiones(db, usuario.id_usuario, "nuevo_inicio_sesion", tipo=TIPO_NORMAL)
    elif tipo == TIPO_VISTA_ROL and administrador_origen:
        revocar_sesiones(
            db,
            usuario.id_usuario,
            "nueva_vista_administrativa",
            tipo=TIPO_VISTA_ROL,
            id_administrador_origen=administrador_origen.id_usuario,
        )
    ahora = datetime.utcnow()
    jti = str(secrets.token_urlsafe(24))
    expiracion = ahora + timedelta(minutes=minutos)
    sesion = models.SesionUsuario(
        jti=jti,
        id_usuario=usuario.id_usuario,
        tipo=tipo,
        id_administrador_origen=administrador_origen.id_usuario if administrador_origen else None,
        dispositivo_hash=dispositivo_hash,
        fecha_creacion=ahora,
        fecha_expiracion=expiracion,
        fecha_ultimo_uso=ahora,
    )
    db.add(sesion)
    token = crear_token_acceso(
        {
            "sub": str(usuario.id_usuario),
            "nombre": usuario.nombre_completo,
            "rol": usuario.rol,
            "jti": jti,
            "tipo_sesion": tipo,
            "origen_autenticacion": origen_autenticacion,
            "modo_vista_rol": tipo == TIPO_VISTA_ROL,
            "administrador_origen": str(administrador_origen.id_usuario) if administrador_origen else None,
        },
        expires_delta=timedelta(minutes=minutos),
    )
    return token, sesion


def validar_sesion(db, payload, dispositivo):
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Sesión no válida; vuelve a iniciar sesión.")
    sesion = db.query(models.SesionUsuario).filter(models.SesionUsuario.jti == str(jti)).first()
    ahora = datetime.utcnow()
    if not sesion or not sesion.activa or sesion.fecha_expiracion <= ahora:
        raise HTTPException(status_code=401, detail="Sesión vencida o cerrada; vuelve a iniciar sesión.")
    if not secrets.compare_digest(sesion.dispositivo_hash, hash_dispositivo(dispositivo)):
        raise HTTPException(status_code=401, detail="Esta sesión pertenece a otro dispositivo.")
    if sesion.fecha_ultimo_uso <= ahora - timedelta(minutes=5):
        sesion.fecha_ultimo_uso = ahora
        db.commit()
    return sesion


def cerrar_sesion(db, jti, motivo="cierre_usuario"):
    sesion = db.query(models.SesionUsuario).filter(models.SesionUsuario.jti == str(jti)).first()
    if sesion and sesion.activa:
        sesion.activa = False
        sesion.fecha_revocacion = datetime.utcnow()
        sesion.motivo_revocacion = motivo
    return sesion
