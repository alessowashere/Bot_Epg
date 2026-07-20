import math
import calendar
import csv
import json
import os
import re
import hashlib
import hmac
import logging
import unicodedata
import uuid as uuid_lib
import zipfile
import subprocess
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from io import BytesIO
from pathlib import Path
from functools import lru_cache
from typing import Optional
from urllib.parse import quote, unquote, urlparse
from urllib.request import urlopen

from fastapi import BackgroundTasks, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from docx import Document
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload
from starlette.middleware.sessions import SessionMiddleware

try:
    from authlib.integrations.starlette_client import OAuth
except ImportError:  # La app continúa operativa mientras Google SSO esté desactivado.
    OAuth = None

import models
from identidad_academica import ascii_mayusculas, normalizar_codigo_matricula
from nombres import quitar_tratamientos
from auditar_identidades_academicas import clave_nombre, nombres_equivalentes
from auth import (
    LEGACY_PASSWORD_LOGIN_ENABLED,
    LEGACY_PASSWORD_RETIREMENT_DATE,
    crear_token_acceso,
    decodificar_token,
    get_current_admin,
    get_current_user,
    get_current_directora_o_admin,
    hashear_password,
    verificar_password,
)
from capacidades import METODOS_MUTABLES, obtener_politica, rutas_mutables_sin_politica
from database import SessionLocal, leer_env_local
from estado_bot import leer_estado_bot
from extractor import extraer_datos_cuerpo, extraer_todos_adjuntos, generar_resumen_ticket
from flujo_resoluciones import (
    ESTADOS_ACTIVOS,
    cambiar_estado as cambiar_estado_tramite,
    confirmar_notificacion as confirmar_notificacion_tramite,
    crear_consultas as crear_consultas_tramite,
    debe_cerrar_por_resolucion_cargada,
    derivar_a_secretaria,
    obtener_consulta_por_token,
    obtener_tramite,
    registrar_evento as registrar_evento_tramite,
    registrar_notificacion as registrar_notificacion_tramite,
    responder_consulta,
    serializar_consulta,
    serializar_notificacion,
    serializar_tramite,
    validar_consultas_segun_regla,
    validar_remision_direccion,
)
from generador_resoluciones import (
    construir_borrador,
    crear_docx_borrador,
    crear_docx_desde_plantilla_oficial,
    es_modelo_utilizable,
    hash_contenido,
    referencias_plantilla_oficial,
    serializar_modelo,
)
from mesa_tramite import (
    catalogo_tipos_resolucion,
    contexto_mesa_tramite,
    control_numeracion,
    es_documento_serie_epg_principal,
    inferir_paso_objetivo,
)
from outbox import (
    aprobar_solicitud,
    cancelar_solicitud,
    crear_solicitud,
    salidas_externas_habilitadas,
    serializar_solicitud,
)
from requisitos_catalogo import inicializar_requisitos_expediente
from reglas_resolucion import regla_aplicada, regla_vigente, serializar_regla, versionar_regla
from sesiones import TIPO_VISTA_ROL, cerrar_sesion, iniciar_sesion, revocar_sesiones, validar_sesion
from seguridad_passwords import (
    cambiar_password_propia,
    requiere_bloqueo_por_cambio,
    restablecer_password_por_admin,
)
from trazabilidad import (
    ROLES_AUTORIZACION,
    ROLES_OPERACION,
    actualizar_requisito,
    confirmar_resolucion,
    decision_actual as decision_actual_normalizada,
    descartar_resolucion,
    exigir_rol,
    proponer_resolucion,
    registrar_accion,
    registrar_decision,
    resumen_requisitos,
    serializar_accion,
    serializar_decision,
    serializar_requisito,
    serializar_ticket_resolucion,
    sincronizar_accion_legacy,
)


def expediente_visible_operativamente():
    """Excluye alias históricos creados al consolidar duplicados.

    El expediente secundario no se borra y puede consultarse por auditoría,
    pero no debe inflar tableros, listados ni alertas operativas.
    """
    return or_(
        models.ExpedienteTesis.sub_estado == None,
        ~models.ExpedienteTesis.sub_estado.like("Unificado en #%"),
    )


app = FastAPI(
    title="API Sistema de Posgrado UAC",
    description="Motor Backend para la gestion de expedientes de tesis - EPG UAC",
    version="3.0.0",
    root_path="/bot-posgrado",
)
logger = logging.getLogger("epg.seguridad")
ROOT = Path("/opt/sistema_posgrado")


def valor_configuracion(clave: str, defecto: str = "") -> str:
    return os.getenv(clave) or leer_env_local(clave) or defecto


ORIGENES_PERMITIDOS = [
    origen.strip()
    for origen in valor_configuracion("EPG_ALLOWED_ORIGINS").split(",")
    if origen.strip()
]
if not ORIGENES_PERMITIDOS:
    raise RuntimeError("EPG_ALLOWED_ORIGINS es obligatorio; no se permite CORS abierto en E1.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def configuracion_booleana(clave: str, defecto: bool = False) -> bool:
    return valor_configuracion(clave, str(defecto)).strip().lower() in {"1", "true", "si", "yes", "on"}


GOOGLE_OAUTH_HABILITADO = configuracion_booleana("EPG_GOOGLE_OAUTH_ENABLED")
GOOGLE_CLIENT_ID = valor_configuracion("EPG_GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = valor_configuracion("EPG_GOOGLE_CLIENT_SECRET")
GOOGLE_DOMINIO_PERMITIDO = valor_configuracion("EPG_GOOGLE_ALLOWED_DOMAIN", "uandina.edu.pe").lower()
GOOGLE_DRIVE_OWNER_EMAILS = {
    correo.strip().lower()
    for correo in valor_configuracion("EPG_GOOGLE_DRIVE_OWNER_EMAILS", valor_configuracion("EPG_GOOGLE_DRIVE_OWNER_EMAIL")).split(",")
    if correo.strip()
}
GOOGLE_OAUTH_SESSION_SECRET = valor_configuracion("EPG_OAUTH_SESSION_SECRET")
# La SPA vive en la raíz pública; `/bot-posgrado` es solamente el prefijo que
# Nginx entrega a FastAPI. Se conserva la forma antigua con el prefijo incluido
# para no romper instalaciones que ya copiaron la primera guía.
EPG_PUBLIC_BASE_URL = valor_configuracion("EPG_PUBLIC_BASE_URL", "https://dataepis.uandina.pe:49267").rstrip("/")
EPG_PUBLIC_API_PREFIX = valor_configuracion("EPG_PUBLIC_API_PREFIX", "/bot-posgrado").rstrip("/")
if EPG_PUBLIC_BASE_URL.endswith("/bot-posgrado"):
    EPG_PUBLIC_BASE_URL = EPG_PUBLIC_BASE_URL.removesuffix("/bot-posgrado")
    EPG_PUBLIC_API_PREFIX = "/bot-posgrado"

# OnlyOffice nunca expone un puerto propio: Nginx lo publica en /onlyoffice y
# el servidor de documentos sólo recibe enlaces firmados y de vida corta.
ONLYOFFICE_HABILITADO = configuracion_booleana("EPG_ONLYOFFICE_ENABLED")
ONLYOFFICE_URL_PUBLICA = valor_configuracion("EPG_ONLYOFFICE_PUBLIC_URL", f"{EPG_PUBLIC_BASE_URL}/onlyoffice").rstrip("/")
ONLYOFFICE_CALLBACK_BASE = valor_configuracion("EPG_ONLYOFFICE_CALLBACK_BASE_URL", "http://host.docker.internal:8000").rstrip("/")
ONLYOFFICE_JWT_SECRET = valor_configuracion("EPG_ONLYOFFICE_JWT_SECRET")
if ONLYOFFICE_HABILITADO and len(ONLYOFFICE_JWT_SECRET) < 32:
    raise RuntimeError("EPG_ONLYOFFICE_JWT_SECRET seguro es obligatorio para el editor Word.")

if GOOGLE_OAUTH_HABILITADO:
    if OAuth is None:
        raise RuntimeError("Instala Authlib para habilitar el acceso con Google Workspace.")
    if not all((GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_OAUTH_SESSION_SECRET)):
        raise RuntimeError("Falta configurar Google OAuth en backend/.env.")
    if not EPG_PUBLIC_BASE_URL.startswith("https://"):
        raise RuntimeError("EPG_PUBLIC_BASE_URL debe ser HTTPS para Google OAuth.")
    app.add_middleware(
        SessionMiddleware,
        secret_key=GOOGLE_OAUTH_SESSION_SECRET,
        same_site="lax",
        https_only=True,
        session_cookie="epg_google_oauth",
        max_age=600,
    )
    oauth_google = OAuth()
    oauth_google.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    oauth_google.register(
        name="drive_readonly",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile https://www.googleapis.com/auth/drive.readonly"},
    )
else:
    oauth_google = None


def crear_dependencia_capacidad(nombre: str, roles: frozenset[str]):
    def verificar_capacidad(current_user: models.UsuarioSistema = Depends(get_current_user)):
        if current_user.rol not in roles:
            raise HTTPException(status_code=403, detail=f"No tienes la capacidad {nombre}.")
        return current_user

    verificar_capacidad.__name__ = f"capacidad_{nombre.replace('.', '_')}"
    return verificar_capacidad


_agregar_ruta_original = app.router.add_api_route


def agregar_ruta_con_capacidad(path: str, endpoint, **kwargs):
    methods = set(kwargs.get("methods") or set())
    mutables = methods & METODOS_MUTABLES
    if mutables:
        politica = obtener_politica(path, mutables)
        if not politica:
            raise RuntimeError(f"Ruta mutable sin política de capacidad: {sorted(mutables)} {path}")
        if not politica.publico:
            dependencias = list(kwargs.get("dependencies") or [])
            dependencias.append(Depends(crear_dependencia_capacidad(politica.nombre, politica.roles)))
            kwargs["dependencies"] = dependencias
    return _agregar_ruta_original(path, endpoint, **kwargs)


# Todas las rutas registradas después de este punto quedan inventariadas y las
# mutables reciben su autorización centralizada antes de ejecutar el endpoint.
app.router.add_api_route = agregar_ruta_con_capacidad


PUBLIC_API_PREFIXES = (
    "/api/auth/login",
    "/api/auth/google/",
    "/api/dictaminante/",
    "/api/consultas-resolucion/",
    # El editor Word no conoce la sesión del navegador. Estas dos rutas se
    # protegen con una firma HMAC corta y el JWT propio de OnlyOffice.
    "/api/onlyoffice/",
)
PUBLIC_PATHS = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    # La protección final es el correo institucional validado en el callback.
    "/api/admin/integraciones/drive/conectar",
}


@app.middleware("http")
async def exigir_jwt_en_api(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS" or path in PUBLIC_PATHS or path.startswith(PUBLIC_API_PREFIXES):
        return await call_next(request)
    if not path.startswith("/api/"):
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "Token Bearer requerido"})

    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload = decodificar_token(token)
        id_usuario = int(payload.get("sub"))
    except (HTTPException, TypeError, ValueError) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else "Token inválido"
        return JSONResponse(status_code=401, content={"detail": detail})

    db = SessionLocal()
    try:
        usuario = db.query(models.UsuarioSistema).filter(
            models.UsuarioSistema.id_usuario == id_usuario,
            models.UsuarioSistema.activo == True,
        ).first()
        if not usuario:
            return JSONResponse(status_code=401, content={"detail": "Usuario no encontrado o inactivo"})
        try:
            sesion = validar_sesion(db, payload, request.headers.get("X-EPG-Device-ID"))
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        request.state.auth_payload = payload
        request.state.sesion_actual = sesion
        if payload.get("modo_vista_rol") and request.method in METODOS_MUTABLES:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "La vista por rol es solo de lectura.",
                    "code": "vista_rol_solo_lectura",
                },
            )
        if (
            not payload.get("modo_vista_rol")
            and payload.get("origen_autenticacion") != "google"
            and requiere_bloqueo_por_cambio(usuario, path, request.method)
        ):
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Debes cambiar tu contraseña antes de continuar.",
                    "code": "cambio_password_requerido",
                },
            )
    finally:
        db.close()

    response = await call_next(request)
    # Los tableros, colas y expedientes son datos operativos: nunca deben
    # reutilizar una respuesta anterior del navegador tras una conciliación.
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ActualizarRequisitoPayload(BaseModel):
    estado: Optional[str] = Field(None, description="Pendiente, Presentado, Validado, Observado o No_Aplica")
    evidencia_url: Optional[str] = None
    evidencia_nombre: Optional[str] = None
    fuente_evidencia: Optional[str] = None
    id_ticket: Optional[int] = None
    id_adjunto: Optional[int] = None
    observacion: Optional[str] = None


class CambiarPasswordPayload(BaseModel):
    password_actual: Optional[str] = Field(None, max_length=128)
    nueva_password: str = Field(..., min_length=1, max_length=128)


class ActualizarReglaResolucionPayload(BaseModel):
    estado_validacion: Optional[str] = None
    sistema_origen: Optional[str] = Field(None, max_length=100)
    requiere_resolucion_direccion: Optional[bool] = None
    requiere_consulta_previa: Optional[bool] = None
    tipos_participantes: Optional[list[str]] = None
    cantidad_aceptaciones: Optional[int] = Field(None, ge=0)
    destinatarios_obligatorios: Optional[list[str]] = None
    vigencia_meses: Optional[int] = Field(None, ge=1, le=120)
    plazo_consulta_dias: Optional[int] = Field(None, ge=1, le=365)
    modalidades_respuesta: Optional[list[str]] = None
    nota_validacion: Optional[str] = Field(None, max_length=2000)


class VistaRolPayload(BaseModel):
    id_usuario: int


class CrearOutboxPayload(BaseModel):
    target_system: str = Field(..., min_length=2, max_length=80)
    action_type: str = Field(..., min_length=2, max_length=120)
    subject_type: str = Field(..., min_length=2, max_length=80)
    subject_uuid: str = Field(..., min_length=1, max_length=36)
    idempotency_key: str = Field(..., min_length=8, max_length=190)
    payload: dict = Field(default_factory=dict)
    ticket_ref: Optional[str] = None
    expediente_ref: Optional[str] = None
    sustento: Optional[str] = Field(None, max_length=2000)
    borrador: bool = False


class TransicionOutboxPayload(BaseModel):
    sustento: Optional[str] = Field(None, max_length=2000)


class DerivarResolucionPayload(BaseModel):
    tipo_resolucion: str = Field(..., min_length=3, max_length=150)
    ticket_id: Optional[int] = None
    id_paso: Optional[int] = Field(None, ge=1, le=7)
    referencia_origen: Optional[str] = Field(None, max_length=150)


class PrepararDerivacionTicketPayload(BaseModel):
    id_paso: int = Field(..., ge=1, le=7)
    tipo_resolucion: str = Field(..., min_length=3, max_length=150)
    referencia_origen: Optional[str] = Field(None, max_length=150)
    nota: Optional[str] = Field(None, max_length=2000)
    confirmar_tramite_intermedio: bool = False


class AsignarArchivoRequisitoPayload(BaseModel):
    id_adjunto: int
    estado: str = Field("Presentado", pattern="^(Presentado|Validado|Observado)$")


class CrearExpedienteInicialPayload(BaseModel):
    id_paso: int = Field(..., ge=1, le=7)
    nombre_alumno: str = Field(..., min_length=3, max_length=150)
    codigo_alumno: str = Field(..., min_length=6, max_length=20)
    grado_postula: str = Field(..., pattern="^(Maestro|Doctor)$")
    programa: Optional[str] = Field(None, max_length=250)
    titulo_tesis: Optional[str] = Field(None, max_length=1000)
    nombre_asesor: Optional[str] = Field(None, max_length=150)
    nota: Optional[str] = Field(None, max_length=2000)


class RevisarTramitePayload(BaseModel):
    accion: str = Field(..., pattern="^(Aceptar|Observar)$")
    nota: Optional[str] = Field(None, max_length=2000)


class ParticipanteConsultaPayload(BaseModel):
    id_docente: int
    tipo_participacion: str = Field(..., min_length=3, max_length=50)
    canal_correo: str = Field("institucional", pattern="^(institucional|personal|ambos)$")


class CrearConsultasPayload(BaseModel):
    participantes: list[ParticipanteConsultaPayload] = Field(..., min_length=1, max_length=10)
    vigencia_dias: int = Field(..., ge=1, le=365)
    modalidad_respuesta: str = Field(..., pattern="^(Respuesta|Documento|Constancia)$")
    asunto: Optional[str] = Field(None, max_length=255)
    mensaje: Optional[str] = Field(None, max_length=5000)


class ConsultaPlantillaPayload(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=120)
    asunto: str = Field(..., min_length=3, max_length=255)
    mensaje: str = Field(..., min_length=20, max_length=5000)
    modalidad_respuesta: str = Field("Respuesta", pattern="^(Respuesta|Documento|Constancia)$")
    activa: bool = True


class GenerarBorradorOficialPayload(BaseModel):
    codigo_plantilla: str = Field(..., min_length=3, max_length=80)
    numero_resolucion: str = Field(..., min_length=6, max_length=50)
    fecha_resolucion: str
    referencia_origen: Optional[str] = Field(None, max_length=150)
    decision_numeracion: Optional[str] = Field(None, pattern="^(regular|no_emitida|archivo|anulada)$")
    nota_numeracion: Optional[str] = Field(None, max_length=1000)


class ResponderConsultaPayload(BaseModel):
    respuesta: str = Field(..., pattern="^(Aceptar|Rechazar)$")
    nota: Optional[str] = Field(None, max_length=2000)


class NotaTramitePayload(BaseModel):
    nota: str = Field(..., min_length=3, max_length=2000)


class RegistrarNotificacionPayload(BaseModel):
    destinatario_tipo: str = Field(..., min_length=3, max_length=40)
    destinatario_nombre: str = Field(..., min_length=3, max_length=180)
    destinatario_referencia: Optional[str] = Field(None, max_length=200)
    canal: str = Field(..., min_length=2, max_length=50)


class ConfirmarNotificacionPayload(BaseModel):
    evidencia: str = Field(..., min_length=3, max_length=2000)


class GenerarBorradorPayload(BaseModel):
    id_modelo_documento: int
    contenido: str = Field(..., min_length=120, max_length=50000)
    numero_resolucion: str = Field(..., min_length=3, max_length=50)
    fecha_resolucion: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    referencia_origen: Optional[str] = Field(None, max_length=150)


class GenerarBorradoresLotePayload(BaseModel):
    id_modelo_documento: int
    tramites: list[str] = Field(..., min_length=1, max_length=50)


class RemitirDireccionLotePayload(BaseModel):
    tramites: list[str] = Field(..., min_length=1, max_length=50)


class ResolverConciliacionPayload(BaseModel):
    accion: str = Field(..., pattern="^(confirmar_trayectoria|separar|mantener_legacy|mantener_sin_vinculo|archivar_historico|reactivar|mantener_activo|fuera_proceso|preparar_unificacion|mantener_separados|pendiente)$")
    clave_identidad: Optional[str] = Field(None, max_length=600)
    nota: Optional[str] = Field(None, max_length=2000)


def es_uuid(valor: str) -> bool:
    try:
        uuid_lib.UUID(str(valor))
        return True
    except ValueError:
        return False


def normalizar_texto_busqueda(valor: str | None) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    return re.sub(r"\s+", " ", texto).strip().upper()


def obtener_ticket_por_ref(db: Session, ticket_ref: str) -> models.TicketOsticket:
    query = db.query(models.TicketOsticket)
    ticket = query.filter(models.TicketOsticket.uuid == ticket_ref).first() if es_uuid(ticket_ref) else None
    if not ticket:
        try:
            ticket = query.filter(models.TicketOsticket.ticket_id == int(ticket_ref)).first()
        except ValueError:
            ticket = None
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


def obtener_expediente_por_ref(db: Session, expediente_ref: str) -> models.ExpedienteTesis:
    query = db.query(models.ExpedienteTesis)
    exp = query.filter(models.ExpedienteTesis.uuid == expediente_ref).first() if es_uuid(expediente_ref) else None
    if not exp:
        try:
            exp = query.filter(models.ExpedienteTesis.id_expediente == int(expediente_ref)).first()
        except ValueError:
            exp = None
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return exp


def obtener_outbox_por_uuid(db: Session, outbox_uuid: str) -> models.IntegrationOutbox:
    item = db.query(models.IntegrationOutbox).filter(models.IntegrationOutbox.uuid == outbox_uuid).first()
    if not item:
        raise HTTPException(status_code=404, detail="Solicitud de integración no encontrada")
    return item


def validar_payload_salida(payload: dict) -> None:
    """Evita persistir secretos o binarios en una cola de integración."""
    serializado = str(payload)
    if len(serializado) > 20_000:
        raise HTTPException(status_code=400, detail="El payload de salida excede el tamaño permitido.")

    def recorrer(valor):
        if isinstance(valor, dict):
            for clave, interno in valor.items():
                clave_normalizada = str(clave).lower()
                if any(fragmento in clave_normalizada for fragmento in ("password", "secret", "token", "credential", "clave")):
                    raise HTTPException(status_code=400, detail="El payload de salida no puede incluir secretos.")
                recorrer(interno)
        elif isinstance(valor, list):
            for interno in valor:
                recorrer(interno)
        elif isinstance(valor, (bytes, bytearray)):
            raise HTTPException(status_code=400, detail="El payload de salida no puede incluir binarios.")

    recorrer(payload)


def registrar_movimiento(db: Session, expediente, accion: str, nota: str | None, usuario_nombre: str | None = "Sistema"):
    db.add(
        models.HistorialMovimiento(
            id_expediente=expediente.id_expediente,
            id_paso=expediente.id_paso_actual,
            accion=accion,
            nota=nota,
            usuario_nombre=usuario_nombre,
        )
    )


def normalizar_codigo_alumno(valor: str | None) -> str | None:
    if not valor:
        return None
    texto = str(valor).strip()
    if "@" in texto:
        texto = texto.split("@", 1)[0]
    texto = re.sub(r"[^0-9A-Za-z]", "", texto).upper()
    if not re.fullmatch(r"\d{6,12}[A-Z]?", texto):
        return None
    return texto


def normalizar_nombre_persona(valor: str | None) -> str:
    texto = quitar_tratamientos(valor)
    texto = re.sub(r"^estudiante\.?\s+", "", texto, flags=re.IGNORECASE)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^A-Za-zÑñ\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip().upper()
    return texto


def resolver_docente_por_nombre(db: Session, nombre: str | None) -> tuple[models.Docente | None, dict]:
    """Encuentra un docente solo cuando la identidad es inequívoca.

    Las carátulas suelen omitir segundo nombre o usar iniciales; por eso se
    compara por tokens además del texto literal, sin crear docentes nuevos.
    """
    buscado = normalizar_nombre_persona(nombre)
    if not buscado:
        return None, {"estado": "sin_nombre"}
    tokens_buscados = set(buscado.split())
    candidatos = []
    for docente in db.query(models.Docente).filter(models.Docente.estado == "Activo").all():
        candidato = normalizar_nombre_persona(docente.nombre_completo)
        if not candidato:
            continue
        if candidato == buscado:
            puntaje, criterio = 100, "nombre_exacto"
        else:
            tokens_candidato = set(candidato.split())
            cobertura = len(tokens_buscados & tokens_candidato) / max(1, len(tokens_buscados))
            similitud = SequenceMatcher(None, buscado, candidato).ratio()
            if len(tokens_buscados) >= 2 and tokens_buscados.issubset(tokens_candidato):
                puntaje, criterio = 96, "tokens_contenidos"
            else:
                puntaje, criterio = round((cobertura * 0.7 + similitud * 0.3) * 100), "similitud_tokens"
        candidatos.append((puntaje, docente, criterio))
    candidatos.sort(key=lambda item: (-item[0], item[1].nombre_completo))
    if not candidatos:
        return None, {"estado": "sin_catalogo", "nombre_detectado": nombre}
    puntaje, docente, criterio = candidatos[0]
    segundo = candidatos[1][0] if len(candidatos) > 1 else 0
    if puntaje >= 92 and puntaje - segundo >= 4:
        return docente, {
            "estado": "coincidencia_confiable",
            "criterio": criterio,
            "puntaje": puntaje,
            "nombre_detectado": nombre,
            "nombre_catalogo": docente.nombre_completo,
        }
    return None, {
        "estado": "requiere_revision",
        "nombre_detectado": nombre,
        "mejor_sugerencia": docente.nombre_completo,
        "puntaje": puntaje,
        "ambigua": segundo >= puntaje - 3,
    }


def expresion_json_texto(ruta: str):
    return func.json_unquote(func.json_extract(models.TicketOsticket.datos_extraidos, ruta))


def decision_actual_ticket(ticket) -> dict:
    return decision_actual_normalizada(ticket)


def paso_sugerido_ticket(ticket) -> dict:
    datos = ticket.datos_extraidos or {}
    resumen = datos.get("resumen") or {}
    estructurados = datos.get("datos_estructurados") or {}
    paso = resumen.get("paso_sugerido") or estructurados.get("paso_sugerido") or {}
    return paso if isinstance(paso, dict) else {}


@lru_cache(maxsize=1)
def indice_referencias_historicas() -> dict[str, dict[str, list[dict]]]:
    """Índice secundario: orienta al usuario, nunca vincula expedientes por sí solo."""
    ruta = Path("/opt/sistema_posgrado/data/historico/referencias_historicas.csv")
    indice = {"codigo": {}, "nombre": {}}
    if not ruta.exists():
        return indice
    with ruta.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            codigo = normalizar_codigo_alumno(fila.get("codigo_alumno"))
            nombre = normalizar_nombre_persona(fila.get("nombre_alumno"))
            if codigo:
                indice["codigo"].setdefault(codigo, []).append(fila)
            if nombre:
                indice["nombre"].setdefault(nombre, []).append(fila)
    return indice


def sugerencias_historicas_ticket(ticket) -> list[dict]:
    indice = indice_referencias_historicas()
    codigo = normalizar_codigo_alumno(ticket.codigo_alumno_osticket)
    nombre = normalizar_nombre_persona(ticket.nombre_estudiante_osticket)
    coincidencias = indice["codigo"].get(codigo, []) if codigo else []
    criterio = "codigo_exacto" if coincidencias else ""
    if not coincidencias and nombre:
        coincidencias = indice["nombre"].get(nombre, [])
        criterio = "nombre_exacto" if coincidencias else ""
    resultado = []
    vistos = set()
    for fila in coincidencias:
        clave = (fila.get("resolucion"), fila.get("fuente"), fila.get("hoja"), fila.get("fila"))
        if clave in vistos:
            continue
        vistos.add(clave)
        resultado.append(
            {
                "criterio": criterio,
                "resolucion": fila.get("resolucion") or "Sin número registrado",
                "fecha": fila.get("fecha"),
                "tipo": fila.get("tipo"),
                "paso_sugerido": fila.get("paso_sugerido"),
                "ticket_o_expediente": fila.get("ticket_o_expediente"),
                "fuente": fila.get("fuente"),
                "hoja": fila.get("hoja"),
                "fila": fila.get("fila"),
            }
        )
        if len(resultado) >= 12:
            break
    return resultado


def tramite_activo_del_ticket(db: Session, ticket):
    """Devuelve el trámite institucional pendiente asociado al ticket, si existe."""
    return (
        db.query(models.ResolucionTramite)
        .filter(
            models.ResolucionTramite.ticket_id == ticket.ticket_id,
            models.ResolucionTramite.estado.in_(ESTADOS_ACTIVOS),
        )
        .order_by(models.ResolucionTramite.fecha_actualizacion.desc())
        .first()
    )


def enviar_ticket_a_secretaria(
    db: Session,
    ticket,
    actor,
    id_paso: int | None = None,
    tipo_resolucion: str | None = None,
    referencia_origen: str | None = None,
    confirmar_tramite_intermedio: bool = False,
):
    """Deriva desde el ticket usando su evidencia, no el paso legado del expediente."""
    if not ticket.id_expediente or any(item.estado == "confirmada" for item in ticket.resoluciones_ticket):
        return None, False

    existente = tramite_activo_del_ticket(db, ticket)
    if existente:
        return existente, False

    expediente = ticket.expediente or db.query(models.ExpedienteTesis).filter(
        models.ExpedienteTesis.id_expediente == ticket.id_expediente
    ).first()
    if not expediente:
        return None, False

    inferencia = inferir_paso_objetivo(db, ticket)
    paso_objetivo = int(id_paso or inferencia["id_paso"])
    if inferencia["tramite_intermedio"] and not confirmar_tramite_intermedio:
        raise HTTPException(
            status_code=409,
            detail="El ticket parece un trámite intermedio sin resolución. Confirma expresamente si debe generar una resolución.",
        )
    regla = regla_vigente(db, paso_objetivo)
    tipo = (tipo_resolucion or catalogo_tipos_resolucion()[(paso_objetivo - 1) * 2]["nombre"]).strip()
    tramite, creado = derivar_a_secretaria(
        db,
        expediente,
        actor,
        tipo,
        ticket,
        referencia_origen,
        regla,
        id_paso=paso_objetivo,
    )
    expediente.sub_estado = "Derivado_Secretaria"
    expediente.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(
        db,
        expediente,
        "Derivado",
        f"Ticket #{ticket.numero_visual} clasificado como P{paso_objetivo} y enviado a Secretaría Académica.",
        actor.nombre_completo,
    )
    agregar_accion_local(
        ticket,
        "enviado_secretaria_automaticamente",
        actor.nombre_completo,
        f"Trámite {tramite.uuid} creado desde la decisión operativa.",
        id_tramite=tramite.id_tramite,
        id_paso=paso_objetivo,
        inferencia=inferencia,
    )
    return tramite, creado


def situacion_operativa_ticket(ticket) -> str:
    if any(relacion.estado == "confirmada" for relacion in ticket.resoluciones_ticket):
        return "atendido_con_resolucion"
    decision = decision_actual_ticket(ticket).get("decision")
    if decision == "resolucion_notificada":
        return "atendido_con_resolucion"
    if decision in {"no_corresponde", "cerrar_interno"}:
        return "fuera_proceso"
    if decision == "transferir":
        return "pendiente_transferencia"
    if int((paso_sugerido_ticket(ticket) or {}).get("id_paso") or 0) in {4, 7}:
        return "canal_erp"
    # El trámite activo tiene prioridad sobre la etiqueta de clasificación:
    # desde aquí el trabajo ya pertenece a Secretaría/Dirección, no al tramitador.
    if ticket.id_expediente and any(
        item.ticket_id == ticket.ticket_id and item.estado in ESTADOS_ACTIVOS
        for item in ticket.expediente.tramites_resolucion
    ):
        return "en_tramite_resolucion"
    if decision == "requiere_resolucion":
        return "requiere_resolucion"
    if ticket.estado_scraping == "Error":
        return "error_extraccion"
    if ticket.estado_scraping in {"Pendiente_Descarga", "Archivos_Descargados"}:
        return "pendiente_adjuntos"
    if ticket.id_expediente and ticket.estado_scraping != "Notificado":
        return "por_clasificar"
    if not ticket.id_expediente:
        return "sin_expediente"
    return "atendido"


def agregar_accion_local(ticket, accion: str, usuario: str | None, nota: str | None = None, **detalle):
    datos = dict(ticket.datos_extraidos or {})
    acciones = list(datos.get("acciones_locales") or [])
    item = {
        "accion": accion,
        "usuario": usuario or "Sistema",
        "nota": nota,
        "fecha": datetime.utcnow().isoformat(),
        **detalle,
    }
    acciones.append(item)
    datos["acciones_locales"] = acciones
    ticket.datos_extraidos = datos
    return item


def parsear_fecha_filtro(valor: str | None, nombre: str, fin_dia: bool = False):
    if not valor:
        return None
    try:
        fecha = datetime.strptime(valor, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"{nombre} debe tener formato AAAA-MM-DD") from exc
    return fecha.replace(hour=23, minute=59, second=59) if fin_dia else fecha


def buscar_candidatos_expediente(db: Session, ticket, limite: int = 6) -> list[dict]:
    datos = ticket.datos_extraidos or {}
    estructurados = datos.get("datos_estructurados") or {}
    caratula = estructurados.get("caratula") or {}
    codigo = normalizar_codigo_alumno(
        ticket.codigo_alumno_osticket
        or estructurados.get("codigo_alumno")
        or (datos.get("vinculacion") or {}).get("codigo_detectado")
    )
    nombre = normalizar_nombre_persona(
        ticket.nombre_estudiante_osticket
        or caratula.get("nombre_alumno")
        or (datos.get("vinculacion") or {}).get("nombre_detectado")
    )
    if not codigo and not nombre:
        return []

    candidatos = []
    for exp in db.query(models.ExpedienteTesis).all():
        codigo_exp = normalizar_codigo_alumno(exp.codigo_alumno)
        nombre_exp = normalizar_nombre_persona(exp.nombre_alumno)
        puntaje_codigo = 100 if codigo and codigo == codigo_exp else 0
        puntaje_nombre = int(SequenceMatcher(None, nombre, nombre_exp).ratio() * 100) if nombre and nombre_exp else 0
        puntaje = max(puntaje_codigo, puntaje_nombre)
        if puntaje_codigo == 100 or puntaje_nombre >= 58:
            candidatos.append(
                {
                    **serializar_expediente_lista(exp),
                    "puntaje": puntaje,
                    "criterio": "codigo_exacto" if puntaje_codigo == 100 else "nombre_similar",
                }
            )
    return sorted(candidatos, key=lambda item: (-item["puntaje"], item["nombre_alumno"]))[:limite]


def vincular_ticket_existente(
    db: Session,
    ticket,
    expediente,
    usuario_nombre: str | None,
    criterio: str,
    nota: str | None = None,
    id_paso_historial: int | None = None,
):
    if ticket.id_expediente and ticket.id_expediente != expediente.id_expediente:
        raise HTTPException(
            status_code=409,
            detail="El ticket ya esta vinculado a otro expediente. Desvinculalo primero de forma explicita.",
        )
    datos = dict(ticket.datos_extraidos or {})
    datos["vinculacion"] = {
        "id_expediente": expediente.id_expediente,
        "uuid": expediente.uuid,
        "criterio": criterio,
        "estado": "vinculado_manual",
        "fecha": datetime.utcnow().isoformat(),
        "usuario": usuario_nombre,
    }
    ticket.datos_extraidos = datos
    ticket.id_expediente = expediente.id_expediente
    ticket.estado_scraping = "Clasificado"
    agregar_accion_local(
        ticket,
        "vinculado_expediente",
        usuario_nombre,
        nota,
        id_expediente=expediente.id_expediente,
        criterio=criterio,
    )
    db.add(
        models.HistorialMovimiento(
            id_expediente=expediente.id_expediente,
            id_paso=id_paso_historial or expediente.id_paso_actual,
            accion="Clasificado",
            nota=nota or f"Ticket #{ticket.numero_visual} vinculado manualmente ({criterio}).",
            usuario_nombre=usuario_nombre or "Sistema",
        )
    )


def buscar_expediente_existente(db: Session, codigo: str | None = None, nombre: str | None = None):
    codigo_norm = normalizar_codigo_alumno(codigo)
    if codigo_norm:
        exp = (
            db.query(models.ExpedienteTesis)
            .filter(func.upper(models.ExpedienteTesis.codigo_alumno) == codigo_norm)
            .order_by(models.ExpedienteTesis.id_expediente.desc())
            .first()
        )
        if exp:
            return exp, "codigo"

    nombre_norm = normalizar_nombre_persona(nombre)
    if nombre_norm:
        candidatos = db.query(models.ExpedienteTesis).all()
        coincidencias = [exp for exp in candidatos if normalizar_nombre_persona(exp.nombre_alumno) == nombre_norm]
        if len(coincidencias) == 1:
            return coincidencias[0], "nombre"

    return None, None


def paginar(query, page: int, per_page: int):
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, math.ceil(total / per_page)) if total else 1
    return total, total_pages, items


def serializar_adjunto(adj):
    return {
        "id_archivo": adj.id_adjunto,
        "nombre": adj.nombre_archivo,
        "url_visor": adj.ruta_local,
        "ruta_local": adj.ruta_local,
        "api_archivo_url": f"/tickets/{adj.ticket.uuid}/adjuntos/{adj.id_adjunto}/archivo" if adj.ticket else None,
        "nombre_archivo": adj.nombre_archivo,
    }


def ruta_local_segura_adjunto(adjunto: models.TicketAdjunto) -> Path:
    """Resuelve URLs históricas de adjuntos sin depender del host público."""
    raiz = Path("/opt/sistema_posgrado/uploads/expedientes").resolve()
    valor = (adjunto.ruta_local or "").strip()
    if not valor:
        raise HTTPException(status_code=404, detail="El adjunto no tiene una ruta registrada.")

    candidato = Path(valor)
    if candidato.is_absolute() and candidato.exists():
        ruta = candidato.resolve()
    else:
        path_url = unquote(urlparse(valor).path) if valor.startswith(("http://", "https://")) else unquote(valor)
        marcador = "/expedientes/"
        if marcador in path_url:
            relativa = path_url.split(marcador, 1)[1]
        else:
            relativa = path_url.lstrip("/")
        ruta = (raiz / relativa).resolve()

    if ruta != raiz and raiz not in ruta.parents:
        raise HTTPException(status_code=403, detail="Ruta de adjunto no permitida.")
    if not ruta.is_file():
        raise HTTPException(status_code=404, detail="El archivo no está disponible en el servidor.")
    return ruta


def serializar_ticket(ticket, detalle=False):
    expediente_uuid = ticket.expediente.uuid if ticket.expediente else None
    datos_extraidos = ticket.datos_extraidos or {}
    datos_lista = {
        "decision_actual": datos_extraidos.get("decision_actual"),
        "vinculacion": datos_extraidos.get("vinculacion"),
        "paso_sugerido": paso_sugerido_ticket(ticket),
    }
    data = {
        "ticket_id": ticket.ticket_id,
        "uuid": ticket.uuid,
        "numero_visual": ticket.numero_visual,
        "asunto": ticket.asunto,
        "estado": ticket.estado_scraping,
        "id_expediente": ticket.id_expediente,
        "expediente_uuid": expediente_uuid,
        "nombre_estudiante_osticket": ticket.nombre_estudiante_osticket,
        "email_estudiante": ticket.email_estudiante,
        "codigo_alumno_osticket": ticket.codigo_alumno_osticket,
        "fecha": ticket.fecha_creacion_osticket.strftime("%Y-%m-%d %H:%M:%S") if ticket.fecha_creacion_osticket else None,
        "adjuntos": [serializar_adjunto(adj) for adj in ticket.adjuntos],
        "adjuntos_count": len(ticket.adjuntos),
        "datos_extraidos": datos_extraidos if detalle else datos_lista,
        "decision_actual": decision_actual_ticket(ticket),
        "paso_sugerido": paso_sugerido_ticket(ticket),
        "situacion_operativa": situacion_operativa_ticket(ticket),
    }
    if detalle:
        data.update(
            {
                "cuerpo": ticket.cuerpo,
                "fecha_extraccion": ticket.fecha_extraccion.strftime("%Y-%m-%d %H:%M:%S")
                if ticket.fecha_extraccion
                else None,
            }
        )
    return data


def serializar_expediente_lista(exp):
    paso = exp.paso_actual
    return {
        "id_expediente": exp.id_expediente,
        "uuid": exp.uuid,
        "codigo_alumno": exp.codigo_alumno,
        "nombre_alumno": exp.nombre_alumno,
        "grado_postula": exp.grado_postula,
        "programa": exp.programa,
        "titulo_tesis": exp.titulo_tesis,
        "id_paso_actual": exp.id_paso_actual,
        "nombre_paso_actual": paso.nombre_paso if paso else "Desconocido",
        "estado_expediente": exp.estado_expediente,
        "sub_estado": exp.sub_estado,
        "fecha_inicio": exp.fecha_inicio_tramite.strftime("%Y-%m-%d") if exp.fecha_inicio_tramite else None,
        "fecha_ultimo_movimiento": exp.fecha_ultimo_movimiento.strftime("%Y-%m-%d") if exp.fecha_ultimo_movimiento else None,
    }


def serializar_expediente_detalle(db: Session, exp):
    historial = []
    for mov in exp.historial:
        historial.append(
            {
                "id_movimiento": mov.id_movimiento,
                "accion": mov.accion,
                "nota": mov.nota,
                "usuario_nombre": mov.usuario_nombre,
                "fecha": mov.fecha_movimiento.strftime("%Y-%m-%d %H:%M:%S"),
                "nombre_paso": mov.paso.nombre_paso if mov.paso else None,
                "id_paso": mov.id_paso,
            }
        )

    tickets = db.query(models.TicketOsticket).filter(models.TicketOsticket.id_expediente == exp.id_expediente).all()
    tickets_data = [
        {
            "ticket_id": t.ticket_id,
            "uuid": t.uuid,
            "numero_visual": t.numero_visual,
            "asunto": t.asunto,
            "fecha": t.fecha_creacion_osticket.strftime("%Y-%m-%d") if t.fecha_creacion_osticket else None,
            "adjuntos_count": len(t.adjuntos),
            "datos_extraidos": t.datos_extraidos or {},
            "decision_actual": decision_actual_ticket(t),
            "situacion_operativa": situacion_operativa_ticket(t),
            "resoluciones_ticket": [serializar_ticket_resolucion(r) for r in t.resoluciones_ticket],
        }
        for t in tickets
    ]

    asignaciones = []
    for asig in exp.asignaciones:
        aceptacion = asig.aceptacion
        asignaciones.append(
            {
                "id_asignacion": asig.id_asignacion,
                "rol_asignado": asig.rol_asignado,
                "estado_asignacion": asig.estado_asignacion,
                "id_docente": asig.id_docente,
                "nombre_docente": asig.docente.nombre_completo if asig.docente else "Desconocido",
                "correo_docente": asig.docente.correo if asig.docente else None,
                "especialidad": asig.docente.especialidad if asig.docente else "",
                "aceptacion": {
                    "id_aceptacion": aceptacion.id_aceptacion,
                    "estado_aceptacion": aceptacion.estado_aceptacion,
                    "nota": aceptacion.nota,
                    "fecha_respuesta": aceptacion.fecha_respuesta.strftime("%Y-%m-%d %H:%M:%S")
                    if aceptacion.fecha_respuesta
                    else None,
                }
                if aceptacion
                else None,
            }
        )

    resoluciones = (
        db.query(models.ResolucionFirma)
        .filter(models.ResolucionFirma.id_expediente == exp.id_expediente)
        .order_by(models.ResolucionFirma.fecha_solicitud.desc())
        .all()
    )

    data = serializar_expediente_lista(exp)
    data.update(
        {
            "fecha_inicio": exp.fecha_inicio_tramite.strftime("%Y-%m-%d %H:%M:%S") if exp.fecha_inicio_tramite else None,
            "fecha_ultimo_movimiento": exp.fecha_ultimo_movimiento.strftime("%Y-%m-%d %H:%M:%S")
            if exp.fecha_ultimo_movimiento
            else None,
            "carpeta_drive_url": exp.carpeta_drive_url,
            "historial": historial,
            "tickets": tickets_data,
            "asignaciones": asignaciones,
            "requisitos": [serializar_requisito(item) for item in exp.requisitos],
            "resumen_requisitos": resumen_requisitos(exp),
            "resoluciones": [
                {
                    "id_resolucion": r.id_resolucion,
                    "id_paso_asociado": r.id_paso_asociado,
                    "tipo_documento": r.tipo_documento,
                    "archivo_drive_url": r.archivo_drive_url,
                    "archivo_historico": bool(r.archivo_drive_url and not re.match(r"^https?://", r.archivo_drive_url, flags=re.I)),
                    "estado_firma": r.estado_firma,
                    "fecha_solicitud": r.fecha_solicitud.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_solicitud else None,
                    "fecha_firma": r.fecha_firma.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_firma else None,
                }
                for r in resoluciones
            ],
            "tramites_resolucion": [
                serializar_tramite(tramite, detalle=True)
                for tramite in reversed(exp.tramites_resolucion)
            ],
        }
    )
    return data


def resoluciones_relacionadas_ticket(db: Session, ticket) -> list[dict]:
    if not ticket.expediente:
        return []

    exp = ticket.expediente
    relacionadas = []
    firmas = (
        db.query(models.ResolucionFirma)
        .filter(models.ResolucionFirma.id_expediente == exp.id_expediente)
        .order_by(models.ResolucionFirma.fecha_firma.desc(), models.ResolucionFirma.id_resolucion.desc())
        .limit(20)
        .all()
    )
    for resolucion in firmas:
        relacionadas.append(
            {
                "ref": f"firma:{resolucion.id_resolucion}",
                "origen": "expediente",
                "numero": resolucion.tipo_documento or f"Resolucion #{resolucion.id_resolucion}",
                "tipo": resolucion.tipo_documento,
                "paso": resolucion.id_paso_asociado,
                "estado": resolucion.estado_firma,
                "fecha": (resolucion.fecha_firma or resolucion.fecha_solicitud).isoformat()
                if (resolucion.fecha_firma or resolucion.fecha_solicitud)
                else None,
                "archivo_url": resolucion.archivo_drive_url,
                "id_resolucion": resolucion.id_resolucion,
                "archivo_historico": bool(resolucion.archivo_drive_url and not re.match(r"^https?://", resolucion.archivo_drive_url, flags=re.I)),
            }
        )

    codigo = (exp.codigo_alumno or "").strip()
    nombre = (exp.nombre_alumno or "").strip()
    documentos = (
        db.query(models.ResolucionDocumento)
        .filter(
            or_(
                func.upper(models.ResolucionDocumento.codigo_alumno) == codigo.upper(),
                func.upper(models.ResolucionDocumento.nombre_alumno) == nombre.upper(),
            )
        )
        .order_by(models.ResolucionDocumento.fecha_resolucion.desc(), models.ResolucionDocumento.id_documento.desc())
        .limit(20)
        .all()
    )
    referencias = {item["ref"] for item in relacionadas}
    for documento in documentos:
        ref = f"documento:{documento.id_documento}"
        if ref in referencias:
            continue
        numero = documento.resolucion_numero or "S/N"
        if documento.resolucion_anio:
            numero = f"{numero}-{documento.resolucion_anio}"
        relacionadas.append(
            {
                "ref": ref,
                "origen": "staging",
                "numero": numero,
                "tipo": documento.tipo_resolucion,
                "paso": documento.id_paso_inferido,
                "estado": documento.estado_revision,
                "fecha": documento.fecha_resolucion.isoformat() if documento.fecha_resolucion else None,
                "archivo_url": None,
                "source_path": documento.source_path,
            }
        )
    estados_ticket = {relacion.referencia: relacion for relacion in ticket.resoluciones_ticket}
    for resolucion in relacionadas:
        relacion = estados_ticket.get(resolucion["ref"])
        if relacion:
            resolucion["relacion_ticket"] = serializar_ticket_resolucion(relacion)
    return relacionadas


def serializar_ticket_detalle_operativo(db: Session, ticket) -> dict:
    data = serializar_ticket(ticket, detalle=True)
    datos = ticket.datos_extraidos or {}
    eventos = []
    if ticket.decisiones_normalizadas:
        eventos.extend({"tipo": "decision", **serializar_decision(decision)} for decision in ticket.decisiones_normalizadas)
    else:
        eventos.extend({"tipo": "decision", **decision} for decision in datos.get("decisiones") or [])
    if ticket.acciones_normalizadas:
        eventos.extend({"tipo": "accion", **serializar_accion(accion)} for accion in ticket.acciones_normalizadas)
    else:
        eventos.extend({"tipo": "accion", **accion} for accion in datos.get("acciones_locales") or [])
    for mensaje in datos.get("mensajes_locales") or []:
        eventos.append(
            {
                "tipo": "mensaje",
                "accion": mensaje.get("tipo"),
                "nota": mensaje.get("mensaje"),
                "usuario": mensaje.get("usuario"),
                "fecha": mensaje.get("fecha"),
            }
        )
    eventos.sort(key=lambda item: item.get("fecha") or "", reverse=True)

    data.update(
        {
            "expediente": serializar_expediente_lista(ticket.expediente) if ticket.expediente else None,
            "posibles_expedientes": [] if ticket.expediente else buscar_candidatos_expediente(db, ticket),
            "antecedentes_historicos": [] if ticket.expediente else sugerencias_historicas_ticket(ticket),
            "resoluciones_relacionadas": resoluciones_relacionadas_ticket(db, ticket),
            "resolucion_ticket_confirmada": next(
                (serializar_ticket_resolucion(relacion) for relacion in ticket.resoluciones_ticket if relacion.estado == "confirmada"),
                datos.get("resolucion_ticket_confirmada"),
            ),
            "trazabilidad": {
                "decisiones": [serializar_decision(item) for item in ticket.decisiones_normalizadas],
                "acciones": [serializar_accion(item) for item in ticket.acciones_normalizadas],
                "resoluciones": [serializar_ticket_resolucion(item) for item in ticket.resoluciones_ticket],
            },
            "historial_acciones": eventos,
            "cierre_local_confirmado": ticket.estado_scraping == "Notificado",
        }
    )
    return data


def validar_resolucion_relacionada(db: Session, ticket, referencia: str | None) -> dict:
    if not referencia:
        raise HTTPException(
            status_code=400,
            detail="Selecciona la resolucion que fue cargada o notificada para este ticket.",
        )
    for resolucion in resoluciones_relacionadas_ticket(db, ticket):
        if resolucion["ref"] == referencia:
            return resolucion
    raise HTTPException(status_code=400, detail="La resolucion seleccionada no pertenece al expediente vinculado.")


def ejecutar_extraccion(db: Session, ticket: models.TicketOsticket):
    datos_previos = dict(ticket.datos_extraidos or {})
    claves_operativas = {
        clave: datos_previos[clave]
        for clave in (
            "decisiones",
            "decision_actual",
            "mensajes_locales",
            "acciones_locales",
            "resolucion_ticket_confirmada",
            "vinculacion",
        )
        if clave in datos_previos
    }
    datos_cuerpo = extraer_datos_cuerpo(ticket.cuerpo or "")
    adjuntos_list = [{"nombre_archivo": adj.nombre_archivo, "ruta_local": adj.ruta_local} for adj in ticket.adjuntos]
    resultado_adjuntos = extraer_todos_adjuntos(adjuntos_list)
    datos_fusionados = {**resultado_adjuntos["datos_extraidos_pdfs"], **datos_cuerpo}

    if ticket.nombre_estudiante_osticket:
        datos_fusionados.setdefault("nombre_osticket", ticket.nombre_estudiante_osticket)
    if ticket.email_estudiante:
        datos_fusionados.setdefault("email_osticket", ticket.email_estudiante)
    if ticket.codigo_alumno_osticket:
        datos_fusionados.setdefault("codigo_alumno", ticket.codigo_alumno_osticket)

    resumen = generar_resumen_ticket(ticket.asunto or "", ticket.cuerpo or "", resultado_adjuntos["texto_combinado"])
    ticket.datos_extraidos = {
        **claves_operativas,
        "datos_estructurados": datos_fusionados,
        "resumen": resumen,
        "archivos_procesados": resultado_adjuntos["archivos_procesados"],
        "detalle_archivos": [
            {
                "nombre": d["nombre"],
                "paginas": d.get("paginas", 0),
                "datos": d.get("datos", {}),
                "texto_preview": d.get("texto_preview", ""),
                "error": d.get("error"),
            }
            for d in resultado_adjuntos["detalle_archivos"]
        ],
        "fecha_extraccion": datetime.utcnow().isoformat(),
    }
    
    # Vinculación conservadora: usa cualquier fuente fiable, pero solo acepta
    # código exacto o un nombre que sea único dentro de los expedientes oficiales.
    caratula = datos_fusionados.get("caratula") or {}
    alumno_resumen = resumen.get("datos_alumno") or {}
    codigo = (
        ticket.codigo_alumno_osticket
        or datos_fusionados.get("codigo_alumno")
        or alumno_resumen.get("codigo")
    )
    nombre = (
        ticket.nombre_estudiante_osticket
        or caratula.get("nombre_alumno")
        or datos_fusionados.get("nombre_firma")
        or datos_fusionados.get("nombre_osticket")
        or alumno_resumen.get("nombre")
    )
    if codigo or nombre:
        exp, criterio = buscar_expediente_existente(db, codigo=codigo, nombre=nombre)
        if exp:
            ticket.id_expediente = exp.id_expediente
            ticket.estado_scraping = "Clasificado"
            ticket.datos_extraidos["vinculacion"] = {
                "id_expediente": exp.id_expediente,
                "uuid": exp.uuid,
                "criterio": criterio,
                "estado": "vinculado_auto_evidencia",
                "fuentes": {
                    "codigo": "osTicket/cuerpo/adjunto" if codigo else None,
                    "nombre": "osTicket/cuerpo/adjunto" if nombre else None,
                },
            }
        else:
            ticket.datos_extraidos["vinculacion"] = {
                "estado": "sin_expediente_existente",
                "codigo_detectado": normalizar_codigo_alumno(codigo),
                "nombre_detectado": nombre,
            }

    if ticket.estado_scraping not in ("Clasificado", "Notificado"):
        ticket.estado_scraping = "Datos_Extraidos"
    db.commit()
    db.refresh(ticket)
    return ticket.datos_extraidos


def ejecutar_extraccion_background(ticket_id: int):
    db = SessionLocal()
    try:
        ticket = db.query(models.TicketOsticket).filter(models.TicketOsticket.ticket_id == ticket_id).first()
        if ticket:
            ejecutar_extraccion(db, ticket)
    finally:
        db.close()


@app.get("/")
def estado_servidor():
    return {"status": "online", "mensaje": "API EPG-UAC v3 operativa"}


@app.get("/api/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.activo == True).all()
    return [
        {
            "id_usuario": u.id_usuario,
            "nombre_completo": u.nombre_completo,
            "correo": u.correo,
            "usuario_login": u.usuario_login,
            "rol": u.rol,
            "activo": u.activo,
            "password_configurada": bool(u.password_hash),
            "debe_cambiar_password": bool(u.debe_cambiar_password),
            "fecha_cambio_password": u.fecha_cambio_password.isoformat() if u.fecha_cambio_password else None,
        }
        for u in usuarios
    ]


@app.post("/api/auth/login")
async def login(
    request: Request,
    correo: Optional[str] = Query(None),
    password: Optional[str] = Query(None),
    # Compatibilidad legacy: si se pasa id_usuario sin password, modo sin contraseña
    id_usuario: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Login JWT. Acepta formulario/JSON y conserva temporalmente parametros legacy."""
    content_type = request.headers.get("content-type", "").lower()
    datos_body = {}
    try:
        if "application/json" in content_type:
            datos_body = await request.json()
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            datos_body = dict(await request.form())
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudieron leer las credenciales")

    identificador = str(datos_body.get("username") or datos_body.get("correo") or correo or "").strip().lower()
    password = str(datos_body.get("password") if datos_body.get("password") is not None else password or "")

    if id_usuario and not identificador:
        # Modo legacy: buscar por ID sin contraseña (solo si el usuario no tiene hash)
        if not LEGACY_PASSWORD_LOGIN_ENABLED:
            raise HTTPException(status_code=401, detail="El acceso legado sin contraseña está deshabilitado.")
        usuario = db.query(models.UsuarioSistema).filter(
            models.UsuarioSistema.id_usuario == id_usuario,
            models.UsuarioSistema.activo == True,
        ).first()
        if not usuario or usuario.password_hash:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    else:
        usuario = db.query(models.UsuarioSistema).filter(
            models.UsuarioSistema.activo == True,
            or_(models.UsuarioSistema.usuario_login == identificador, models.UsuarioSistema.correo == identificador),
        ).first()
        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        if usuario.password_hash:
            # Usuario con contraseña configurada — verificar
            if not verificar_password(password, usuario.password_hash):
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        else:
            # Usuario sin contraseña (modo legacy para migración)
            if not LEGACY_PASSWORD_LOGIN_ENABLED:
                raise HTTPException(status_code=401, detail="Esta cuenta requiere configurar contraseña.")

    token, _ = iniciar_sesion(db, usuario, request.headers.get("X-EPG-Device-ID"))
    db.commit()
    return {
        "access_token": token,
        "token_type": "bearer",
        "id_usuario": usuario.id_usuario,
        "nombre_completo": usuario.nombre_completo,
        "correo": usuario.correo,
        "rol": usuario.rol,
        "debe_cambiar_password": bool(usuario.debe_cambiar_password),
    }


def url_callback_google() -> str:
    return f"{EPG_PUBLIC_BASE_URL}{EPG_PUBLIC_API_PREFIX}/api/auth/google/callback"


def url_login_google_error(mensaje: str) -> str:
    # El fragmento no se envía al servidor ni se registra en los access logs.
    return f"{EPG_PUBLIC_BASE_URL}/a0#oauth_error={quote(mensaje, safe='')}"


RUTA_TOKEN_DRIVE_LECTURA = Path("/opt/sistema_posgrado/data/private/google_drive_readonly_token.json")
RUTA_ESTADO_DRIVE_LECTURA = Path("/opt/sistema_posgrado/data/private/google_drive_readonly_estado.json")


def registrar_estado_drive_lectura(etapa: str, **detalle) -> None:
    """Deja un diagnóstico operativo sin persistir tokens ni datos OAuth sensibles."""
    RUTA_ESTADO_DRIVE_LECTURA.parent.mkdir(parents=True, exist_ok=True)
    contenido = {"etapa": etapa, "actualizado_en": datetime.utcnow().isoformat(), **detalle}
    temporal = RUTA_ESTADO_DRIVE_LECTURA.with_suffix(".tmp")
    temporal.write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")
    os.chmod(temporal, 0o600)
    temporal.replace(RUTA_ESTADO_DRIVE_LECTURA)


def guardar_token_drive_lectura(token: dict, correo: str) -> None:
    """Persiste solo el refresh token de la cuenta institucional autorizada."""
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("Google no entregó refresh_token; vuelve a autorizar con consentimiento.")
    RUTA_TOKEN_DRIVE_LECTURA.parent.mkdir(parents=True, exist_ok=True)
    temporal = RUTA_TOKEN_DRIVE_LECTURA.with_suffix(".tmp")
    temporal.write_text(
        json.dumps({"refresh_token": refresh_token, "correo": correo, "autorizado_en": datetime.utcnow().isoformat()}, ensure_ascii=False),
        encoding="utf-8",
    )
    os.chmod(temporal, 0o600)
    temporal.replace(RUTA_TOKEN_DRIVE_LECTURA)


@app.get("/api/admin/integraciones/drive/conectar")
async def iniciar_conexion_drive_lectura(
    request: Request,
):
    """Autoriza una única cuenta UAndina para inventario/descarga de solo lectura."""
    if not oauth_google:
        raise HTTPException(status_code=503, detail="Google OAuth no está configurado.")
    if not GOOGLE_DRIVE_OWNER_EMAILS:
        raise HTTPException(status_code=503, detail="Falta configurar EPG_GOOGLE_DRIVE_OWNER_EMAILS.")
    request.session["epg_drive_lectura_pendiente"] = True
    registrar_estado_drive_lectura("autorizacion_iniciada")
    return await oauth_google.drive_readonly.authorize_redirect(
        request,
        url_callback_google(),
        prompt="consent",
        access_type="offline",
    )


@app.get("/api/auth/google/config")
def configuracion_google_login():
    """Expone solo disponibilidad; credenciales y callback no salen de la API."""
    return {"enabled": bool(oauth_google)}


@app.get("/api/auth/google/login")
async def iniciar_login_google(request: Request, dispositivo: str = Query(..., min_length=20, max_length=200)):
    if not oauth_google:
        raise HTTPException(status_code=503, detail="El acceso con Google aún no está configurado.")
    # La sesión firmada conserva el dispositivo y el estado anti-CSRF durante el salto a Google.
    request.session["epg_dispositivo"] = dispositivo
    return await oauth_google.google.authorize_redirect(request, url_callback_google(), prompt="select_account")


@app.get("/api/auth/google/callback", name="auth_google_callback")
async def callback_login_google(request: Request, db: Session = Depends(get_db)):
    if not oauth_google:
        raise HTTPException(status_code=503, detail="El acceso con Google aún no está configurado.")
    es_conexion_drive = bool(request.session.pop("epg_drive_lectura_pendiente", None)) or any(
        str(clave).startswith("_state_drive_readonly_")
        for clave in request.session
    ) or "https://www.googleapis.com/auth/drive.readonly" in request.query_params.get("scope", "")
    try:
        cliente = oauth_google.drive_readonly if es_conexion_drive else oauth_google.google
        token_google = await cliente.authorize_access_token(request)
        perfil_google = token_google.get("userinfo") or {}
        if es_conexion_drive and not perfil_google:
            respuesta_perfil = await cliente.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                token=token_google,
            )
            respuesta_perfil.raise_for_status()
            perfil_google = respuesta_perfil.json()
    except Exception:
        if es_conexion_drive:
            registrar_estado_drive_lectura("error_oauth")
        logger.warning("Falló el retorno de Google OAuth", exc_info=True)
        return RedirectResponse(url_login_google_error("No se pudo validar tu cuenta de Google."), status_code=303)

    correo = str(perfil_google.get("email") or "").strip().lower()
    dominio = str(perfil_google.get("hd") or "").strip().lower()
    dispositivo = request.session.pop("epg_dispositivo", None)
    if (
        not correo
        or not bool(perfil_google.get("email_verified"))
        or dominio != GOOGLE_DOMINIO_PERMITIDO
        or not correo.endswith(f"@{GOOGLE_DOMINIO_PERMITIDO}")
        or (not es_conexion_drive and not dispositivo)
    ):
        if es_conexion_drive:
            registrar_estado_drive_lectura("perfil_invalido", correo=correo or None, dominio=dominio or None)
        return RedirectResponse(url_login_google_error("Usa una cuenta institucional UAndina válida."), status_code=303)

    if es_conexion_drive:
        if correo not in GOOGLE_DRIVE_OWNER_EMAILS:
            registrar_estado_drive_lectura("cuenta_no_autorizada", correo=correo)
            return RedirectResponse(url_login_google_error("Esta cuenta no está autorizada para la lectura institucional de Drive."), status_code=303)
        try:
            guardar_token_drive_lectura(token_google, correo)
        except Exception as exc:
            registrar_estado_drive_lectura("error_guardado_token", correo=correo)
            logger.warning("No se pudo guardar autorización Drive de solo lectura", exc_info=True)
            return RedirectResponse(url_login_google_error("No se pudo guardar la autorización de Drive."), status_code=303)
        registrar_estado_drive_lectura("autorizado", correo=correo)
        return RedirectResponse(f"{EPG_PUBLIC_BASE_URL}/a0#drive_readonly_connected=1", status_code=303)

    usuario = db.query(models.UsuarioSistema).filter(
        func.lower(models.UsuarioSistema.correo) == correo,
        models.UsuarioSistema.activo == True,
    ).first()
    if not usuario:
        return RedirectResponse(
            url_login_google_error("Tu correo no tiene una cuenta activa autorizada en Posgrado."),
            status_code=303,
        )

    try:
        token_epg, _ = iniciar_sesion(
            db,
            usuario,
            dispositivo,
            origen_autenticacion="google",
        )
        db.commit()
    except HTTPException:
        db.rollback()
        logger.warning("No se pudo crear la sesión de Google para el usuario %s", usuario.id_usuario)
        return RedirectResponse(url_login_google_error("No se pudo iniciar la sesión institucional."), status_code=303)

    # El JWT viaja solo en fragmento: el navegador lo recibe, pero no lo entrega a Nginx.
    return RedirectResponse(f"{EPG_PUBLIC_BASE_URL}/a0#oauth_token={quote(token_epg, safe='')}", status_code=303)


@app.post("/api/auth/vista-rol")
def iniciar_vista_por_rol(
    payload: VistaRolPayload,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    """Emite una sesión temporal, solo lectura, con el rol seleccionado por Administración."""
    destino = db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.id_usuario == payload.id_usuario,
        models.UsuarioSistema.activo == True,
    ).first()
    if not destino:
        raise HTTPException(status_code=404, detail="Usuario activo no encontrado.")
    if destino.id_usuario == current_user.id_usuario:
        raise HTTPException(status_code=400, detail="Ya estás usando tu propia cuenta de Administrador.")
    token, _ = iniciar_sesion(
        db,
        destino,
        request.headers.get("X-EPG-Device-ID"),
        tipo=TIPO_VISTA_ROL,
        minutos=30,
        administrador_origen=current_user,
    )
    db.commit()
    logger.warning(
        "vista_rol_iniciada administrador_id=%s destino_id=%s rol=%s",
        current_user.id_usuario,
        destino.id_usuario,
        destino.rol,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "id_usuario": destino.id_usuario,
        "nombre_completo": destino.nombre_completo,
        "correo": destino.correo,
        "rol": destino.rol,
        "debe_cambiar_password": bool(destino.debe_cambiar_password),
        "modo_vista_rol": True,
        "expira_en_minutos": 30,
    }


@app.post("/api/auth/logout")
def cerrar_mi_sesion(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    payload = getattr(request.state, "auth_payload", {})
    cerrar_sesion(db, payload.get("jti"), "cierre_usuario")
    db.commit()
    return {"status": "ok"}


@app.post("/api/auth/cerrar-otras-sesiones")
def cerrar_mis_otras_sesiones(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    payload = getattr(request.state, "auth_payload", {})
    cerradas = revocar_sesiones(
        db,
        current_user.id_usuario,
        "cierre_remoto_por_usuario",
        excluir_jti=payload.get("jti"),
    )
    db.commit()
    return {"status": "ok", "sesiones_cerradas": cerradas}


@app.post("/api/usuarios")
def crear_usuario(
    nombre_completo: str,
    correo: str,
    rol: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    if rol not in {"Administrador", "Recepcion", "Secretaria_Academica", "Directora", "Dictaminante"}:
        raise HTTPException(status_code=400, detail="Rol de usuario no permitido")
    usuario = models.UsuarioSistema(
        nombre_completo=nombre_completo,
        correo=correo,
        rol=rol,
        debe_cambiar_password=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {
        "id_usuario": usuario.id_usuario,
        "nombre_completo": usuario.nombre_completo,
        "rol": usuario.rol,
        "debe_cambiar_password": True,
    }


@app.put("/api/usuarios/{id_usuario}")
def actualizar_usuario(
    id_usuario: int,
    nombre_completo: str,
    correo: str,
    rol: str,
    activo: bool = True,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if rol not in {"Administrador", "Recepcion", "Secretaria_Academica", "Directora", "Dictaminante"}:
        raise HTTPException(status_code=400, detail="Rol de usuario no permitido")
    usuario.nombre_completo = nombre_completo
    usuario.correo = correo
    usuario.rol = rol
    usuario.activo = activo
    db.commit()
    return {"status": "ok"}


@app.delete("/api/usuarios/{id_usuario}")
def eliminar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.activo = False
    db.commit()
    return {"status": "ok"}


@app.get("/api/admin/security/legacy-accounts")
def reporte_cuentas_legacy(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    """Reporte agregado, sin correos ni hashes, para retirar el modo legacy con coordinación."""
    filas = (
        db.query(models.UsuarioSistema.rol, func.count(models.UsuarioSistema.id_usuario))
        .filter(models.UsuarioSistema.activo == True, models.UsuarioSistema.password_hash.is_(None))
        .group_by(models.UsuarioSistema.rol)
        .all()
    )
    por_rol = {rol: total for rol, total in filas}
    return {
        "legacy_password_login_enabled": LEGACY_PASSWORD_LOGIN_ENABLED,
        "retirement_date": LEGACY_PASSWORD_RETIREMENT_DATE,
        "total_active_without_password": sum(por_rol.values()),
        "by_role": por_rol,
        "nota": "Reporte agregado: no expone correos, hashes ni credenciales.",
    }


@app.get("/api/integraciones/outbox")
def listar_outbox(
    status: Optional[str] = Query(None, pattern="^(borrador|pendiente_aprobacion|aprobada|cancelada)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    query = db.query(models.IntegrationOutbox)
    if current_user.rol not in ROLES_AUTORIZACION:
        if current_user.rol != "Recepcion":
            raise HTTPException(status_code=403, detail="No tienes permisos para auditar integraciones.")
        query = query.filter(models.IntegrationOutbox.requested_by == current_user.id_usuario)
    if status:
        query = query.filter(models.IntegrationOutbox.status == status)
    total = query.count()
    items = (
        query.order_by(models.IntegrationOutbox.requested_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page) if total else 0,
        "outbound_actions_enabled": salidas_externas_habilitadas(),
        "data": [serializar_solicitud(item, incluir_eventos=True) for item in items],
    }


@app.post("/api/integraciones/outbox")
def solicitar_salida(
    payload: CrearOutboxPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    if payload.target_system != "osticket":
        raise HTTPException(status_code=400, detail="E1 solo admite solicitudes locales destinadas a osTicket.")
    if payload.action_type not in {"ticket.respuesta_cliente", "ticket.notificacion"}:
        raise HTTPException(status_code=400, detail="Tipo de salida no habilitado en E1.")
    if payload.subject_type != "ticket":
        raise HTTPException(status_code=400, detail="E1 solo admite tickets como sujeto de salida.")
    validar_payload_salida(payload.payload)
    ticket = obtener_ticket_por_ref(db, payload.ticket_ref or payload.subject_uuid)
    if ticket.uuid != payload.subject_uuid:
        raise HTTPException(status_code=400, detail="El sujeto de la solicitud no coincide con el ticket indicado.")
    expediente = obtener_expediente_por_ref(db, payload.expediente_ref) if payload.expediente_ref else ticket.expediente
    item, creada = crear_solicitud(
        db,
        actor=current_user,
        target_system=payload.target_system,
        action_type=payload.action_type,
        subject_type=payload.subject_type,
        subject_uuid=payload.subject_uuid,
        idempotency_key=payload.idempotency_key,
        payload=payload.payload,
        ticket=ticket,
        expediente=expediente,
        sustento=payload.sustento,
        status_inicial="borrador" if payload.borrador else "pendiente_aprobacion",
    )
    db.commit()
    db.refresh(item)
    return {"status": item.status, "creada": creada, "outbox": serializar_solicitud(item, incluir_eventos=True)}


@app.post("/api/integraciones/outbox/{outbox_uuid}/aprobar")
def aprobar_salida(
    outbox_uuid: str,
    payload: TransicionOutboxPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    item = aprobar_solicitud(db, obtener_outbox_por_uuid(db, outbox_uuid), current_user, payload.sustento)
    db.commit()
    db.refresh(item)
    return {
        "status": item.status,
        "outbox": serializar_solicitud(item, incluir_eventos=True),
        "mensaje": "La solicitud fue aprobada localmente; E1 no ejecuta acciones externas.",
    }


@app.post("/api/integraciones/outbox/{outbox_uuid}/cancelar")
def cancelar_salida(
    outbox_uuid: str,
    payload: TransicionOutboxPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    item = cancelar_solicitud(db, obtener_outbox_por_uuid(db, outbox_uuid), current_user, payload.sustento)
    db.commit()
    db.refresh(item)
    return {"status": item.status, "outbox": serializar_solicitud(item, incluir_eventos=True)}


@app.get("/api/dashboard/kpis")
def obtener_kpis(
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    """KPIs del tablero. Cuando se elige un año, todo el tablero usa esa cohorte anual."""
    decision_expr = expresion_json_texto("$.decision_actual.decision")
    inicio_hoy = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_anio = datetime(anio, 1, 1) if anio else None
    fin_anio = datetime(anio + 1, 1, 1) if anio else None
    expedientes_query = db.query(models.ExpedienteTesis).filter(expediente_visible_operativamente())
    if anio:
        fecha_cohorte = func.coalesce(
            models.ExpedienteTesis.fecha_inicio_tramite,
            models.ExpedienteTesis.fecha_ultimo_movimiento,
        )
        expedientes_query = expedientes_query.filter(fecha_cohorte >= inicio_anio, fecha_cohorte < fin_anio)
    ids_expedientes = [fila[0] for fila in expedientes_query.with_entities(models.ExpedienteTesis.id_expediente).all()]
    filtro_tickets_anio = None
    if anio:
        filtro_tickets_anio = or_(
            models.TicketOsticket.id_expediente.in_(ids_expedientes or [-1]),
            and_(
                models.TicketOsticket.id_expediente == None,
                models.TicketOsticket.fecha_creacion_osticket >= inicio_anio,
                models.TicketOsticket.fecha_creacion_osticket < fin_anio,
            ),
        )

    def tickets_query():
        query = db.query(models.TicketOsticket)
        return query.filter(filtro_tickets_anio) if filtro_tickets_anio is not None else query

    total_tickets = tickets_query().count()
    tickets_nuevos = (
        tickets_query()
        .filter(models.TicketOsticket.fecha_creacion_osticket >= inicio_hoy)
        .count()
    )
    decisiones_hoy = db.query(models.TicketDecision).filter(
        models.TicketDecision.fecha_registro >= inicio_hoy
    ).count()
    movimientos_hoy = db.query(models.HistorialMovimiento).filter(
        models.HistorialMovimiento.fecha_movimiento >= inicio_hoy
    ).count()
    tickets_pendientes = (
        tickets_query()
        .filter(models.TicketOsticket.estado_scraping != "Notificado")
        .count()
    )
    tickets_abiertos_15_dias = (
        tickets_query()
        .filter(
            models.TicketOsticket.estado_scraping != "Notificado",
            models.TicketOsticket.fecha_creacion_osticket <= datetime.utcnow() - timedelta(days=15),
        )
        .count()
    )
    tickets_sin_clasificar = (
        tickets_query()
        .filter(models.TicketOsticket.id_expediente == None, models.TicketOsticket.estado_scraping != "Notificado")
        .count()
    )
    tickets_fuera_proceso = (
        tickets_query()
        .filter(decision_expr.in_(["no_corresponde", "cerrar_interno"]))
        .count()
    )
    tickets_requieren_resolucion = (
        tickets_query()
        .filter(decision_expr == "requiere_resolucion")
        .count()
    )
    resoluciones_pendientes_firma = (
        db.query(models.ResolucionFirma)
        .filter(models.ResolucionFirma.estado_firma == "Pendiente_Directora")
        .count()
    )
    resoluciones_firmadas_hoy = (
        db.query(models.ResolucionFirma)
        .filter(
            models.ResolucionFirma.estado_firma == "Firmado",
            models.ResolucionFirma.fecha_firma >= inicio_hoy,
        )
        .count()
    )
    actividad_reciente = []
    for item in db.query(models.TicketDecision).filter(
        models.TicketDecision.fecha_registro >= inicio_hoy
    ).order_by(models.TicketDecision.fecha_registro.desc()).limit(4).all():
        ticket = db.get(models.TicketOsticket, item.ticket_id)
        actividad_reciente.append({
            "tipo": "decision_ticket", "icono": "pi-inbox", "fecha": item.fecha_registro.isoformat(),
            "titulo": f"Ticket #{ticket.numero_visual if ticket else item.ticket_id}",
            "detalle": (item.decision or "Decisión registrada").replace("_", " "),
        })
    for item in db.query(models.HistorialMovimiento).filter(
        models.HistorialMovimiento.fecha_movimiento >= inicio_hoy
    ).order_by(models.HistorialMovimiento.fecha_movimiento.desc()).limit(4).all():
        expediente = db.get(models.ExpedienteTesis, item.id_expediente)
        actividad_reciente.append({
            "tipo": "movimiento_expediente", "icono": "pi-folder-open", "fecha": item.fecha_movimiento.isoformat(),
            "titulo": expediente.nombre_alumno if expediente else f"Expediente #{item.id_expediente}",
            "detalle": item.accion.replace("_", " "),
        })
    for item in db.query(models.ResolucionFirma).filter(
        models.ResolucionFirma.estado_firma == "Firmado",
        models.ResolucionFirma.fecha_firma >= inicio_hoy,
    ).order_by(models.ResolucionFirma.fecha_firma.desc()).limit(4).all():
        expediente = db.get(models.ExpedienteTesis, item.id_expediente)
        actividad_reciente.append({
            "tipo": "resolucion_firmada", "icono": "pi-file-check", "fecha": item.fecha_firma.isoformat(),
            "titulo": item.tipo_documento or "Resolución firmada",
            "detalle": expediente.nombre_alumno if expediente else f"Expediente #{item.id_expediente}",
        })
    actividad_reciente.sort(key=lambda item: item["fecha"], reverse=True)
    vinculados_sin_resolucion = (
        tickets_query()
        .filter(
            models.TicketOsticket.id_expediente != None,
            models.TicketOsticket.estado_scraping != "Notificado",
            or_(decision_expr == None, decision_expr != "resolucion_notificada"),
        )
        .count()
    )
    vinculados_con_resolucion = (
        tickets_query()
        .filter(
            models.TicketOsticket.id_expediente != None,
            decision_expr == "resolucion_notificada",
        )
        .count()
    )
    ahora = datetime.utcnow()
    try:
        limite_trayectoria = ahora.replace(year=ahora.year - 5)
        limite_trayectoria_proxima = (ahora + timedelta(days=90)).replace(year=(ahora + timedelta(days=90)).year - 5)
    except ValueError:
        # Solo protege el 29 de febrero al calcular el horizonte operativo de cinco años.
        limite_trayectoria = ahora.replace(year=ahora.year - 5, month=2, day=28)
        horizonte = ahora + timedelta(days=90)
        limite_trayectoria_proxima = horizonte.replace(year=horizonte.year - 5, month=2, day=28)
    trayectorias_cinco_anios = (
        expedientes_query
        .filter(
            models.ExpedienteTesis.estado_expediente == "En Proceso",
            models.ExpedienteTesis.fecha_inicio_tramite <= limite_trayectoria,
        )
        .count()
    )
    trayectorias_cinco_anios_proximas = (
        expedientes_query
        .filter(
            models.ExpedienteTesis.estado_expediente == "En Proceso",
            models.ExpedienteTesis.fecha_inicio_tramite > limite_trayectoria,
            models.ExpedienteTesis.fecha_inicio_tramite <= limite_trayectoria_proxima,
        )
        .count()
    )
    errores_sync = (
        tickets_query()
        .filter(models.TicketOsticket.estado_scraping == "Error")
        .count()
    )
    adjuntos_pendientes = (
        tickets_query()
        .filter(models.TicketOsticket.estado_scraping.in_(["Pendiente_Descarga", "Archivos_Descargados"]))
        .count()
    )
    total_expedientes = expedientes_query.count()
    expedientes_en_proceso = (
        expedientes_query.filter(models.ExpedienteTesis.estado_expediente == "En Proceso").count()
    )
    expedientes_observados = (
        expedientes_query.filter(models.ExpedienteTesis.estado_expediente == "Observado").count()
    )
    graduados = (
        expedientes_query.filter(models.ExpedienteTesis.estado_expediente == "Archivado_Graduado").count()
    )
    requisitos_pendientes = (
        db.query(models.ExpedienteRequisito)
        .join(models.RequisitoPasoCatalogo)
        .join(models.ExpedienteTesis)
        .filter(
            models.ExpedienteTesis.id_expediente.in_(ids_expedientes or [-1]) if anio else True,
            models.RequisitoPasoCatalogo.id_paso == models.ExpedienteTesis.id_paso_actual,
            models.RequisitoPasoCatalogo.obligatorio == True,
            models.ExpedienteRequisito.estado.notin_(["Validado", "No_Aplica"]),
        )
        .count()
    )
    requisitos_observados = (
        db.query(models.ExpedienteRequisito)
        .join(models.RequisitoPasoCatalogo)
        .join(models.ExpedienteTesis)
        .filter(
            models.ExpedienteTesis.id_expediente.in_(ids_expedientes or [-1]) if anio else True,
            models.RequisitoPasoCatalogo.id_paso == models.ExpedienteTesis.id_paso_actual,
            models.ExpedienteRequisito.estado == "Observado",
        )
        .count()
    )

    por_paso = []
    for paso in db.query(models.PasoFlujo).order_by(models.PasoFlujo.id_paso).all():
        count = (
            expedientes_query
            .filter(
                models.ExpedienteTesis.id_paso_actual == paso.id_paso,
                models.ExpedienteTesis.estado_expediente == "En Proceso",
            )
            .count()
        )
        por_paso.append({"id_paso": paso.id_paso, "nombre_paso": paso.nombre_paso, "total": count})

    estados_expedientes = []
    for estado, etiqueta in (
        ("En Proceso", "En proceso"),
        ("Observado", "Observados"),
        ("Archivado_Graduado", "Graduados"),
        ("Caduco", "Vigencia de paso vencida"),
    ):
        estados_expedientes.append({
            "clave": estado,
            "label": etiqueta,
            "total": expedientes_query
            .filter(models.ExpedienteTesis.estado_expediente == estado)
            .count(),
        })

    return {
        "contexto": {"anio": anio, "etiqueta": str(anio) if anio else "Todos los años"},
        "tickets_sincronizados": total_tickets,
        "tickets_nuevos": tickets_nuevos,
        "decisiones_hoy": decisiones_hoy,
        "movimientos_hoy": movimientos_hoy,
        "tickets_pendientes_reales": tickets_pendientes,
        "tickets_abiertos_15_dias": tickets_abiertos_15_dias,
        "tickets_sin_clasificar": tickets_sin_clasificar,
        "tickets_fuera_proceso": tickets_fuera_proceso,
        "tickets_requieren_resolucion": tickets_requieren_resolucion,
        "resoluciones_pendientes_firma": resoluciones_pendientes_firma,
        "resoluciones_firmadas_hoy": resoluciones_firmadas_hoy,
        "actividad_reciente": actividad_reciente[:6],
        "tickets_vinculados_sin_resolucion": vinculados_sin_resolucion,
        "tickets_vinculados_con_resolucion": vinculados_con_resolucion,
        "errores_sync": errores_sync,
        "adjuntos_pendientes": adjuntos_pendientes,
        "total_expedientes": total_expedientes,
        "en_proceso": expedientes_en_proceso,
        "observados": expedientes_observados,
        "graduados": graduados,
        "requisitos_pendientes_actuales": requisitos_pendientes,
        "requisitos_observados_actuales": requisitos_observados,
        "trayectorias_cinco_anios": trayectorias_cinco_anios,
        "trayectorias_cinco_anios_proximas": trayectorias_cinco_anios_proximas,
        "resoluciones": db.query(models.ResolucionDocumento).count(),
        "distribucion_pasos": por_paso,
        "estados_expedientes": estados_expedientes,
        "colas": [
            {
                "clave": "requiere_resolucion",
                "label": "Requiere resolucion",
                "total": tickets_requieren_resolucion,
                "ruta": "/tickets-pendientes?cola=requiere_resolucion",
            },
            {
                "clave": "falta_resolucion",
                "label": "Vinculados pendientes",
                "total": vinculados_sin_resolucion,
                "ruta": "/tickets-pendientes?cola=falta_resolucion",
            },
            {
                "clave": "sin_expediente",
                "label": "Sin expediente",
                "total": tickets_sin_clasificar,
                "ruta": "/tickets-pendientes?cola=sin_expediente",
            },
            {
                "clave": "pendiente_adjuntos",
                "label": "Descarga o extraccion",
                "total": adjuntos_pendientes,
                "ruta": "/tickets-pendientes?cola=pendiente_adjuntos",
            },
            {
                "clave": "error_extraccion",
                "label": "Errores tecnicos",
                "total": errores_sync,
                "ruta": "/tickets-pendientes?cola=error_extraccion",
            },
        ],
        "bot": obtener_estado_bot_operativo(),
    }


def vencimiento_resolucion(fecha: datetime | None) -> datetime | None:
    """La vigencia institucional es de 24 meses desde la emisión."""
    if not fecha:
        return None
    try:
        return fecha.replace(year=fecha.year + 2)
    except ValueError:
        return fecha.replace(year=fecha.year + 2, month=2, day=28)


def obtener_vencimientos_expedientes(db: Session, dias: int, anio: int | None = None) -> tuple[list[dict], list[int]]:
    """Obtiene la vigencia del paso actual sin asumir que una firma cierra el expediente."""
    hoy = datetime.utcnow()
    limite = hoy + timedelta(days=dias)
    expedientes_query = db.query(models.ExpedienteTesis).filter(
        expediente_visible_operativamente(),
        models.ExpedienteTesis.estado_expediente == "En Proceso",
    )
    if anio:
        fecha_cohorte = func.coalesce(
            models.ExpedienteTesis.fecha_inicio_tramite,
            models.ExpedienteTesis.fecha_ultimo_movimiento,
        )
        expedientes_query = expedientes_query.filter(
            fecha_cohorte >= datetime(anio, 1, 1),
            fecha_cohorte < datetime(anio + 1, 1, 1),
        )
    expedientes = expedientes_query.all()
    firmas = (
        db.query(models.ResolucionFirma)
        .filter(models.ResolucionFirma.estado_firma == "Firmado")
        .order_by(models.ResolucionFirma.fecha_firma.asc())
        .all()
    )
    firmas_actuales = {}
    for firma in firmas:
        if firma.fecha_firma:
            firmas_actuales[(firma.id_expediente, firma.id_paso_asociado)] = firma

    casos = []
    for expediente in expedientes:
        firma = firmas_actuales.get((expediente.id_expediente, expediente.id_paso_actual))
        vence = vencimiento_resolucion(firma.fecha_firma if firma else None)
        if vence and hoy <= vence <= limite:
            casos.append({
                "id_expediente": expediente.id_expediente,
                "uuid": expediente.uuid,
                "nombre_alumno": expediente.nombre_alumno,
                "codigo_alumno": expediente.codigo_alumno,
                "id_paso": expediente.id_paso_actual,
                "vence": vence.date().isoformat(),
            })
    casos.sort(key=lambda item: item["vence"])
    return casos, [caso["id_expediente"] for caso in casos]


@app.get("/api/dashboard/seguimiento-historico")
def obtener_seguimiento_historico(
    dias: int = Query(90, ge=1, le=730),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    """Indicadores temporales bajo un contexto anual compartido por el tablero."""
    hoy = datetime.utcnow()
    limite_30 = hoy + timedelta(days=30)
    todos_expedientes = db.query(models.ExpedienteTesis).filter(expediente_visible_operativamente()).all()
    expedientes = [
        expediente for expediente in todos_expedientes
        if not anio or (expediente.fecha_inicio_tramite or expediente.fecha_ultimo_movimiento or hoy).year == anio
    ]
    firmas = (
        db.query(models.ResolucionFirma)
        .filter(models.ResolucionFirma.estado_firma == "Firmado")
        .order_by(models.ResolucionFirma.fecha_firma.asc())
        .all()
    )
    firmas_actuales = {}
    ultima_firma = {}
    for firma in firmas:
        if not firma.fecha_firma:
            continue
        anterior = ultima_firma.get(firma.id_expediente)
        if not anterior or firma.fecha_firma > anterior.fecha_firma:
            ultima_firma[firma.id_expediente] = firma

        clave_paso = (firma.id_expediente, firma.id_paso_asociado)
        firmas_actuales[clave_paso] = firma

    cohortes = {}
    for expediente in todos_expedientes:
        anio_cohorte = (expediente.fecha_inicio_tramite or expediente.fecha_ultimo_movimiento or hoy).year
        cohorte = cohortes.setdefault(anio_cohorte, {"anio": anio_cohorte, "total": 0, "en_proceso": 0, "observados": 0, "caducos": 0, "graduados": 0})
        cohorte["total"] += 1
        if expediente.estado_expediente == "En Proceso":
            cohorte["en_proceso"] += 1
        elif expediente.estado_expediente == "Observado":
            cohorte["observados"] += 1
        elif expediente.estado_expediente == "Caduco":
            cohorte["caducos"] += 1
        elif expediente.estado_expediente == "Archivado_Graduado":
            cohorte["graduados"] += 1

    caducos_por_paso = {paso: 0 for paso in range(1, 8)}
    por_paso = {paso: 0 for paso in range(1, 8)}
    vence_30 = []
    vence_periodo, _ = obtener_vencimientos_expedientes(db, dias, anio)
    duraciones_graduados = []
    for expediente in expedientes:
        if expediente.estado_expediente == "En Proceso":
            pass
        elif expediente.estado_expediente == "Observado":
            pass
        elif expediente.estado_expediente == "Caduco":
            caducos_por_paso[expediente.id_paso_actual] += 1
        elif expediente.estado_expediente == "Archivado_Graduado":
            ultima = ultima_firma.get(expediente.id_expediente)
            if ultima and expediente.fecha_inicio_tramite and ultima.fecha_firma:
                duraciones_graduados.append((ultima.fecha_firma - expediente.fecha_inicio_tramite).days)

        if expediente.estado_expediente == "En Proceso":
            por_paso[expediente.id_paso_actual] += 1
            firma = firmas_actuales.get((expediente.id_expediente, expediente.id_paso_actual))
            vencimiento = vencimiento_resolucion(firma.fecha_firma if firma else None)
            if vencimiento and hoy <= vencimiento <= limite_30:
                vence_30.append(expediente.id_expediente)

    # Cada línea representa un año real de emisión, nunca un promedio artificial.
    ids_contexto = {expediente.id_expediente for expediente in expedientes}
    firmas_contexto = [firma for firma in firmas if firma.id_expediente in ids_contexto]
    anios_ritmo = sorted({firma.fecha_firma.year for firma in firmas_contexto if firma.fecha_firma})
    if anio:
        anios_ritmo = [anio]
    conteo_meses = {(year, month): 0 for year in anios_ritmo for month in range(1, 13)}
    for firma in firmas_contexto:
        if firma.fecha_firma:
            clave_mes = (firma.fecha_firma.year, firma.fecha_firma.month)
            if clave_mes in conteo_meses:
                conteo_meses[clave_mes] += 1
    ritmo_series = [
        {
            "anio": year,
            "total": sum(conteo_meses[(year, month)] for month in range(1, 13)),
            "valores": [conteo_meses[(year, month)] for month in range(1, 13)],
        }
        for year in anios_ritmo
    ]

    # Solo mide continuidades entre pasos distintos; no interpreta rectificaciones como avance.
    continuidad = {"0_30": 0, "31_90": 0, "91_180": 0, "mas_180": 0, "fuera_vigencia": 0}
    firmas_por_expediente = {}
    for firma in firmas_contexto:
        if firma.fecha_firma and firma.id_paso_asociado:
            firmas_por_expediente.setdefault(firma.id_expediente, []).append(firma)
    for historial_firmas in firmas_por_expediente.values():
        historial_firmas.sort(key=lambda firma: firma.fecha_firma)
        for firma in historial_firmas:
            anteriores = [
                anterior for anterior in historial_firmas
                if anterior.fecha_firma < firma.fecha_firma and anterior.id_paso_asociado < firma.id_paso_asociado
            ]
            if not anteriores:
                continue
            anterior = max(anteriores, key=lambda item: item.fecha_firma)
            vence_anterior = vencimiento_resolucion(anterior.fecha_firma)
            dias_antes = (vence_anterior - firma.fecha_firma).days
            if dias_antes < 0:
                continuidad["fuera_vigencia"] += 1
            elif dias_antes <= 30:
                continuidad["0_30"] += 1
            elif dias_antes <= 90:
                continuidad["31_90"] += 1
            elif dias_antes <= 180:
                continuidad["91_180"] += 1
            else:
                continuidad["mas_180"] += 1

    meses_cortos = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    return {
        "contexto": {"anio": anio, "etiqueta": str(anio) if anio else "Todos los años"},
        "cohortes": sorted(cohortes.values(), key=lambda item: item["anio"], reverse=True),
        "anios_disponibles": sorted(cohortes.keys(), reverse=True),
        "vigencia": {
            "caducos": sum(caducos_por_paso.values()),
            "caducos_por_paso": [{"id_paso": paso, "total": total} for paso, total in caducos_por_paso.items()],
            "vence_30": len(vence_30),
            "dias_consultados": dias,
            "vence_periodo": len(vence_periodo),
            # La interfaz mantiene su propio scroll; no recortar la lista frente al contador.
            "proximos": vence_periodo,
        },
        "trayectoria": {
            "activos_por_paso": [{"id_paso": paso, "total": total} for paso, total in por_paso.items()],
            "duracion_promedio_graduados_dias": round(sum(duraciones_graduados) / len(duraciones_graduados)) if duraciones_graduados else None,
            "ritmo_series": ritmo_series,
            "meses_ritmo": meses_cortos,
            # Compatibilidad con la cifra total del panel; el gráfico usa ritmo_series.
            "ritmo_resoluciones": [
                {
                    "anio": anio or 0,
                    "mes": month,
                    "etiqueta": meses_cortos[month - 1],
                    "total": sum(conteo_meses[(year, month)] for year in anios_ritmo),
                }
                for month in range(1, 13)
            ],
            "continuidad_antes_vigencia": continuidad,
        },
    }


@app.get("/api/dashboard/personas")
def obtener_personas_dashboard(
    busqueda: Optional[str] = Query(None, max_length=120),
    estado: Optional[str] = Query(None, pattern="^(En Proceso|Observado|Archivado_Graduado|Caduco)$"),
    id_paso: Optional[int] = Query(None, ge=1, le=7),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    limite: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Resumen humano del avance por estudiante, separado del monitor técnico."""
    query = db.query(models.ExpedienteTesis).filter(expediente_visible_operativamente())
    if anio:
        fecha_cohorte = func.coalesce(
            models.ExpedienteTesis.fecha_inicio_tramite,
            models.ExpedienteTesis.fecha_ultimo_movimiento,
        )
        query = query.filter(fecha_cohorte >= datetime(anio, 1, 1), fecha_cohorte < datetime(anio + 1, 1, 1))
    if estado:
        query = query.filter(models.ExpedienteTesis.estado_expediente == estado)
    if id_paso:
        query = query.filter(models.ExpedienteTesis.id_paso_actual == id_paso)
    if busqueda:
        termino = f"%{busqueda.strip()}%"
        query = query.filter(
            or_(
                models.ExpedienteTesis.nombre_alumno.like(termino),
                models.ExpedienteTesis.codigo_alumno.like(termino),
                models.ExpedienteTesis.titulo_tesis.like(termino),
            )
        )
    total = query.count()
    expedientes = query.order_by(models.ExpedienteTesis.nombre_alumno.asc()).limit(limite).all()
    tickets_por_expediente = dict(
        db.query(models.TicketOsticket.id_expediente, func.count(models.TicketOsticket.ticket_id))
        .filter(models.TicketOsticket.id_expediente != None)
        .group_by(models.TicketOsticket.id_expediente)
        .all()
    )
    resoluciones_por_expediente = dict(
        db.query(models.ResolucionFirma.id_expediente, func.count(models.ResolucionFirma.id_resolucion))
        .filter(models.ResolucionFirma.id_expediente != None)
        .group_by(models.ResolucionFirma.id_expediente)
        .all()
    )
    items = []
    for expediente in expedientes:
        items.append(
            {
                "id_expediente": expediente.id_expediente,
                "uuid": expediente.uuid,
                "nombre_alumno": expediente.nombre_alumno,
                "codigo_alumno": expediente.codigo_alumno,
                "grado_postula": expediente.grado_postula,
                "titulo_tesis": expediente.titulo_tesis,
                "id_paso_actual": expediente.id_paso_actual,
                "nombre_paso_actual": expediente.paso_actual.nombre_paso if expediente.paso_actual else "Sin paso",
                "estado_expediente": expediente.estado_expediente,
                "sub_estado": expediente.sub_estado,
                "tickets": tickets_por_expediente.get(expediente.id_expediente, 0),
                "resoluciones": resoluciones_por_expediente.get(expediente.id_expediente, 0),
            }
        )
    total_expedientes = db.query(models.ExpedienteTesis).filter(expediente_visible_operativamente()).count()
    total_tickets = db.query(models.TicketOsticket).filter(models.TicketOsticket.id_expediente != None).count()
    total_resoluciones = db.query(models.ResolucionFirma).filter(models.ResolucionFirma.id_expediente != None).count()
    return {
        "total": total,
        "items": items,
        "promedios": {
            "tickets_por_expediente": round(total_tickets / total_expedientes, 2) if total_expedientes else 0,
            "resoluciones_por_expediente": round(total_resoluciones / total_expedientes, 2) if total_expedientes else 0,
        },
    }


def obtener_estado_bot_operativo():
    estado = leer_estado_bot()
    estado.setdefault("estado", "sin_registro")
    estado.setdefault("intervalo_minutos", int(os.getenv("EPG_BOT_INTERVAL_MINUTES", "15")))
    estado.setdefault(
        "limites",
        {
            "deep_crawl": int(os.getenv("OSTICKET_MAX_DEEP_CRAWL", "80")),
            "workers_backfill": int(os.getenv("EPG_BACKFILL_WORKERS", "2")),
            "max_tickets_backfill": int(os.getenv("EPG_BACKFILL_MAX_TICKETS", "120")),
            "paginas_por_adjunto": int(os.getenv("EPG_EXTRACT_MAX_PAGES", "6")),
            "cpu_quota": "45%",
        },
    )
    actividad_logs = {}
    for nombre, ruta in {
        "sincronizacion": Path(os.getenv("OSTICKET_SYNC_LOG", "/opt/sistema_posgrado/backend/sincronizador.log")),
        "backfill": Path(os.getenv("OSTICKET_BACKFILL_LOG", "/opt/sistema_posgrado/backend/backfill_tickets.log")),
    }.items():
        try:
            actividad_logs[nombre] = datetime.utcfromtimestamp(ruta.stat().st_mtime).isoformat()
        except OSError:
            actividad_logs[nombre] = None
    estado["actividad_logs"] = actividad_logs
    return estado


@app.get("/api/operacion/bot")
def estado_bot():
    return obtener_estado_bot_operativo()


def db_ticket_activo_subquery():
    return select(models.ResolucionTramite.ticket_id).where(
            models.ResolucionTramite.ticket_id != None,
            models.ResolucionTramite.estado.in_(ESTADOS_ACTIVOS),
    )


def aplicar_filtro_situacion(query, situacion: str | None):
    if not situacion:
        return query
    decision_expr = expresion_json_texto("$.decision_actual.decision")
    if situacion == "requiere_accion":
        return query.filter(models.TicketOsticket.estado_scraping != "Notificado")
    if situacion == "requiere_resolucion":
        return query.filter(
            decision_expr == "requiere_resolucion",
            models.TicketOsticket.id_expediente == None,
            ~models.TicketOsticket.ticket_id.in_(
                db_ticket_activo_subquery()
            ),
        )
    if situacion == "en_tramite_resolucion":
        return query.filter(models.TicketOsticket.ticket_id.in_(db_ticket_activo_subquery()))
    if situacion == "fuera_proceso":
        return query.filter(decision_expr.in_(["no_corresponde", "cerrar_interno"]))
    if situacion == "pendiente_transferencia":
        return query.filter(decision_expr == "transferir")
    if situacion == "posible_expediente":
        # Compatibilidad para enlaces antiguos: ya no es una cola separada.
        situacion = "sin_expediente"
    if situacion == "sin_expediente":
        return query.filter(
            models.TicketOsticket.id_expediente == None,
            models.TicketOsticket.estado_scraping.notin_(["Pendiente_Descarga", "Archivos_Descargados", "Error", "Notificado"]),
            decision_expr == None,
        )
    if situacion in {"falta_resolucion", "por_clasificar"}:
        return query.filter(
            models.TicketOsticket.id_expediente != None,
            models.TicketOsticket.estado_scraping != "Notificado",
            decision_expr == None,
            ~models.TicketOsticket.ticket_id.in_(db_ticket_activo_subquery()),
        )
    if situacion == "atendido_con_resolucion":
        return query.filter(decision_expr == "resolucion_notificada")
    if situacion == "error_extraccion":
        return query.filter(models.TicketOsticket.estado_scraping == "Error")
    if situacion == "pendiente_adjuntos":
        return query.filter(
            models.TicketOsticket.estado_scraping.in_(["Pendiente_Descarga", "Archivos_Descargados"])
        )
    raise HTTPException(status_code=400, detail="Situacion operativa no valida")


@app.get("/api/tickets")
def obtener_bandeja_tickets(
    solo_sin_clasificar: bool = False,
    busqueda: Optional[str] = None,
    estado: Optional[str] = None,
    estado_operativo: str = Query("Activo", pattern="^(Activo|Revision_historica|Archivado_historico|Fuera_proceso|todos)$"),
    vinculado: Optional[str] = Query(None, description="'si', 'no' o vacio"),
    solo_con_adjuntos: bool = False,
    adjuntos: Optional[str] = Query(None, pattern="^(con|sin)$"),
    decision: Optional[str] = None,
    situacion: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    antiguedad_dias: Optional[int] = Query(None, ge=1, le=3650),
    paso_sugerido: Optional[int] = Query(None, ge=1, le=7),
    estudiante: Optional[str] = None,
    codigo: Optional[str] = None,
    asunto: Optional[str] = None,
    sort_by: str = Query("fecha", pattern="^(fecha|ticket|estudiante|codigo|estado|adjuntos)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.TicketOsticket)
    # La bandeja diaria no es un archivo histórico. Los casos archivados se
    # conservan y pueden consultarse explícitamente, pero no cuentan como
    # trabajo pendiente al abrir la vista.
    if estado_operativo != "todos":
        query = query.filter(models.TicketOsticket.estado_operativo == estado_operativo)
    if solo_sin_clasificar:
        query = query.filter(
            models.TicketOsticket.id_expediente == None,
            models.TicketOsticket.estado_scraping != "Notificado",
        )
    if estado:
        query = query.filter(models.TicketOsticket.estado_scraping == estado)
    if vinculado == "si":
        query = query.filter(models.TicketOsticket.id_expediente != None)
    elif vinculado == "no":
        query = query.filter(models.TicketOsticket.id_expediente == None)
    if solo_con_adjuntos or adjuntos == "con":
        query = query.filter(models.TicketOsticket.adjuntos.any())
    elif adjuntos == "sin":
        query = query.filter(~models.TicketOsticket.adjuntos.any())
    if decision:
        query = query.filter(expresion_json_texto("$.decision_actual.decision") == decision)
    query = aplicar_filtro_situacion(query, situacion)
    desde = parsear_fecha_filtro(fecha_desde, "fecha_desde")
    hasta = parsear_fecha_filtro(fecha_hasta, "fecha_hasta", fin_dia=True)
    if desde:
        query = query.filter(models.TicketOsticket.fecha_creacion_osticket >= desde)
    if hasta:
        query = query.filter(models.TicketOsticket.fecha_creacion_osticket <= hasta)
    if antiguedad_dias:
        query = query.filter(
            models.TicketOsticket.estado_scraping != "Notificado",
            models.TicketOsticket.fecha_creacion_osticket <= datetime.utcnow() - timedelta(days=antiguedad_dias),
        )
    if paso_sugerido:
        query = query.filter(
            or_(
                expresion_json_texto("$.resumen.paso_sugerido.id_paso") == str(paso_sugerido),
                expresion_json_texto("$.datos_estructurados.paso_sugerido.id_paso") == str(paso_sugerido),
            )
        )
    if estudiante:
        like = f"%{estudiante.strip()}%"
        query = query.filter(models.TicketOsticket.nombre_estudiante_osticket.like(like))
    if codigo:
        like = f"%{codigo.strip()}%"
        query = query.filter(models.TicketOsticket.codigo_alumno_osticket.like(like))
    if asunto:
        like = f"%{asunto.strip()}%"
        query = query.filter(models.TicketOsticket.asunto.like(like))
    if busqueda:
        like = f"%{busqueda.strip()}%"
        query = query.filter(
            or_(
                models.TicketOsticket.numero_visual.like(like),
                models.TicketOsticket.asunto.like(like),
                models.TicketOsticket.nombre_estudiante_osticket.like(like),
                models.TicketOsticket.codigo_alumno_osticket.like(like),
                models.TicketOsticket.email_estudiante.like(like),
                models.TicketOsticket.cuerpo.like(like),
                models.TicketOsticket.adjuntos.any(models.TicketAdjunto.nombre_archivo.like(like)),
                models.TicketOsticket.expediente.has(
                    or_(
                        models.ExpedienteTesis.nombre_alumno.like(like),
                        models.ExpedienteTesis.codigo_alumno.like(like),
                        models.ExpedienteTesis.titulo_tesis.like(like),
                        models.ExpedienteTesis.asignaciones.any(
                            models.AsignacionTesis.docente.has(models.Docente.nombre_completo.like(like))
                        ),
                    )
                ),
            )
        )

    sort_map = {
        "fecha": models.TicketOsticket.fecha_creacion_osticket,
        "ticket": models.TicketOsticket.numero_visual,
        "estudiante": models.TicketOsticket.nombre_estudiante_osticket,
        "codigo": models.TicketOsticket.codigo_alumno_osticket,
        "estado": models.TicketOsticket.estado_scraping,
        "adjuntos": func.count(models.TicketAdjunto.id_adjunto),
    }
    if sort_by == "adjuntos":
        query = query.outerjoin(models.TicketAdjunto).group_by(models.TicketOsticket.ticket_id)
    sort_col = sort_map[sort_by]
    query = query.order_by(sort_col.asc() if sort_dir == "asc" else sort_col.desc())

    total, total_pages, tickets = paginar(query, page, per_page)
    return {
        "total_tickets": total,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": [serializar_ticket(ticket) for ticket in tickets],
    }


@app.get("/api/buscar")
def busqueda_global(
    q: str = Query(..., min_length=2),
    limite: int = Query(8, ge=1, le=25),
    db: Session = Depends(get_db),
):
    texto = q.strip()
    like = f"%{texto}%"

    tickets = (
        db.query(models.TicketOsticket)
        .filter(
            or_(
                models.TicketOsticket.numero_visual.like(like),
                models.TicketOsticket.asunto.like(like),
                models.TicketOsticket.nombre_estudiante_osticket.like(like),
                models.TicketOsticket.codigo_alumno_osticket.like(like),
                models.TicketOsticket.email_estudiante.like(like),
                models.TicketOsticket.cuerpo.like(like),
            )
        )
        .order_by(models.TicketOsticket.fecha_creacion_osticket.desc())
        .limit(limite)
        .all()
    )
    expedientes = (
        db.query(models.ExpedienteTesis)
        .filter(
            or_(
                models.ExpedienteTesis.nombre_alumno.like(like),
                models.ExpedienteTesis.codigo_alumno.like(like),
                models.ExpedienteTesis.titulo_tesis.like(like),
            )
        )
        .order_by(models.ExpedienteTesis.fecha_ultimo_movimiento.desc())
        .limit(limite)
        .all()
    )
    docentes = (
        db.query(models.Docente)
        .filter(or_(models.Docente.nombre_completo.like(like), models.Docente.correo.like(like), models.Docente.dni.like(like)))
        .order_by(models.Docente.nombre_completo.asc())
        .limit(limite)
        .all()
    )
    resoluciones = (
        db.query(models.ResolucionDocumento)
        .filter(
            or_(
                models.ResolucionDocumento.resolucion_numero.like(like),
                models.ResolucionDocumento.nombre_alumno.like(like),
                models.ResolucionDocumento.codigo_alumno.like(like),
                models.ResolucionDocumento.titulo_tesis.like(like),
                models.ResolucionDocumento.tipo_resolucion.like(like),
            )
        )
        .order_by(models.ResolucionDocumento.fecha_resolucion.desc())
        .limit(limite)
        .all()
    )
    adjuntos = (
        db.query(models.TicketAdjunto)
        .filter(models.TicketAdjunto.nombre_archivo.like(like))
        .order_by(models.TicketAdjunto.id_adjunto.desc())
        .limit(limite)
        .all()
    )

    return {
        "q": texto,
        "tickets": [
            {
                "tipo": "ticket",
                "id": t.ticket_id,
                "uuid": t.uuid,
                "titulo": f"Ticket {t.numero_visual}",
                "subtitulo": t.asunto,
                "detalle": t.nombre_estudiante_osticket or t.codigo_alumno_osticket or t.email_estudiante,
                "ruta": f"/bandeja/{t.uuid}",
            }
            for t in tickets
        ],
        "expedientes": [
            {
                "tipo": "expediente",
                "id": e.id_expediente,
                "uuid": e.uuid,
                "titulo": e.nombre_alumno,
                "subtitulo": e.codigo_alumno,
                "detalle": e.titulo_tesis,
                "ruta": f"/expedientes/{e.uuid}",
            }
            for e in expedientes
        ],
        "docentes": [
            {
                "tipo": "docente",
                "id": d.id_docente,
                "titulo": d.nombre_completo,
                "subtitulo": d.correo,
                "detalle": d.especialidad,
                "ruta": "/docentes",
            }
            for d in docentes
        ],
        "resoluciones": [
            {
                "tipo": "resolucion",
                "id": r.id_documento,
                "titulo": r.resolucion_numero or r.archivo_normalizado,
                "subtitulo": r.nombre_alumno or r.codigo_alumno,
                "detalle": r.tipo_resolucion,
                "ruta": "/resoluciones",
            }
            for r in resoluciones
        ],
        "adjuntos": [
            {
                "tipo": "adjunto",
                "id": a.id_adjunto,
                "titulo": a.nombre_archivo,
                "subtitulo": f"Ticket {a.ticket.numero_visual}" if a.ticket else "",
                "detalle": a.ruta_local,
                "ruta": f"/bandeja/{a.ticket.uuid}" if a.ticket else "/bandeja",
            }
            for a in adjuntos
        ],
    }


@app.post("/api/tickets/{ticket_ref}/decision")
def registrar_decision_ticket(
    ticket_ref: str,
    decision: str = Query(
        ...,
        pattern="^(requiere_resolucion|resolucion_notificada|no_corresponde|transferir|cerrar_interno|reabrir)$",
    ),
    nota: Optional[str] = None,
    destino: Optional[str] = None,
    resolucion_ref: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_OPERACION, "registrar decisiones operativas")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    paso_ticket = int((paso_sugerido_ticket(ticket) or {}).get("id_paso") or 0)
    if decision == "requiere_resolucion" and paso_ticket in {4, 7}:
        raise HTTPException(
            status_code=409,
            detail=f"El paso {paso_ticket} se gestiona en ERP; no corresponde tramitarlo desde Mesa de Partes.",
        )
    if decision == "transferir" and not (destino or "").strip():
        raise HTTPException(status_code=400, detail="Indica el destino de la transferencia local.")
    if decision == "resolucion_notificada":
        exigir_rol(current_user, ROLES_AUTORIZACION, "confirmar una resolucion")
        relacion, _ = proponer_resolucion(db, ticket, resolucion_ref, current_user, nota)
        item = confirmar_resolucion(db, ticket, relacion, current_user, nota)
        decision_data = serializar_ticket_resolucion(item)
    else:
        item = registrar_decision(db, ticket, decision, current_user, nota, destino, resolucion_ref)
        decision_data = serializar_decision(item)
    # El destino operativo debe reflejar la decisión, no quedarse como una
    # etiqueta JSON que continúe contaminando la bandeja diaria.
    if decision == "cerrar_interno":
        ticket.estado_operativo = "Archivado_historico"
    elif decision == "no_corresponde":
        ticket.estado_operativo = "Fuera_proceso"
    elif decision == "reabrir":
        ticket.estado_operativo = "Activo"
    tramite = None
    tramite_creado = False
    if decision == "requiere_resolucion" and ticket.id_expediente:
        tramite, tramite_creado = enviar_ticket_a_secretaria(db, ticket, current_user)
    if ticket.id_expediente:
        exp = db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.id_expediente == ticket.id_expediente).first()
        if exp:
            registrar_movimiento(
                db,
                exp,
                "Clasificado",
                f"Decision ticket #{ticket.numero_visual}: {decision}. {nota or ''}",
                current_user.nombre_completo,
            )
    db.commit()
    return {
        "status": "ok",
        "ticket_id": ticket.ticket_id,
        "decision": decision_data,
        "estado": ticket.estado_scraping,
        "situacion_operativa": situacion_operativa_ticket(ticket),
        "tramite": serializar_tramite(tramite, detalle=True) if tramite else None,
        "tramite_creado": tramite_creado,
    }


@app.get("/api/tickets/{ticket_ref}/trazabilidad")
def obtener_trazabilidad_ticket(ticket_ref: str, db: Session = Depends(get_db)):
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    return {
        "ticket_id": ticket.ticket_id,
        "decisiones": [serializar_decision(item) for item in ticket.decisiones_normalizadas],
        "acciones": [serializar_accion(item) for item in ticket.acciones_normalizadas],
        "resoluciones": [serializar_ticket_resolucion(item) for item in ticket.resoluciones_ticket],
    }


@app.post("/api/tickets/{ticket_ref}/resoluciones/proponer")
def proponer_resolucion_ticket(
    ticket_ref: str,
    resolucion_ref: str,
    nota: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_OPERACION, "proponer una resolucion")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    relacion, creada = proponer_resolucion(db, ticket, resolucion_ref, current_user, nota)
    db.commit()
    return {"status": "creada" if creada else "actualizada", "relacion": serializar_ticket_resolucion(relacion)}


@app.post("/api/tickets/{ticket_ref}/resoluciones/{id_relacion}/confirmar")
def confirmar_resolucion_ticket(
    ticket_ref: str,
    id_relacion: int,
    nota: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_AUTORIZACION, "confirmar una resolucion")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    relacion = db.query(models.TicketResolucion).filter(
        models.TicketResolucion.id_ticket_resolucion == id_relacion,
        models.TicketResolucion.ticket_id == ticket.ticket_id,
    ).first()
    if not relacion:
        raise HTTPException(status_code=404, detail="Propuesta de resolucion no encontrada.")
    relacion = confirmar_resolucion(db, ticket, relacion, current_user, nota)
    if ticket.expediente:
        registrar_movimiento(db, ticket.expediente, "Clasificado", f"Resolucion confirmada para ticket #{ticket.numero_visual}.", current_user.nombre_completo)
    db.commit()
    return {"status": "ok", "relacion": serializar_ticket_resolucion(relacion)}


@app.post("/api/tickets/{ticket_ref}/resoluciones/{id_relacion}/descartar")
def descartar_resolucion_ticket(
    ticket_ref: str,
    id_relacion: int,
    nota: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_AUTORIZACION, "descartar una propuesta de resolucion")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    relacion = db.query(models.TicketResolucion).filter(
        models.TicketResolucion.id_ticket_resolucion == id_relacion,
        models.TicketResolucion.ticket_id == ticket.ticket_id,
    ).first()
    if not relacion:
        raise HTTPException(status_code=404, detail="Propuesta de resolucion no encontrada.")
    relacion = descartar_resolucion(db, ticket, relacion, current_user, nota)
    db.commit()
    return {"status": "ok", "relacion": serializar_ticket_resolucion(relacion)}


@app.get("/api/tickets/revision")
@app.get("/api/tickets-pendientes-vinculacion")
def listar_tickets_pendientes_vinculacion(
    busqueda: Optional[str] = None,
    estado: Optional[str] = Query(None),
    solo_con_adjuntos: bool = False,
    adjuntos: Optional[str] = Query(None, pattern="^(con|sin)$"),
    cola: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    cola_aplicada = cola or "sin_expediente"
    # La revisión humana muestra trabajo vivo. El archivo histórico se consulta
    # desde la Bandeja con su filtro explícito, nunca como una cola pendiente.
    tickets_activos = db.query(models.TicketOsticket).filter(
        models.TicketOsticket.estado_operativo == "Activo"
    )
    query = aplicar_filtro_situacion(tickets_activos, cola_aplicada)
    if estado:
        query = query.filter(models.TicketOsticket.estado_scraping == estado)
    if solo_con_adjuntos or adjuntos == "con":
        query = query.filter(models.TicketOsticket.adjuntos.any())
    elif adjuntos == "sin":
        query = query.filter(~models.TicketOsticket.adjuntos.any())
    if busqueda:
        like = f"%{busqueda.strip()}%"
        query = query.filter(
            or_(
                models.TicketOsticket.numero_visual.like(like),
                models.TicketOsticket.asunto.like(like),
                models.TicketOsticket.nombre_estudiante_osticket.like(like),
                models.TicketOsticket.codigo_alumno_osticket.like(like),
                models.TicketOsticket.email_estudiante.like(like),
                models.TicketOsticket.cuerpo.like(like),
                models.TicketOsticket.adjuntos.any(models.TicketAdjunto.nombre_archivo.like(like)),
                models.TicketOsticket.expediente.has(
                    or_(
                        models.ExpedienteTesis.nombre_alumno.like(like),
                        models.ExpedienteTesis.codigo_alumno.like(like),
                        models.ExpedienteTesis.titulo_tesis.like(like),
                    )
                ),
            )
        )

    total, total_pages, tickets = paginar(
        query.order_by(models.TicketOsticket.fecha_creacion_osticket.desc()),
        page,
        per_page,
    )

    base_pendientes = aplicar_filtro_situacion(tickets_activos, "requiere_accion")
    total_pendientes = base_pendientes.count()
    pendientes_con_adjuntos = base_pendientes.filter(models.TicketOsticket.adjuntos.any()).count()
    resumen_estados = {
        estado or "Sin estado": total
        for estado, total in db.query(
            models.TicketOsticket.estado_scraping,
            func.count(models.TicketOsticket.ticket_id),
        )
        .filter(
            models.TicketOsticket.estado_operativo == "Activo",
            models.TicketOsticket.estado_scraping != "Notificado",
        )
        .group_by(models.TicketOsticket.estado_scraping)
        .all()
    }
    claves_colas = [
        "por_clasificar",
        "requiere_resolucion",
        "en_tramite_resolucion",
        "fuera_proceso",
        "posible_expediente",
        "sin_expediente",
        "falta_resolucion",
        "error_extraccion",
        "pendiente_adjuntos",
        "pendiente_transferencia",
        "atendido_con_resolucion",
    ]
    conteos_colas = {
        clave: aplicar_filtro_situacion(tickets_activos, clave).count()
        for clave in claves_colas
    }

    data = []
    for ticket in tickets:
        datos = ticket.datos_extraidos or {}
        vinculacion = datos.get("vinculacion") or {}
        item = serializar_ticket(ticket)
        item.update(
            {
                "motivo": vinculacion.get("motivo") or situacion_operativa_ticket(ticket),
                "vinculacion": vinculacion,
            }
        )
        data.append(item)

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "resumen": {
            "pendientes": total_pendientes,
            "con_adjuntos": pendientes_con_adjuntos,
            "sin_adjuntos": total_pendientes - pendientes_con_adjuntos,
            "estados": resumen_estados,
            "colas": conteos_colas,
        },
        "cola": cola_aplicada,
        "data": data,
    }


@app.get("/api/resoluciones")
def listar_resoluciones(
    estado: Optional[str] = Query(None),
    vista: Optional[str] = Query(None, pattern="^(oficial|revision|diagnostico|descartado)$"),
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    id_paso: Optional[int] = Query(None, ge=1, le=7),
    tipo: Optional[str] = None,
    busqueda: Optional[str] = None,
    orden: str = Query("fecha_desc", pattern="^(fecha_desc|fecha_asc|numero_desc|numero_asc|estudiante_asc|programa_asc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    query = db.query(models.ResolucionDocumento)
    if anio:
        query = query.filter(models.ResolucionDocumento.resolucion_anio == anio)
    if id_paso:
        query = query.filter(models.ResolucionDocumento.id_paso_inferido == id_paso)
    if tipo:
        query = query.filter(models.ResolucionDocumento.tipo_resolucion.like(f"%{tipo.strip()}%"))
    if busqueda:
        like = f"%{busqueda.strip()}%"
        query = query.filter(
            or_(
                models.ResolucionDocumento.codigo_alumno.like(like),
                models.ResolucionDocumento.nombre_alumno.like(like),
                models.ResolucionDocumento.resolucion_numero.like(like),
                models.ResolucionDocumento.tipo_resolucion.like(like),
                models.ResolucionDocumento.programa.like(like),
                models.ResolucionDocumento.observaciones.like(like),
            )
        )

    # El staging historico contiene tambien actas, compilados y archivos vacios.
    # No deben presentarse como miles de resoluciones pendientes de Secretaria.
    revision_prioritaria = and_(
        models.ResolucionDocumento.estado_revision == "Observado",
        models.ResolucionDocumento.resolucion_numero.isnot(None),
        models.ResolucionDocumento.resolucion_anio.isnot(None),
        models.ResolucionDocumento.fecha_resolucion.isnot(None),
        models.ResolucionDocumento.nombre_alumno.isnot(None),
        models.ResolucionDocumento.texto_preview.like("%RESOLUCI%"),
    )
    resolucion_utilizable = models.ResolucionDocumento.estado_revision.in_(["OK", "Importado"])

    resumen_control = {
        "utilizables": query.filter(resolucion_utilizable).count(),
        "revision_prioritaria": query.filter(revision_prioritaria).count(),
        "diagnostico_extraccion": query.filter(
            models.ResolucionDocumento.estado_revision == "Observado",
            ~revision_prioritaria,
        ).count(),
        "documentos_ajenos": query.filter(
            models.ResolucionDocumento.estado_revision == "Descartado"
        ).count(),
    }

    if estado:
        query = query.filter(models.ResolucionDocumento.estado_revision == estado)
    elif vista == "oficial":
        query = query.filter(resolucion_utilizable)
    elif vista == "revision":
        query = query.filter(revision_prioritaria)
    elif vista == "diagnostico":
        query = query.filter(
            models.ResolucionDocumento.estado_revision == "Observado",
            ~revision_prioritaria,
        )
    elif vista == "descartado":
        query = query.filter(models.ResolucionDocumento.estado_revision == "Descartado")

    ordenes = {
        "fecha_desc": (models.ResolucionDocumento.fecha_resolucion.desc(), models.ResolucionDocumento.resolucion_numero.desc()),
        "fecha_asc": (models.ResolucionDocumento.fecha_resolucion.asc(), models.ResolucionDocumento.resolucion_numero.asc()),
        "numero_desc": (models.ResolucionDocumento.resolucion_anio.desc(), models.ResolucionDocumento.resolucion_numero.desc()),
        "numero_asc": (models.ResolucionDocumento.resolucion_anio.asc(), models.ResolucionDocumento.resolucion_numero.asc()),
        "estudiante_asc": (models.ResolucionDocumento.nombre_alumno.asc(), models.ResolucionDocumento.fecha_resolucion.desc()),
        "programa_asc": (models.ResolucionDocumento.programa.asc(), models.ResolucionDocumento.nombre_alumno.asc()),
    }
    total, total_pages, resoluciones = paginar(query.order_by(*ordenes[orden]), page, per_page)
    resumen = {
        estado or "Sin estado": total
        for estado, total in db.query(
            models.ResolucionDocumento.estado_revision,
            func.count(models.ResolucionDocumento.id_documento),
        ).group_by(models.ResolucionDocumento.estado_revision).all()
    }
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "resumen": resumen,
        "resumen_control": resumen_control,
        "data": [
            {
                "id_documento": r.id_documento,
                "source_path": r.source_path,
                "archivo_normalizado": r.archivo_normalizado,
                "resolucion_numero": r.resolucion_numero,
                "resolucion_anio": r.resolucion_anio,
                "fecha_resolucion": r.fecha_resolucion.isoformat() if r.fecha_resolucion else None,
                "expediente_admin": r.expediente_admin,
                "codigo_alumno": r.codigo_alumno,
                "nombre_alumno": r.nombre_alumno,
                "grado_postula": r.grado_postula,
                "programa": r.programa,
                "titulo_tesis": r.titulo_tesis,
                "tipo_resolucion": r.tipo_resolucion,
                "id_paso_inferido": r.id_paso_inferido,
                "estado_revision": r.estado_revision,
                "observaciones": r.observaciones,
                "texto_preview": r.texto_preview,
                "api_archivo_url": f"/resolucion-documentos/{r.id_documento}/archivo",
            }
            for r in resoluciones
        ],
    }


@app.put("/api/resoluciones/{id_documento}")
def actualizar_resolucion(
    id_documento: int,
    estado_revision: Optional[str] = Query(None),
    observaciones: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_directora_o_admin),
):
    doc = db.query(models.ResolucionDocumento).filter(
        models.ResolucionDocumento.id_documento == id_documento
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Resolucion no encontrada")
    if estado_revision:
        if estado_revision not in {"OK", "Observado"}:
            raise HTTPException(status_code=400, detail="Estado no permitido")
        doc.estado_revision = estado_revision
    if observaciones is not None:
        doc.observaciones = observaciones
    db.commit()
    return {"ok": True, "id_documento": doc.id_documento, "estado_revision": doc.estado_revision}


@lru_cache(maxsize=1)
def indice_archivos_resolucion_locales():
    raices = [ROOT / "data" / "drive_resoluciones" / "raw", Path("/opt/CARPETA DE SECRETARÍA ACADEMICA")]
    indice = defaultdict(list)
    for raiz in raices:
        if not raiz.exists():
            continue
        for ruta in raiz.rglob("*"):
            if ruta.is_file() and ruta.suffix.lower() in {".pdf", ".doc", ".docx"}:
                indice[ruta.name.lower()].append(ruta.resolve())
    return dict(indice)


@app.get("/api/resolucion-documentos/{id_documento}/archivo")
def abrir_archivo_resolucion_documental(
    id_documento: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    documento = db.query(models.ResolucionDocumento).filter(models.ResolucionDocumento.id_documento == id_documento).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Resolución documental no encontrada.")
    referencia = Path((documento.source_path or documento.archivo_normalizado or "").strip())
    permitidas = [
        (ROOT / "data" / "drive_resoluciones" / "raw").resolve(),
        Path("/opt/CARPETA DE SECRETARÍA ACADEMICA").resolve(),
    ]
    candidatos = []
    if referencia.is_absolute():
        candidatos.append(referencia.resolve())
    else:
        candidatos.extend((raiz / referencia).resolve() for raiz in permitidas)
    candidatos.extend(indice_archivos_resolucion_locales().get(referencia.name.lower(), []))
    ruta = next(
        (
            candidata for candidata in candidatos
            if candidata.is_file() and any(raiz == candidata.parent or raiz in candidata.parents for raiz in permitidas)
        ),
        None,
    )
    if not ruta:
        raise HTTPException(status_code=404, detail="El archivo de esta resolución no está disponible localmente.")
    tipo = "application/pdf" if ruta.suffix.lower() == ".pdf" else None
    return FileResponse(ruta, filename=ruta.name, media_type=tipo, content_disposition_type="inline")


@app.get("/api/tickets/{ticket_ref}")
def obtener_ticket_detalle(ticket_ref: str, db: Session = Depends(get_db)):
    return serializar_ticket_detalle_operativo(db, obtener_ticket_por_ref(db, ticket_ref))


@app.get("/api/tickets/{ticket_ref}/adjuntos/{id_adjunto}/archivo")
def abrir_adjunto_ticket(
    ticket_ref: str,
    id_adjunto: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    adjunto = db.query(models.TicketAdjunto).filter(
        models.TicketAdjunto.id_adjunto == id_adjunto,
        models.TicketAdjunto.ticket_id == ticket.ticket_id,
    ).first()
    if not adjunto:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado para este ticket.")
    return FileResponse(
        ruta_local_segura_adjunto(adjunto),
        filename=adjunto.nombre_archivo,
        content_disposition_type="inline",
    )


@app.get("/api/catalogos/tipos-resolucion")
def listar_tipos_resolucion(
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    return {"data": catalogo_tipos_resolucion()}


@app.get("/api/tickets/{ticket_ref}/mesa-tramite")
def obtener_mesa_tramite_ticket(
    ticket_ref: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    return contexto_mesa_tramite(db, ticket, serializar_requisito)


@app.post("/api/tickets/{ticket_ref}/preparar-derivacion")
def preparar_derivacion_ticket(
    ticket_ref: str,
    payload: PrepararDerivacionTicketPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_OPERACION, "derivar tickets a Secretaría Académica")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    if not ticket.id_expediente:
        raise HTTPException(status_code=409, detail="Primero vincula o crea el expediente desde esta misma mesa.")
    decision = decision_actual_ticket(ticket).get("decision")
    if decision != "requiere_resolucion":
        registrar_decision(db, ticket, "requiere_resolucion", current_user, payload.nota, origen="mesa_tramite")
    tramite, creado = enviar_ticket_a_secretaria(
        db,
        ticket,
        current_user,
        id_paso=payload.id_paso,
        tipo_resolucion=payload.tipo_resolucion,
        referencia_origen=payload.referencia_origen,
        confirmar_tramite_intermedio=payload.confirmar_tramite_intermedio,
    )
    if not tramite:
        raise HTTPException(status_code=409, detail="El ticket ya fue atendido con una resolución confirmada.")
    db.commit()
    db.refresh(tramite)
    return {
        "status": "ok",
        "creado": creado,
        "mensaje": f"Ticket #{ticket.numero_visual} enviado a Secretaría como P{tramite.id_paso}.",
        "tramite": serializar_tramite(tramite, detalle=True),
    }


@app.post("/api/tickets/{ticket_ref}/vincular-expediente")
def vincular_ticket_a_expediente(
    ticket_ref: str,
    expediente_ref: str,
    nota: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_OPERACION, "vincular tickets")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    expediente = obtener_expediente_por_ref(db, expediente_ref)
    vincular_ticket_existente(
        db,
        ticket,
        expediente,
        current_user.nombre_completo,
        criterio="seleccion_usuario",
        nota=nota,
    )
    registrar_accion(
        db, ticket, "vinculado_expediente", current_user, nota,
        {"id_expediente": expediente.id_expediente, "criterio": "seleccion_usuario"},
    )
    db.commit()
    return {
        "status": "ok",
        "ticket_id": ticket.ticket_id,
        "id_expediente": expediente.id_expediente,
        "expediente_uuid": expediente.uuid,
        "estado": ticket.estado_scraping,
    }


@app.post("/api/tickets/{ticket_ref}/crear-expediente-inicial")
def crear_expediente_inicial_desde_ticket(
    ticket_ref: str,
    payload: CrearExpedienteInicialPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Crea y deriva el primer expediente; la clasificación queda trazada automáticamente."""
    exigir_rol(current_user, ROLES_OPERACION, "crear expedientes iniciales")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    if ticket.id_expediente:
        raise HTTPException(status_code=409, detail="El ticket ya está vinculado a un expediente.")
    decision_previa = decision_actual_ticket(ticket).get("decision")
    if decision_previa and decision_previa not in {"requiere_resolucion", "reabrir"}:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede crear un expediente mientras el ticket está marcado como '{decision_previa}'. Reábrelo o corrige la decisión.",
        )
    if decision_previa != "requiere_resolucion":
        registrar_decision(
            db,
            ticket,
            "requiere_resolucion",
            current_user,
            "Decisión registrada automáticamente al crear el expediente inicial.",
        )

    nombre = normalizar_nombre_persona(payload.nombre_alumno)
    codigo = normalizar_codigo_alumno(payload.codigo_alumno)
    if not nombre or not codigo:
        raise HTTPException(status_code=400, detail="Nombre o código de alumno no válido.")

    existente, criterio = buscar_expediente_existente(db, codigo=codigo, nombre=nombre)
    if existente:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Ya existe el expediente #{existente.id_expediente} para este alumno "
                f"(coincidencia por {criterio}). Revisa y vincula el ticket existente."
            ),
        )

    paso = db.query(models.PasoFlujo).filter(models.PasoFlujo.id_paso == payload.id_paso).first()
    if not paso:
        raise HTTPException(status_code=400, detail="Paso de flujo inválido.")

    expediente = models.ExpedienteTesis(
        codigo_alumno=codigo,
        nombre_alumno=nombre,
        grado_postula=payload.grado_postula,
        programa=payload.programa.strip() if payload.programa else None,
        titulo_tesis=payload.titulo_tesis.strip() if payload.titulo_tesis else None,
        id_paso_actual=payload.id_paso,
        estado_expediente="En Proceso",
        sub_estado="Inicial_desde_ticket",
    )
    db.add(expediente)
    db.flush()
    docente, coincidencia_asesor = resolver_docente_por_nombre(db, payload.nombre_asesor)
    if docente:
            db.add(models.AsignacionTesis(
                id_expediente=expediente.id_expediente,
                id_docente=docente.id_docente,
                rol_asignado="Asesor",
                estado_asignacion="Activo",
            ))
    inicializar_requisitos_expediente(db, expediente)
    ticket.id_expediente = expediente.id_expediente
    ticket.estado_scraping = "Clasificado"
    datos = dict(ticket.datos_extraidos or {})
    datos["vinculacion"] = {
        "id_expediente": expediente.id_expediente,
        "uuid": expediente.uuid,
        "criterio": "expediente_inicial_desde_ticket",
        "estado": "vinculado_manual",
        "fecha": datetime.utcnow().isoformat(),
        "usuario": current_user.nombre_completo,
    }
    if payload.nombre_asesor:
        datos["asesor_detectado"] = coincidencia_asesor
    ticket.datos_extraidos = datos
    nota = payload.nota or f"Expediente inicial creado desde ticket #{ticket.numero_visual}."
    agregar_accion_local(
        ticket,
        "expediente_inicial_creado",
        current_user.nombre_completo,
        nota,
        id_expediente=expediente.id_expediente,
        id_paso=payload.id_paso,
    )
    registrar_accion(
        db,
        ticket,
        "expediente_inicial_creado",
        current_user,
        nota,
        {"id_expediente": expediente.id_expediente, "id_paso": payload.id_paso},
    )
    registrar_movimiento(
        db,
        expediente,
        "Creado",
        f"Creado desde ticket #{ticket.numero_visual}; paso inicial P{payload.id_paso} ({paso.nombre_paso}).",
        current_user.nombre_completo,
    )
    tramite, tramite_creado = enviar_ticket_a_secretaria(
        db, ticket, current_user, id_paso=payload.id_paso,
    )
    db.commit()
    db.refresh(expediente)
    return {
        "status": "ok",
        "mensaje": f"Expediente inicial #{expediente.id_expediente} creado y ticket vinculado.",
        "id_expediente": expediente.id_expediente,
        "uuid": expediente.uuid,
        "id_paso": expediente.id_paso_actual,
        "requisitos_creados": len(expediente.requisitos),
        "tramite": serializar_tramite(tramite, detalle=True) if tramite else None,
        "tramite_creado": tramite_creado,
    }


@app.post("/api/tickets/{ticket_ref}/enviar-secretaria")
def enviar_ticket_clasificado_a_secretaria(
    ticket_ref: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Normaliza los tickets antiguos clasificados antes del enrutamiento automático."""
    exigir_rol(current_user, ROLES_OPERACION, "derivar tickets a Secretaría Académica")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    if decision_actual_ticket(ticket).get("decision") != "requiere_resolucion":
        raise HTTPException(status_code=409, detail="Primero confirma que el ticket requiere resolución.")
    if not ticket.id_expediente:
        raise HTTPException(status_code=409, detail="Primero vincula o crea el expediente inicial.")
    tramite, creado = enviar_ticket_a_secretaria(db, ticket, current_user)
    if not tramite:
        raise HTTPException(status_code=409, detail="El ticket ya tiene una resolución confirmada o no puede derivarse.")
    db.commit()
    db.refresh(tramite)
    return {"status": "ok", "creado": creado, "tramite": serializar_tramite(tramite, detalle=True)}


@app.post("/api/tickets/{ticket_ref}/desvincular-expediente")
def desvincular_ticket_de_expediente(
    ticket_ref: str,
    confirmar: bool = False,
    nota: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_OPERACION, "desvincular tickets")
    if not confirmar:
        raise HTTPException(status_code=400, detail="Confirma explicitamente la desvinculacion.")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    if not ticket.id_expediente:
        return {"status": "sin_cambios", "ticket_id": ticket.ticket_id}

    expediente = ticket.expediente
    id_anterior = ticket.id_expediente
    datos = dict(ticket.datos_extraidos or {})
    datos["vinculacion"] = {
        "estado": "desvinculado_manual",
        "id_expediente_anterior": id_anterior,
        "fecha": datetime.utcnow().isoformat(),
        "usuario": current_user.nombre_completo,
        "motivo": nota,
    }
    ticket.datos_extraidos = datos
    agregar_accion_local(
        ticket,
        "desvinculado_expediente",
        current_user.nombre_completo,
        nota,
        id_expediente_anterior=id_anterior,
    )
    registrar_accion(
        db, ticket, "desvinculado_expediente", current_user, nota,
        {"id_expediente_anterior": id_anterior},
    )
    ticket.id_expediente = None
    decision = decision_actual_ticket(ticket).get("decision")
    ticket.estado_scraping = "Notificado" if decision in {"no_corresponde", "cerrar_interno"} else "Datos_Extraidos"
    if expediente:
        registrar_movimiento(
            db,
            expediente,
            "Clasificado",
            nota or f"Ticket #{ticket.numero_visual} desvinculado manualmente.",
            current_user.nombre_completo,
        )
    db.commit()
    return {"status": "ok", "ticket_id": ticket.ticket_id, "estado": ticket.estado_scraping}


@app.get("/api/tickets/{ticket_ref}/extraer-datos")
def extraer_datos_ticket(ticket_ref: str, db: Session = Depends(get_db)):
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    datos = ejecutar_extraccion(db, ticket)
    return {
        "ticket_id": ticket.ticket_id,
        "uuid": ticket.uuid,
        "datos_estructurados": datos["datos_estructurados"],
        "resumen": datos["resumen"],
        "archivos_procesados": datos["archivos_procesados"],
        "detalle_archivos": datos["detalle_archivos"],
    }


@app.post("/api/tickets/{ticket_ref}/extraer-datos")
def extraer_datos_ticket_background(ticket_ref: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    background_tasks.add_task(ejecutar_extraccion_background, ticket.ticket_id)
    return {"status": "extraccion_iniciada", "ticket_id": ticket.ticket_id, "uuid": ticket.uuid}


@app.post("/api/tickets/{ticket_ref}/clasificar")
def clasificar_ticket(
    ticket_ref: str,
    id_paso: int,
    nombre_alumno: str,
    codigo_alumno: str,
    grado_postula: str,
    titulo_tesis: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_OPERACION, "clasificar tickets")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    paso = db.query(models.PasoFlujo).filter(models.PasoFlujo.id_paso == id_paso).first()
    if not paso:
        raise HTTPException(status_code=400, detail="Paso de flujo invalido")

    expediente, criterio = buscar_expediente_existente(db, codigo=codigo_alumno, nombre=nombre_alumno)
    if not expediente:
        raise HTTPException(
            status_code=404,
            detail=(
                "No existe expediente oficial para ese codigo/nombre. "
                "Primero debe entrar por resolucion o por carga historica validada."
            ),
        )

    nota_vinculacion = (
        f"Ticket #{ticket.numero_visual} vinculado por {criterio}. "
        f"Paso sugerido del ticket: {paso.nombre_paso}. "
        "No se creo ni modifico expediente desde ticket."
    )
    vincular_ticket_existente(
        db,
        ticket,
        expediente,
        current_user.nombre_completo,
        criterio=criterio or "datos_ingresados",
        nota=nota_vinculacion,
        id_paso_historial=id_paso,
    )
    registrar_accion(
        db, ticket, "vinculado_expediente", current_user, nota_vinculacion,
        {"id_expediente": expediente.id_expediente, "criterio": criterio or "datos_ingresados"},
    )
    db.commit()
    db.refresh(expediente)

    return {
        "status": "ok",
        "id_expediente": expediente.id_expediente,
        "uuid": expediente.uuid,
        "paso": paso.nombre_paso,
        "criterio": criterio,
        "mensaje": f"Ticket #{ticket.numero_visual} vinculado al expediente existente #{expediente.id_expediente}",
    }


@app.post("/api/tickets/{ticket_ref}/cambiar-estado")
def cambiar_estado(
    ticket_ref: str,
    nuevo_estado: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_AUTORIZACION, "cambiar el estado tecnico de un ticket")
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    ticket.estado_scraping = nuevo_estado
    db.commit()
    return {"status": "ok", "nuevo_estado": nuevo_estado}


@app.get("/api/expedientes")
def listar_expedientes(
    id_paso: Optional[int] = None,
    estado: Optional[str] = None,
    sub_estado: Optional[str] = None,
    busqueda: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    anio: Optional[int] = Query(None, ge=2000, le=2100),
    vence_en_dias: Optional[int] = Query(None, ge=1, le=730),
    antiguedad_anios: Optional[int] = Query(None, ge=1, le=20),
    requisitos: Optional[str] = Query(None, pattern="^(pendientes|observados|listos)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.ExpedienteTesis)
        .filter(expediente_visible_operativamente())
        .order_by(models.ExpedienteTesis.fecha_ultimo_movimiento.desc())
    )
    if id_paso:
        query = query.filter(models.ExpedienteTesis.id_paso_actual == id_paso)
    if estado:
        query = query.filter(models.ExpedienteTesis.estado_expediente == estado)
    if sub_estado:
        query = query.filter(models.ExpedienteTesis.sub_estado == sub_estado)
    if busqueda:
        like = f"%{busqueda.strip()}%"
        query = query.filter(
            or_(
                models.ExpedienteTesis.nombre_alumno.like(like),
                models.ExpedienteTesis.codigo_alumno.like(like),
                models.ExpedienteTesis.titulo_tesis.like(like),
            )
        )
    if fecha_desde:
        try:
            fd = datetime.strptime(fecha_desde, "%Y-%m-%d")
            query = query.filter(models.ExpedienteTesis.fecha_inicio_tramite >= fd)
        except ValueError:
            pass
    if fecha_hasta:
        try:
            fh = datetime.strptime(fecha_hasta, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(models.ExpedienteTesis.fecha_inicio_tramite <= fh)
        except ValueError:
            pass
    if anio:
        fecha_cohorte = func.coalesce(
            models.ExpedienteTesis.fecha_inicio_tramite,
            models.ExpedienteTesis.fecha_ultimo_movimiento,
        )
        query = query.filter(fecha_cohorte >= datetime(anio, 1, 1), fecha_cohorte < datetime(anio + 1, 1, 1))
    if vence_en_dias:
        _, ids_vigentes = obtener_vencimientos_expedientes(db, vence_en_dias, anio)
        query = query.filter(models.ExpedienteTesis.id_expediente.in_(ids_vigentes or [-1]))
    if antiguedad_anios:
        ahora = datetime.utcnow()
        try:
            limite_antiguedad = ahora.replace(year=ahora.year - antiguedad_anios)
        except ValueError:
            limite_antiguedad = ahora.replace(year=ahora.year - antiguedad_anios, month=2, day=28)
        query = query.filter(models.ExpedienteTesis.fecha_inicio_tramite <= limite_antiguedad)
    if requisitos:
        if requisitos == "observados":
            query = query.join(models.ExpedienteRequisito).join(models.RequisitoPasoCatalogo).filter(
                models.RequisitoPasoCatalogo.id_paso == models.ExpedienteTesis.id_paso_actual,
                models.RequisitoPasoCatalogo.obligatorio == True,
                models.ExpedienteRequisito.estado == "Observado",
            )
        elif requisitos == "pendientes":
            query = query.join(models.ExpedienteRequisito).join(models.RequisitoPasoCatalogo).filter(
                models.RequisitoPasoCatalogo.id_paso == models.ExpedienteTesis.id_paso_actual,
                models.RequisitoPasoCatalogo.obligatorio == True,
                models.ExpedienteRequisito.estado.notin_(["Validado", "No_Aplica"]),
            )
        else:
            # Expedientes que no tienen requisitos obligatorios bloqueando el paso actual.
            bloqueos = (
                db.query(models.ExpedienteRequisito.id_expediente)
                .join(models.RequisitoPasoCatalogo)
                .join(
                    models.ExpedienteTesis,
                    models.ExpedienteTesis.id_expediente == models.ExpedienteRequisito.id_expediente,
                )
                .filter(
                    models.RequisitoPasoCatalogo.id_paso == models.ExpedienteTesis.id_paso_actual,
                    models.RequisitoPasoCatalogo.obligatorio == True,
                    models.ExpedienteRequisito.estado.notin_(["Validado", "No_Aplica"]),
                )
            )
            query = query.filter(~models.ExpedienteTesis.id_expediente.in_(bloqueos))
        query = query.distinct()

    total, total_pages, expedientes = paginar(query, page, per_page)
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": [serializar_expediente_lista(exp) for exp in expedientes],
    }


def _serializar_trayectoria_persona(
    db: Session,
    trayectoria: models.TrayectoriaAcademica,
    incluir_documentos: bool = False,
) -> dict:
    """Resume una trayectoria sin confundirla con otras de la misma persona."""
    relaciones = (
        db.query(models.ExpedienteTrayectoriaHistorica)
        .filter(models.ExpedienteTrayectoriaHistorica.id_trayectoria == trayectoria.id_trayectoria)
        .all()
    )
    expedientes = []
    for relacion in relaciones:
        expediente = db.query(models.ExpedienteTesis).filter(
            models.ExpedienteTesis.id_expediente == relacion.id_expediente
        ).first()
        if expediente:
            expedientes.append(serializar_expediente_lista(expediente))

    documentos = []
    if incluir_documentos:
        filas_documento = (
            db.query(models.DocumentoTrayectoriaHistorica, models.ResolucionDocumento)
            .join(
                models.ResolucionDocumento,
                models.ResolucionDocumento.id_documento == models.DocumentoTrayectoriaHistorica.id_documento,
            )
            .filter(models.DocumentoTrayectoriaHistorica.id_trayectoria == trayectoria.id_trayectoria)
            .order_by(models.ResolucionDocumento.fecha_resolucion.desc())
            .limit(12)
            .all()
        )
        documentos = [
            {
                "id_documento": documento.id_documento,
                "numero": documento.resolucion_numero,
                "fecha": documento.fecha_resolucion.strftime("%Y-%m-%d") if documento.fecha_resolucion else None,
                "paso": documento.id_paso_inferido,
                "tipo": documento.tipo_resolucion,
                "archivo": documento.archivo_normalizado or Path(documento.source_path or "").name,
            }
            for _, documento in filas_documento
        ]

    tickets = (
        db.query(models.TicketOsticket)
        .filter(models.TicketOsticket.id_expediente.in_([item["id_expediente"] for item in expedientes] or [-1]))
        .order_by(models.TicketOsticket.fecha_creacion_osticket.desc())
        .all()
    )
    return {
        "id_trayectoria": trayectoria.id_trayectoria,
        "grado": trayectoria.grado_postula,
        "programa": trayectoria.programa,
        "modalidad": trayectoria.modalidad,
        "codigo": trayectoria.codigo_canonico,
        "titulo_tesis": trayectoria.titulo_tesis,
        "paso_actual": trayectoria.paso_actual_documentado,
        "fecha_ultima_resolucion": trayectoria.fecha_ultima_resolucion.strftime("%Y-%m-%d") if trayectoria.fecha_ultima_resolucion else None,
        "estado": trayectoria.estado_migracion,
        "expedientes": expedientes,
        "tickets": [
            {
                "ticket_id": ticket.ticket_id,
                "uuid": ticket.uuid,
                "numero_visual": ticket.numero_visual,
                "asunto": ticket.asunto,
                "estado": ticket.estado_operativo,
            }
            for ticket in tickets[:8]
        ],
        "total_documentos": (
            db.query(models.DocumentoTrayectoriaHistorica)
            .filter(models.DocumentoTrayectoriaHistorica.id_trayectoria == trayectoria.id_trayectoria)
            .count()
        ),
        "documentos": documentos,
    }


@app.get("/api/estudiantes")
def listar_estudiantes(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Lista personas canónicas; cada programa/grado permanece como trayectoria propia."""
    query = db.query(models.PersonaAcademica)
    if q and q.strip():
        like = f"%{q.strip()}%"
        trayectorias_coincidentes = db.query(models.TrayectoriaAcademica.id_persona).filter(
            or_(
                models.TrayectoriaAcademica.nombre_alumno.like(like),
                models.TrayectoriaAcademica.codigo_canonico.like(like),
                models.TrayectoriaAcademica.programa.like(like),
                models.TrayectoriaAcademica.titulo_tesis.like(like),
            )
        )
        query = query.filter(
            or_(
                models.PersonaAcademica.nombre_canonico.like(like),
                models.PersonaAcademica.dni_canonico.like(like),
                models.PersonaAcademica.id_persona.in_(trayectorias_coincidentes),
            )
        )
    query = query.order_by(models.PersonaAcademica.nombre_canonico.asc())
    total, total_pages, personas = paginar(query, page, per_page)
    ids = [persona.id_persona for persona in personas]
    trayectorias_por_persona: dict[int, list[models.TrayectoriaAcademica]] = defaultdict(list)
    if ids:
        for trayectoria in db.query(models.TrayectoriaAcademica).filter(
            models.TrayectoriaAcademica.id_persona.in_(ids)
        ).all():
            trayectorias_por_persona[trayectoria.id_persona].append(trayectoria)
    data = []
    for persona in personas:
        trayectorias = trayectorias_por_persona[persona.id_persona]
        ultima = max((item.fecha_ultima_resolucion for item in trayectorias if item.fecha_ultima_resolucion), default=None)
        data.append({
            "id_persona": persona.id_persona,
            "nombre": persona.nombre_canonico,
            "dni": persona.dni_canonico,
            "estado_identidad": persona.estado_identidad,
            "trayectorias": len(trayectorias),
            "maestrias": sum(1 for item in trayectorias if item.grado_postula == "Maestro"),
            "doctorados": sum(1 for item in trayectorias if item.grado_postula == "Doctor"),
            "ultima_resolucion": ultima.strftime("%Y-%m-%d") if ultima else None,
        })
    return {"total": total, "page": page, "per_page": per_page, "total_pages": total_pages, "data": data}


@app.get("/api/estudiantes/{id_persona}")
def obtener_estudiante(
    id_persona: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    persona = db.query(models.PersonaAcademica).filter(models.PersonaAcademica.id_persona == id_persona).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    trayectorias = (
        db.query(models.TrayectoriaAcademica)
        .filter(models.TrayectoriaAcademica.id_persona == persona.id_persona)
        .order_by(models.TrayectoriaAcademica.fecha_ultima_resolucion.desc())
        .all()
    )
    return {
        "persona": {
            "id_persona": persona.id_persona,
            "nombre": persona.nombre_canonico,
            "dni": persona.dni_canonico,
            "estado_identidad": persona.estado_identidad,
        },
        "trayectorias": [_serializar_trayectoria_persona(db, item, incluir_documentos=True) for item in trayectorias],
    }


@app.get("/api/expedientes/{expediente_ref}")
def obtener_expediente(expediente_ref: str, db: Session = Depends(get_db)):
    return serializar_expediente_detalle(db, obtener_expediente_por_ref(db, expediente_ref))


@app.get("/api/expedientes/{expediente_ref}/requisitos")
def listar_requisitos_expediente(
    expediente_ref: str,
    id_paso: Optional[int] = None,
    incluir_eventos: bool = False,
    db: Session = Depends(get_db),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    requisitos = [item for item in exp.requisitos if not id_paso or item.requisito.id_paso == id_paso]
    return {
        "expediente_uuid": exp.uuid,
        "resumen": resumen_requisitos(exp),
        "data": [serializar_requisito(item, incluir_eventos) for item in requisitos],
    }


@app.post("/api/expedientes/{expediente_ref}/requisitos/inicializar")
def inicializar_requisitos_de_expediente(
    expediente_ref: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    creados = inicializar_requisitos_expediente(db, exp)
    db.commit()
    return {"status": "ok", "creados": creados, "resumen": resumen_requisitos(exp)}


@app.put("/api/expedientes/{expediente_ref}/requisitos/{id_expediente_requisito}")
def actualizar_requisito_expediente(
    expediente_ref: str,
    id_expediente_requisito: int,
    payload: ActualizarRequisitoPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    estado = payload.estado
    roles = ROLES_AUTORIZACION if estado in {"Validado", "Observado", "No_Aplica"} else ROLES_OPERACION
    exigir_rol(current_user, roles, "actualizar este requisito")
    exp = obtener_expediente_por_ref(db, expediente_ref)
    item = db.query(models.ExpedienteRequisito).filter(
        models.ExpedienteRequisito.id_expediente_requisito == id_expediente_requisito,
        models.ExpedienteRequisito.id_expediente == exp.id_expediente,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Requisito no encontrado para el expediente.")
    item = actualizar_requisito(
        db, exp, item, current_user,
        estado=payload.estado,
        evidencia_url=payload.evidencia_url,
        evidencia_nombre=payload.evidencia_nombre,
        fuente_evidencia=payload.fuente_evidencia,
        id_ticket=payload.id_ticket,
        id_adjunto=payload.id_adjunto,
        observacion=payload.observacion,
    )
    registrar_movimiento(
        db, exp, "Clasificado",
        f"Requisito {item.requisito.codigo}: {item.estado}. {item.observacion or ''}",
        current_user.nombre_completo,
    )
    db.commit()
    return {"status": "ok", "requisito": serializar_requisito(item, incluir_eventos=True), "resumen": resumen_requisitos(exp)}


def obtener_requisito_expediente(db, expediente, id_expediente_requisito):
    item = db.query(models.ExpedienteRequisito).filter(
        models.ExpedienteRequisito.id_expediente_requisito == id_expediente_requisito,
        models.ExpedienteRequisito.id_expediente == expediente.id_expediente,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="La caja documental no pertenece a este expediente.")
    return item


@app.post("/api/expedientes/{expediente_ref}/requisitos/{id_expediente_requisito}/archivos/asignar")
def asignar_adjunto_a_requisito(
    expediente_ref: str,
    id_expediente_requisito: int,
    payload: AsignarArchivoRequisitoPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_OPERACION, "clasificar archivos del ticket")
    expediente = obtener_expediente_por_ref(db, expediente_ref)
    item = obtener_requisito_expediente(db, expediente, id_expediente_requisito)
    adjunto = db.query(models.TicketAdjunto).filter(models.TicketAdjunto.id_adjunto == payload.id_adjunto).first()
    if not adjunto or not adjunto.ticket or adjunto.ticket.id_expediente != expediente.id_expediente:
        raise HTTPException(status_code=400, detail="El archivo debe pertenecer a un ticket vinculado a este expediente.")
    existente = db.query(models.ExpedienteRequisitoArchivo).filter(
        models.ExpedienteRequisitoArchivo.id_expediente_requisito == item.id_expediente_requisito,
        models.ExpedienteRequisitoArchivo.id_adjunto == adjunto.id_adjunto,
    ).first()
    if existente:
        return {"status": "sin_cambios", "requisito": serializar_requisito(item, incluir_eventos=True)}
    archivo = models.ExpedienteRequisitoArchivo(
        id_expediente_requisito=item.id_expediente_requisito,
        id_ticket=adjunto.ticket_id,
        id_adjunto=adjunto.id_adjunto,
        archivo_url=None,
        archivo_nombre=adjunto.nombre_archivo,
        fuente="ticket",
        estado=payload.estado,
        id_asignado_por=current_user.id_usuario,
        asignado_por_nombre=current_user.nombre_completo,
        asignado_por_rol=current_user.rol,
    )
    db.add(archivo)
    if item.estado == "Pendiente":
        actualizar_requisito(
            db, expediente, item, current_user,
            estado="Presentado", evidencia_nombre=adjunto.nombre_archivo,
            fuente_evidencia="ticket", id_ticket=adjunto.ticket_id, id_adjunto=adjunto.id_adjunto,
        )
    registrar_movimiento(
        db, expediente, "Clasificado",
        f"Archivo {adjunto.nombre_archivo} asignado al requisito {item.requisito.codigo}.",
        current_user.nombre_completo,
    )
    db.commit()
    return {"status": "ok", "requisito": serializar_requisito(item, incluir_eventos=True)}


@app.post("/api/expedientes/{expediente_ref}/requisitos/{id_expediente_requisito}/archivos/subir")
def subir_archivo_a_requisito(
    expediente_ref: str,
    id_expediente_requisito: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_OPERACION, "cargar archivos de requisitos")
    expediente = obtener_expediente_por_ref(db, expediente_ref)
    item = obtener_requisito_expediente(db, expediente, id_expediente_requisito)
    nombre_original = Path(archivo.filename or "archivo").name
    extension = Path(nombre_original).suffix.lower()
    permitidas = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".xls", ".xlsx"}
    if extension not in permitidas:
        raise HTTPException(status_code=400, detail="Formato no admitido. Usa PDF, Word, imagen o Excel.")
    contenido = archivo.file.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(contenido) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo supera el límite de 50 MB.")
    carpeta = Path(valor_configuracion("EPG_UPLOADS_DIR", "/opt/sistema_posgrado/uploads/expedientes"))
    carpeta = carpeta / expediente.uuid / "requisitos" / str(item.id_expediente_requisito)
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre_seguro = f"{uuid_lib.uuid4().hex[:12]}{extension}"
    destino = carpeta / nombre_seguro
    destino.write_bytes(contenido)
    registro = models.ExpedienteRequisitoArchivo(
        id_expediente_requisito=item.id_expediente_requisito,
        archivo_url=str(destino),
        archivo_nombre=nombre_original,
        fuente="carga_local",
        estado="Presentado",
        id_asignado_por=current_user.id_usuario,
        asignado_por_nombre=current_user.nombre_completo,
        asignado_por_rol=current_user.rol,
    )
    db.add(registro)
    db.flush()
    if item.estado == "Pendiente":
        actualizar_requisito(
            db, expediente, item, current_user,
            estado="Presentado", evidencia_nombre=nombre_original, fuente_evidencia="carga_local",
        )
    db.commit()
    return {"status": "ok", "requisito": serializar_requisito(item, incluir_eventos=True)}


@app.get("/api/expedientes/{expediente_ref}/requisitos-archivos/{id_requisito_archivo}/archivo")
def abrir_archivo_requisito(
    expediente_ref: str,
    id_requisito_archivo: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    expediente = obtener_expediente_por_ref(db, expediente_ref)
    registro = db.query(models.ExpedienteRequisitoArchivo).join(models.ExpedienteRequisito).filter(
        models.ExpedienteRequisitoArchivo.id_requisito_archivo == id_requisito_archivo,
        models.ExpedienteRequisito.id_expediente == expediente.id_expediente,
    ).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Archivo no encontrado para el expediente.")
    if registro.adjunto:
        return FileResponse(
            ruta_local_segura_adjunto(registro.adjunto),
            filename=registro.archivo_nombre,
            content_disposition_type="inline",
        )
    ruta = Path(registro.archivo_url or "").resolve()
    raiz = Path(valor_configuracion("EPG_UPLOADS_DIR", "/opt/sistema_posgrado/uploads/expedientes")).resolve()
    if not ruta.is_file() or raiz not in ruta.parents:
        raise HTTPException(status_code=404, detail="El archivo local no está disponible.")
    return FileResponse(ruta, filename=registro.archivo_nombre, content_disposition_type="inline")


@app.delete("/api/expedientes/{expediente_ref}/requisitos/{id_expediente_requisito}/archivos/{id_requisito_archivo}")
def quitar_archivo_de_requisito(
    expediente_ref: str,
    id_expediente_requisito: int,
    id_requisito_archivo: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exigir_rol(current_user, ROLES_OPERACION, "retirar archivos de requisitos")
    expediente = obtener_expediente_por_ref(db, expediente_ref)
    item = obtener_requisito_expediente(db, expediente, id_expediente_requisito)
    registro = db.query(models.ExpedienteRequisitoArchivo).filter(
        models.ExpedienteRequisitoArchivo.id_requisito_archivo == id_requisito_archivo,
        models.ExpedienteRequisitoArchivo.id_expediente_requisito == item.id_expediente_requisito,
    ).first()
    if not registro:
        raise HTTPException(status_code=404, detail="El archivo ya no está asignado a esta caja.")
    db.delete(registro)
    db.flush()
    restantes = db.query(models.ExpedienteRequisitoArchivo).filter(
        models.ExpedienteRequisitoArchivo.id_expediente_requisito == item.id_expediente_requisito
    ).count()
    if not restantes and item.estado == "Presentado":
        actualizar_requisito(db, expediente, item, current_user, estado="Pendiente", observacion="Archivo retirado de la caja documental.")
    db.commit()
    return {"status": "ok", "requisito": serializar_requisito(item, incluir_eventos=True)}


@app.post("/api/expedientes/{expediente_ref}/avanzar")
def avanzar_expediente(
    expediente_ref: str,
    nota: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)

    if exp.id_paso_actual >= 7:
        exp.estado_expediente = "Archivado_Graduado"
        exp.sub_estado = None
        exp.fecha_ultimo_movimiento = datetime.utcnow()
        registrar_movimiento(db, exp, "Archivado", nota or "Expediente completado. Alumno graduado.", current_user.nombre_completo)
        db.commit()
        return {"status": "graduado", "mensaje": "El expediente ha sido completado."}

    paso_siguiente = exp.id_paso_actual + 1
    paso_obj = db.query(models.PasoFlujo).filter(models.PasoFlujo.id_paso == paso_siguiente).first()
    exp.id_paso_actual = paso_siguiente
    exp.estado_expediente = "En Proceso"
    exp.sub_estado = None
    exp.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(
        db,
        exp,
        "Avanzado",
        nota or f"Aprobado. Avanzado a: {paso_obj.nombre_paso if paso_obj else paso_siguiente}",
        current_user.nombre_completo,
    )
    db.commit()
    return {"status": "ok", "nuevo_paso": paso_siguiente, "nombre_paso": paso_obj.nombre_paso if paso_obj else str(paso_siguiente)}


@app.post("/api/expedientes/{expediente_ref}/observar")
def observar_expediente(
    expediente_ref: str,
    nota: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    exp.estado_expediente = "Observado"
    exp.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(db, exp, "Observado", nota, current_user.nombre_completo)
    db.commit()
    return {"status": "ok", "mensaje": "Expediente marcado como observado"}


@app.post("/api/expedientes/{expediente_ref}/derivar-directora")
def derivar_directora(
    expediente_ref: str,
    nota: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    exp.sub_estado = "Derivado_Directora"
    exp.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(db, exp, "Derivado", nota or "Expediente derivado a Directora.", current_user.nombre_completo)
    db.commit()
    return {"status": "ok", "sub_estado": exp.sub_estado}


def guardar_upload_resolucion(exp, archivo: UploadFile) -> str:
    uploads_dir = Path(os.getenv("EPG_UPLOADS_DIR", "/opt/sistema_posgrado/uploads/expedientes"))
    carpeta = uploads_dir / str(exp.uuid) / "resoluciones"
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / archivo.filename
    with destino.open("wb") as f:
        f.write(archivo.file.read())
    public_base = os.getenv("EPG_UPLOADS_PUBLIC_URL", "https://dataepis.uandina.pe/expedientes")
    return f"{public_base}/{exp.uuid}/resoluciones/{archivo.filename}"


def guardar_archivo_tramite(tramite, archivo: UploadFile, tipo: str) -> tuple[str, str, str]:
    nombre_original = Path(archivo.filename or "archivo").name
    nombre_seguro = re.sub(r"[^0-9A-Za-z._-]", "_", nombre_original)
    extension = Path(nombre_seguro).suffix.lower()
    permitidas = {"word": {".doc", ".docx"}, "firmado": {".pdf"}}
    if extension not in permitidas[tipo]:
        esperado = "Word (.doc o .docx)" if tipo == "word" else "PDF"
        raise HTTPException(status_code=400, detail=f"El archivo debe ser {esperado}.")
    contenido = archivo.file.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(contenido) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo supera el límite de 50 MB.")
    if tipo == "firmado" and not contenido.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="El archivo firmado no tiene contenido PDF válido.")

    carpeta_base = Path(valor_configuracion("EPG_UPLOADS_DIR", "/opt/sistema_posgrado/uploads/expedientes"))
    carpeta = carpeta_base / tramite.expediente.uuid / "resoluciones-tramites" / tramite.uuid
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre_almacenado = f"{tipo}-{uuid_lib.uuid4().hex[:10]}{extension}"
    destino = carpeta / nombre_almacenado
    destino.write_bytes(contenido)
    public_base = valor_configuracion("EPG_UPLOADS_PUBLIC_URL", "https://dataepis.uandina.pe/expedientes")
    url = f"{public_base.rstrip('/')}/{tramite.expediente.uuid}/resoluciones-tramites/{tramite.uuid}/{nombre_almacenado}"
    return url, nombre_original, hashlib.sha256(contenido).hexdigest()


def guardar_borrador_generado(tramite, contenido: bytes) -> tuple[str, str, str, Path]:
    carpeta_base = Path(valor_configuracion("EPG_UPLOADS_DIR", "/opt/sistema_posgrado/uploads/expedientes"))
    carpeta = carpeta_base / tramite.expediente.uuid / "resoluciones-tramites" / tramite.uuid
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = f"word-generado-{uuid_lib.uuid4().hex[:10]}.docx"
    destino = carpeta / nombre
    destino.write_bytes(contenido)
    public_base = valor_configuracion("EPG_UPLOADS_PUBLIC_URL", "https://dataepis.uandina.pe/expedientes")
    url = f"{public_base.rstrip('/')}/{tramite.expediente.uuid}/resoluciones-tramites/{tramite.uuid}/{nombre}"
    return url, nombre, hash_contenido(contenido), destino


def _firma_onlyoffice(referencia: str, expiracion: int) -> str:
    mensaje = f"{referencia}:{expiracion}".encode("utf-8")
    return hmac.new(ONLYOFFICE_JWT_SECRET.encode("utf-8"), mensaje, hashlib.sha256).hexdigest()


def _validar_enlace_onlyoffice(referencia: str, expiracion: int, firma: str) -> None:
    if not ONLYOFFICE_HABILITADO:
        raise HTTPException(status_code=404, detail="El editor Word institucional no está habilitado.")
    if expiracion < int(datetime.utcnow().timestamp()) or expiracion > int((datetime.utcnow() + timedelta(hours=3)).timestamp()):
        raise HTTPException(status_code=403, detail="El enlace del editor Word venció.")
    esperada = _firma_onlyoffice(referencia, expiracion)
    if not firma or not hmac.compare_digest(esperada, firma):
        raise HTTPException(status_code=403, detail="Firma de editor Word inválida.")


def _ruta_borrador_word(tramite) -> Path:
    if not tramite.borrador_word_url:
        raise HTTPException(status_code=409, detail="Primero genera o carga un borrador Word para editarlo.")
    carpeta_base = Path(valor_configuracion("EPG_UPLOADS_DIR", "/opt/sistema_posgrado/uploads/expedientes")).resolve()
    nombre = Path(urlparse(tramite.borrador_word_url).path).name
    carpeta = (carpeta_base / tramite.expediente.uuid / "resoluciones-tramites" / tramite.uuid).resolve()
    ruta = (carpeta / nombre).resolve()
    if carpeta_base not in ruta.parents or not ruta.is_file() or ruta.suffix.lower() != ".docx":
        raise HTTPException(status_code=404, detail="El borrador Word no está disponible localmente.")
    return ruta


@app.get("/api/resolucion-tramites/{tramite_ref}/onlyoffice-config")
def obtener_configuracion_onlyoffice(
    tramite_ref: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    if not ONLYOFFICE_HABILITADO:
        raise HTTPException(status_code=503, detail="El editor Word institucional aún no está disponible.")
    tramite = obtener_tramite(db, tramite_ref)
    ruta = _ruta_borrador_word(tramite)
    expiracion = int((datetime.utcnow() + timedelta(minutes=75)).timestamp())
    firma = _firma_onlyoffice(tramite.uuid, expiracion)
    # El navegador habla con OnlyOffice por HTTPS público, pero el propio
    # servidor de documentos obtiene el DOCX por la red Docker interna. Así
    # no depende del certificado público ni expone el Word en otra ruta.
    url_documento = f"{ONLYOFFICE_CALLBACK_BASE}/api/onlyoffice/documento/{tramite.uuid}?expiracion={expiracion}&firma={firma}"
    url_callback = f"{ONLYOFFICE_CALLBACK_BASE}/api/onlyoffice/callback/{tramite.uuid}?expiracion={expiracion}&firma={firma}"
    llave = hashlib.sha256(f"{tramite.uuid}:{tramite.borrador_version}:{ruta.name}:{ruta.stat().st_mtime_ns}".encode("utf-8")).hexdigest()
    configuracion = {
        "document": {
            "fileType": "docx",
            "key": llave,
            "title": tramite.borrador_word_nombre or ruta.name,
            "url": url_documento,
            "permissions": {"edit": True, "download": True, "print": True},
        },
        "documentType": "word",
        "editorConfig": {
            "callbackUrl": url_callback,
            "lang": "es",
            "mode": "edit",
            "user": {"id": str(current_user.id_usuario), "name": current_user.nombre_completo},
            "customization": {"autosave": True, "forcesave": False, "compactToolbar": False},
        },
    }
    configuracion["token"] = jwt.encode(configuracion, ONLYOFFICE_JWT_SECRET, algorithm="HS256")
    return {
        "editor_api_url": f"{ONLYOFFICE_URL_PUBLICA}/web-apps/apps/api/documents/api.js",
        "configuracion": configuracion,
        "vence_en": datetime.utcfromtimestamp(expiracion).isoformat() + "Z",
    }


@app.get("/api/onlyoffice/documento/{tramite_ref}")
def descargar_borrador_para_onlyoffice(
    tramite_ref: str,
    expiracion: int,
    firma: str,
    db: Session = Depends(get_db),
):
    _validar_enlace_onlyoffice(tramite_ref, expiracion, firma)
    tramite = obtener_tramite(db, tramite_ref)
    ruta = _ruta_borrador_word(tramite)
    return FileResponse(ruta, filename=tramite.borrador_word_nombre or ruta.name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.post("/api/onlyoffice/callback/{tramite_ref}")
async def recibir_guardado_onlyoffice(
    tramite_ref: str,
    request: Request,
    expiracion: int,
    firma: str,
    db: Session = Depends(get_db),
):
    _validar_enlace_onlyoffice(tramite_ref, expiracion, firma)
    try:
        cuerpo = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="OnlyOffice envió una confirmación inválida.") from exc
    estado = int(cuerpo.get("status", 0) or 0)
    if estado in {1, 4, 6, 7}:
        return {"error": 0}
    if estado not in {2, 3}:
        return {"error": 0}
    if estado == 3:
        logger.warning("OnlyOffice no pudo guardar el borrador %s: %s", tramite_ref, cuerpo.get("error"))
        return {"error": 1}
    url_documento = (cuerpo.get("url") or "").strip()
    host_documento = (urlparse(url_documento).hostname or "").lower()
    host_publico = (urlparse(ONLYOFFICE_URL_PUBLICA).hostname or "").lower()
    if not url_documento or host_documento not in {host_publico, "localhost", "127.0.0.1", "host.docker.internal"}:
        logger.warning("OnlyOffice devolvió una URL de guardado no permitida para %s", tramite_ref)
        return {"error": 1}
    try:
        with urlopen(url_documento, timeout=60) as respuesta:
            contenido = respuesta.read(50 * 1024 * 1024 + 1)
    except Exception:
        logger.exception("No se pudo recuperar el Word editado desde OnlyOffice para %s", tramite_ref)
        return {"error": 1}
    if not contenido or len(contenido) > 50 * 1024 * 1024 or not contenido.startswith(b"PK"):
        logger.warning("OnlyOffice devolvió un Word inválido para %s", tramite_ref)
        return {"error": 1}
    tramite = obtener_tramite(db, tramite_ref)
    anterior = tramite.borrador_word_url
    url, nombre, contenido_hash, _ = guardar_borrador_generado(tramite, contenido)
    tramite.borrador_version = (tramite.borrador_version or 0) + 1
    tramite.borrador_word_url = url
    tramite.borrador_word_nombre = nombre
    tramite.fecha_actualizacion = datetime.utcnow()
    registrar_evento_tramite(
        db, tramite, "borrador_editado_en_servidor", None, tramite.estado,
        "Word editado directamente en el servidor mediante OnlyOffice.",
        {"version": tramite.borrador_version, "sha256": contenido_hash, "origen_anterior": anterior},
    )
    db.commit()
    return {"error": 0}


def _partes_numero_resolucion(numero: str) -> tuple[int | None, int | None]:
    """Extrae la pareja de control sin imponer cómo Secretaría escribe el sufijo."""
    numero_encontrado = re.search(r"\d{1,4}", numero or "")
    anio_encontrado = re.search(r"20\d{2}", numero or "")
    return (
        int(numero_encontrado.group()) if numero_encontrado else None,
        int(anio_encontrado.group()) if anio_encontrado else None,
    )


def inspeccionar_numeracion(db: Session, numero: str, tramite=None) -> dict:
    """Devuelve evidencia legible para decidir una numeración, sin modificar archivos históricos."""
    consecutivo, anio = _partes_numero_resolucion(numero)
    if consecutivo is None or anio is None:
        return {"valido": False, "bloquea": True, "mensaje": "Usa un número con año, por ejemplo 0766-2026/EPG-UAC.", "registros": []}

    registros = []
    documentos = db.query(models.ResolucionDocumento).filter(
        models.ResolucionDocumento.resolucion_anio == anio,
        models.ResolucionDocumento.estado_revision.in_(["OK", "Importado"]),
    ).all()
    for documento in documentos:
        numero_documento, _ = _partes_numero_resolucion(f"{documento.resolucion_numero or ''}-{anio}")
        if numero_documento != consecutivo or not es_documento_serie_epg_principal(documento, anio):
            continue
        registros.append({
            "origen": "Resolución firmada del archivo", "referencia": f"{documento.resolucion_numero}-{anio}",
            "estudiante": documento.nombre_alumno or "Sin estudiante extraído", "tipo": documento.tipo_resolucion or "Sin tipo extraído",
            "fecha": documento.fecha_resolucion.strftime("%Y-%m-%d") if documento.fecha_resolucion else None,
            "archivo_url": f"/resolucion-documentos/{documento.id_documento}/archivo", "bloqueante": True,
        })
    internos = db.query(models.ResolucionTramite).filter(models.ResolucionTramite.numero_resolucion.isnot(None)).all()
    for interno in internos:
        if tramite and interno.id_tramite == tramite.id_tramite:
            continue
        numero_interno, anio_interno = _partes_numero_resolucion(interno.numero_resolucion)
        if numero_interno != consecutivo or anio_interno != anio:
            continue
        registros.append({
            "origen": "Trámite interno", "referencia": interno.numero_resolucion,
            "estudiante": interno.expediente.nombre_alumno if interno.expediente else "Sin estudiante",
            "tipo": interno.tipo_resolucion, "fecha": interno.fecha_resolucion.strftime("%Y-%m-%d") if interno.fecha_resolucion else None,
            "estado": interno.estado, "bloqueante": True,
        })
    control = control_numeracion(db, anio)
    maximo = control.get("ultimo_numero_controlado") or 0
    es_hueco = not registros and consecutivo <= maximo
    return {
        "valido": True, "numero": consecutivo, "anio": anio, "registros": registros,
        "bloquea": bool(registros), "es_hueco": es_hueco, "siguiente_sugerido": control.get("siguiente_disponible"),
        "mensaje": (
            "El número ya está ocupado. Revisa la resolución indicada; no se reemplazará desde este trámite."
            if registros else "Este número quedó libre dentro de la serie anual; registra por qué se utiliza."
            if es_hueco else "Número disponible en el libro anual."
        ),
    }


def validar_numeracion_operativa(db: Session, tramite, numero: str, decision: str | None = None, nota: str | None = None) -> dict:
    inspeccion = inspeccionar_numeracion(db, numero, tramite)
    if inspeccion["bloquea"]:
        raise HTTPException(status_code=409, detail={"mensaje": inspeccion["mensaje"], "numeracion": inspeccion})
    if inspeccion["es_hueco"] and decision not in {"no_emitida", "archivo", "anulada"}:
        raise HTTPException(status_code=409, detail={"mensaje": "Este número deja una secuencia previa sin usar. Indica si fue no emitida, reservada para archivo o anulada.", "numeracion": inspeccion})
    if inspeccion["es_hueco"] and not (nota or "").strip():
        raise HTTPException(status_code=409, detail={"mensaje": "Describe brevemente la decisión de numeración para conservar la auditoría.", "numeracion": inspeccion})
    return inspeccion


def pdf_de_docx_para_vista_previa(contenido: bytes) -> bytes:
    """LibreOffice entrega una representación visual fiel sin publicar borradores temporales."""
    with tempfile.TemporaryDirectory(prefix="epg-vista-word-") as temporal:
        carpeta = Path(temporal)
        origen = carpeta / "vista-previa.docx"
        origen.write_bytes(contenido)
        entorno = {
            **os.environ,
            "HOME": temporal,
            # El servicio sólo expone el virtualenv en PATH; LibreOffice es un
            # script del sistema que también invoca utilidades de /usr/bin.
            "PATH": f"{os.environ.get('PATH', '')}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        }
        try:
            subprocess.run(
                [valor_configuracion("EPG_LIBREOFFICE_BIN", "/usr/bin/libreoffice"), "--headless", "--convert-to", "pdf", "--outdir", str(carpeta), str(origen)],
                check=True, capture_output=True, timeout=45, env=entorno,
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(status_code=503, detail="No se pudo preparar la vista visual del Word. Intenta nuevamente.") from exc
        destino = carpeta / "vista-previa.pdf"
        if not destino.exists():
            raise HTTPException(status_code=503, detail="LibreOffice no produjo la vista previa PDF.")
        return destino.read_bytes()


def obtener_modelo_resolucion(db: Session, id_modelo_documento: int, id_paso: int | None = None):
    modelo = db.query(models.ResolucionDocumento).filter(
        models.ResolucionDocumento.id_documento == id_modelo_documento
    ).first()
    if not modelo:
        raise HTTPException(status_code=404, detail="El modelo de resolución no existe.")
    if id_paso is not None and modelo.id_paso_inferido != id_paso:
        raise HTTPException(status_code=409, detail="El modelo elegido no corresponde al paso del trámite.")
    if not (modelo.texto_preview or "").strip():
        raise HTTPException(status_code=409, detail="El modelo no tiene texto suficiente para construir un borrador.")
    if not es_modelo_utilizable(modelo):
        raise HTTPException(status_code=409, detail="El documento es una rectificación, cambio o anulación y no puede usarse como modelo base.")
    return modelo


def validar_preparacion_generada(db: Session, tramite, modelo, numero: str, fecha: datetime, referencia_origen: str | None = None):
    if tramite.estado not in {"en_elaboracion_secretaria", "observado_por_direccion"}:
        raise HTTPException(status_code=409, detail="El trámite no está disponible para generar un borrador.")
    obtener_modelo_resolucion(db, modelo.id_documento, tramite.id_paso)
    duplicado = db.query(models.ResolucionTramite).filter(
        models.ResolucionTramite.numero_resolucion == numero,
        models.ResolucionTramite.id_tramite != tramite.id_tramite,
    ).first()
    if duplicado:
        raise HTTPException(status_code=409, detail="Ese número de resolución ya está asignado a otro trámite.")
    regla = regla_aplicada(db, tramite)
    if regla and regla.requiere_consulta_previa is False and tramite.consultas:
        raise HTTPException(status_code=409, detail="La regla aplicada no admite consulta previa; revisa las consultas existentes antes de continuar.")
    if tramite.id_paso == 4 and not (referencia_origen or tramite.referencia_origen):
        raise HTTPException(status_code=409, detail="El paso 4 requiere registrar la referencia ERP antes de generar el borrador.")
    return regla


def aplicar_borrador_generado(db: Session, tramite, modelo, contenido: str, numero: str, fecha: datetime, actor, referencia_origen: str | None = None):
    regla = validar_preparacion_generada(db, tramite, modelo, numero, fecha, referencia_origen)
    generado = crear_docx_borrador(contenido, tramite, modelo)
    url, nombre, contenido_hash, ruta = guardar_borrador_generado(tramite, generado)
    anterior = tramite.estado
    tramite.numero_resolucion = numero
    tramite.fecha_resolucion = fecha
    if tramite.vigencia_meses:
        tramite.fecha_vencimiento = sumar_meses(fecha, tramite.vigencia_meses)
    if referencia_origen is not None:
        tramite.referencia_origen = referencia_origen.strip() or None
    tramite.requiere_consulta_previa = regla.requiere_consulta_previa if regla and regla.requiere_consulta_previa is not None else tramite.requiere_consulta_previa
    tramite.borrador_version = (tramite.borrador_version or 0) + (1 if tramite.borrador_word_url else 0)
    tramite.borrador_word_url = url
    tramite.borrador_word_nombre = nombre
    if anterior == "observado_por_direccion":
        tramite.estado = "en_elaboracion_secretaria"
        tramite.observacion_actual = None
    tramite.fecha_actualizacion = datetime.utcnow()
    registrar_evento_tramite(
        db,
        tramite,
        "borrador_generado_desde_modelo",
        actor,
        anterior,
        "Borrador Word generado desde modelo institucional; requiere revisión antes de remitir.",
        {
            "id_modelo_documento": modelo.id_documento,
            "modelo_numero": modelo.resolucion_numero,
            "sha256": contenido_hash,
            "borrador_word_nombre": nombre,
        },
    )
    return ruta


def sumar_meses(fecha: datetime, meses: int) -> datetime:
    indice = fecha.month - 1 + meses
    anio = fecha.year + indice // 12
    mes = indice % 12 + 1
    dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
    return fecha.replace(year=anio, month=mes, day=dia)


def guardar_evidencia_consulta(consulta, archivo: UploadFile) -> tuple[str, str, str]:
    nombre_original = Path(archivo.filename or "evidencia").name
    extension = Path(nombre_original).suffix.lower()
    if extension not in {".pdf", ".doc", ".docx"}:
        raise HTTPException(status_code=400, detail="La evidencia debe ser PDF, DOC o DOCX.")
    contenido = archivo.file.read()
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo de evidencia está vacío.")
    if len(contenido) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="La evidencia supera el límite de 25 MB.")
    firmas = {".pdf": b"%PDF", ".docx": b"PK", ".doc": b"\xd0\xcf\x11\xe0"}
    if not contenido.startswith(firmas[extension]):
        raise HTTPException(status_code=400, detail="El contenido del archivo no corresponde a su extensión.")
    carpeta_base = Path(valor_configuracion("EPG_PRIVATE_UPLOADS_DIR", "/opt/sistema_posgrado/uploads_privados"))
    tramite = consulta.tramite
    carpeta = carpeta_base / tramite.expediente.uuid / "consultas" / consulta.uuid
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre_almacenado = f"evidencia{extension}"
    (carpeta / nombre_almacenado).write_bytes(contenido)
    url = f"/bot-posgrado/api/resolucion-consultas/{consulta.uuid}/evidencia"
    return url, nombre_original, hashlib.sha256(contenido).hexdigest()


@app.post("/api/expedientes/{expediente_ref}/cargar-resolucion-directa")
def cargar_resolucion_directa(
    expediente_ref: str,
    tipo_documento: str = "Resolucion directa",
    archivo_url: Optional[str] = None,
    archivo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    url = archivo_url
    if archivo:
        url = guardar_upload_resolucion(exp, archivo)
    if not url:
        raise HTTPException(status_code=400, detail="Adjunta un archivo o envia archivo_url")

    resolucion = models.ResolucionFirma(
        id_expediente=exp.id_expediente,
        id_paso_asociado=exp.id_paso_actual,
        tipo_documento=tipo_documento,
        archivo_drive_url=url,
        estado_firma="Firmado",
        fecha_firma=datetime.utcnow(),
    )
    db.add(resolucion)
    exp.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(db, exp, "Resolucion_Cargada", f"{tipo_documento}: {url}", current_user.nombre_completo)
    db.commit()
    return {"status": "ok", "id_resolucion": resolucion.id_resolucion, "archivo_url": url}


@app.post("/api/expedientes/{expediente_ref}/cambiar-titulo")
def cambiar_titulo(
    expediente_ref: str,
    nuevo_titulo: str,
    nota: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    titulo_anterior = exp.titulo_tesis
    exp.titulo_tesis = nuevo_titulo
    exp.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(
        db,
        exp,
        "Titulo_Actualizado",
        nota or f"Titulo actualizado. Anterior: {titulo_anterior or 'sin registro'}",
        current_user.nombre_completo,
    )
    db.commit()
    return {"status": "ok", "titulo_tesis": exp.titulo_tesis}


@app.post("/api/expedientes/{expediente_ref}/asignar-dictaminantes")
def asignar_dictaminantes(
    expediente_ref: str,
    docente_ids: str,
    reemplazar: bool = True,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    ids = [int(x.strip()) for x in docente_ids.split(",") if x.strip()]
    if len(ids) != 3:
        raise HTTPException(status_code=400, detail="Debes enviar exactamente 3 docentes")

    docentes = db.query(models.Docente).filter(models.Docente.id_docente.in_(ids)).all()
    if len(docentes) != 3:
        raise HTTPException(status_code=400, detail="Uno o mas docentes no existen")

    if reemplazar:
        for actual in exp.asignaciones:
            if actual.rol_asignado == "Dictaminante" and actual.estado_asignacion == "Activo":
                actual.estado_asignacion = "Concluido"

    nuevas = []
    for id_docente in ids:
        asignacion = models.AsignacionTesis(
            id_expediente=exp.id_expediente,
            id_docente=id_docente,
            rol_asignado="Dictaminante",
            estado_asignacion="Activo",
        )
        db.add(asignacion)
        db.flush()
        db.add(models.AceptacionDictaminante(id_asignacion=asignacion.id_asignacion, estado_aceptacion="Pendiente"))
        nuevas.append(asignacion)

    exp.sub_estado = "Pendiente_Dictaminantes"
    exp.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(db, exp, "Dictaminantes_Asignados", "Se asignaron 3 dictaminantes.", current_user.nombre_completo)
    db.commit()
    return {"status": "ok", "asignaciones": [a.id_asignacion for a in nuevas], "sub_estado": exp.sub_estado}


@app.post("/api/expedientes/{expediente_ref}/notificar")
def notificar_expediente(
    expediente_ref: str,
    mensaje: str,
    ticket_id: Optional[int] = None,
    archivo_resolucion: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    if not ticket_id:
        raise HTTPException(status_code=400, detail="Selecciona un ticket concreto; E1 no permite notificaciones masivas.")
    ticket = obtener_ticket_por_ref(db, str(ticket_id))
    if ticket.id_expediente != exp.id_expediente:
        raise HTTPException(status_code=400, detail="El ticket no pertenece al expediente indicado.")
    if not mensaje.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")
    payload = {"mensaje": mensaje.strip(), "archivo_resolucion": archivo_resolucion or None}
    validar_payload_salida(payload)
    clave = f"osticket.notification:{ticket.uuid}:{hashlib.sha256(str(payload).encode('utf-8')).hexdigest()[:32]}"
    item, creada = crear_solicitud(
        db,
        actor=current_user,
        target_system="osticket",
        action_type="ticket.notificacion",
        subject_type="ticket",
        subject_uuid=ticket.uuid,
        idempotency_key=clave,
        payload=payload,
        ticket=ticket,
        expediente=exp,
        sustento="Solicitud desde expediente",
    )
    registrar_movimiento(
        db,
        exp,
        "Clasificado",
        f"Notificación solicitada para ticket #{ticket.numero_visual}; pendiente de aprobación.",
        current_user.nombre_completo,
    )
    db.commit()
    db.refresh(item)
    return {"status": item.status, "creada": creada, "outbox_uuid": item.uuid, "outbox": serializar_solicitud(item)}


@app.get("/api/resolucion-modelos")
def listar_modelos_resolucion(
    id_paso: int = Query(..., ge=1, le=7),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    modelos = (
        db.query(models.ResolucionDocumento)
        .filter(
            models.ResolucionDocumento.id_paso_inferido == id_paso,
            models.ResolucionDocumento.estado_revision.in_(["OK", "Importado"]),
        )
        .order_by(models.ResolucionDocumento.fecha_resolucion.desc(), models.ResolucionDocumento.id_documento.desc())
        .limit(120)
        .all()
    )
    return {"data": [serializar_modelo(modelo) for modelo in modelos if es_modelo_utilizable(modelo)][:40]}


def cargar_catalogo_plantillas_oficiales():
    ruta = ROOT / "data" / "plantillas_resolucion" / "catalogo.json"
    if not ruta.exists():
        return {"modelos_canonicos": [], "cobertura_base": {}}
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"modelos_canonicos": [], "cobertura_base": {}}


def obtener_plantilla_oficial(codigo: str, id_paso: int | None = None):
    modelos = cargar_catalogo_plantillas_oficiales().get("modelos_canonicos") or []
    plantilla = next((item for item in modelos if item.get("codigo") == codigo), None)
    if not plantilla:
        raise HTTPException(status_code=404, detail="Plantilla oficial no encontrada.")
    if id_paso and int(plantilla.get("id_paso") or 0) != int(id_paso):
        raise HTTPException(status_code=409, detail="La plantilla elegida no corresponde al paso del trámite.")
    ruta = Path(plantilla["archivo"]).resolve()
    raiz = (ROOT / "data" / "plantillas_resolucion" / "canonicas").resolve()
    if not ruta.is_file() or raiz not in ruta.parents:
        raise HTTPException(status_code=404, detail="El Word canónico no está disponible localmente.")
    return plantilla, ruta


@app.get("/api/plantillas-resolucion")
def listar_plantillas_resolucion_oficiales(
    id_paso: Optional[int] = Query(None, ge=1, le=7),
    variante: Optional[str] = None,
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    catalogo = cargar_catalogo_plantillas_oficiales()
    modelos = catalogo.get("modelos_canonicos") or []
    if id_paso:
        modelos = [item for item in modelos if item.get("id_paso") == id_paso]
    if variante:
        modelos = [item for item in modelos if item.get("variante") == variante]
    return {
        "total": len(modelos),
        "data": modelos,
        "cobertura_base": catalogo.get("cobertura_base") or {},
        "generado_en": catalogo.get("generado_en"),
    }


@app.get("/api/plantillas-resolucion/{codigo}/archivo")
def abrir_plantilla_resolucion_oficial(
    codigo: str,
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    _, ruta = obtener_plantilla_oficial(codigo)
    return FileResponse(ruta, filename=ruta.name)


@app.get("/api/resolucion-tramites/{tramite_ref}/plantilla-oficial/{codigo}/vista-previa")
def vista_previa_plantilla_oficial(
    tramite_ref: str,
    codigo: str,
    numero_resolucion: str,
    fecha_resolucion: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    plantilla, ruta = obtener_plantilla_oficial(codigo, tramite.id_paso)
    try:
        fecha = datetime.strptime(fecha_resolucion, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="La fecha debe tener formato AAAA-MM-DD.") from exc
    contenido, detalle = crear_docx_desde_plantilla_oficial(ruta, tramite, numero_resolucion.strip(), fecha)
    documento = Document(BytesIO(contenido))
    texto = "\n".join(parrafo.text for parrafo in documento.paragraphs if parrafo.text.strip())
    return {"plantilla": plantilla, "contenido": texto, **detalle}


@app.get("/api/resolucion-tramites/{tramite_ref}/plantilla-oficial/{codigo}/vista-previa-pdf")
def vista_previa_pdf_plantilla_oficial(
    tramite_ref: str,
    codigo: str,
    numero_resolucion: str,
    fecha_resolucion: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    _, ruta = obtener_plantilla_oficial(codigo, tramite.id_paso)
    try:
        fecha = datetime.strptime(fecha_resolucion, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="La fecha debe tener formato AAAA-MM-DD.") from exc
    contenido, _ = crear_docx_desde_plantilla_oficial(ruta, tramite, numero_resolucion.strip(), fecha)
    return Response(content=pdf_de_docx_para_vista_previa(contenido), media_type="application/pdf")


@app.get("/api/resolucion-tramites/{tramite_ref}/numeracion")
def revisar_numeracion_tramite(
    tramite_ref: str,
    numero_resolucion: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    return inspeccionar_numeracion(db, numero_resolucion.strip(), obtener_tramite(db, tramite_ref))


@app.post("/api/resolucion-tramites/{tramite_ref}/generar-borrador-oficial")
def generar_borrador_desde_plantilla_oficial(
    tramite_ref: str,
    payload: GenerarBorradorOficialPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    if tramite.estado not in {"en_elaboracion_secretaria", "observado_por_direccion"}:
        raise HTTPException(status_code=409, detail="El trámite no está disponible para generar o corregir el Word.")
    plantilla, ruta_plantilla = obtener_plantilla_oficial(payload.codigo_plantilla, tramite.id_paso)
    try:
        fecha = datetime.strptime(payload.fecha_resolucion, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="La fecha debe tener formato AAAA-MM-DD.") from exc
    numero = payload.numero_resolucion.strip()
    inspeccion_numeracion = validar_numeracion_operativa(
        db, tramite, numero, payload.decision_numeracion, payload.nota_numeracion,
    )
    if tramite.id_paso in {4, 7} and not (payload.referencia_origen or tramite.referencia_origen):
        raise HTTPException(status_code=409, detail=f"El paso {tramite.id_paso} requiere una referencia ERP.")

    contenido, detalle = crear_docx_desde_plantilla_oficial(ruta_plantilla, tramite, numero, fecha)
    destino = None
    try:
        url, nombre, contenido_hash, destino = guardar_borrador_generado(tramite, contenido)
        anterior = tramite.estado
        tramite.numero_resolucion = numero
        tramite.fecha_resolucion = fecha
        tramite.borrador_version = (tramite.borrador_version or 0) + (1 if tramite.borrador_word_url else 0)
        tramite.borrador_word_url = url
        tramite.borrador_word_nombre = nombre
        tramite.referencia_origen = payload.referencia_origen or tramite.referencia_origen
        tramite.estado = "en_elaboracion_secretaria"
        tramite.fecha_actualizacion = datetime.utcnow()
        registrar_evento_tramite(
            db, tramite, "borrador_generado_plantilla_oficial", current_user, anterior,
            f"Word generado desde {payload.codigo_plantilla}; conserva el formato institucional.",
            {
                "codigo_plantilla": payload.codigo_plantilla,
                "sha256": contenido_hash,
                "decision_numeracion": payload.decision_numeracion or "regular",
                "nota_numeracion": payload.nota_numeracion,
                "inspeccion_numeracion": inspeccion_numeracion,
                **detalle,
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        if destino and destino.exists():
            destino.unlink()
        raise
    return {
        "status": "ok",
        "plantilla": plantilla,
        "detalle": detalle,
        "tramite": serializar_tramite(tramite, detalle=True),
    }


@app.get("/api/resoluciones/control-numeracion")
def obtener_control_numeracion_resoluciones(
    anio: int = Query(datetime.utcnow().year, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    return control_numeracion(db, anio)


@app.get("/api/resolucion-modelos/{id_modelo_documento}/vista-previa")
def vista_previa_modelo_resolucion(
    id_modelo_documento: int,
    tramite_ref: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    modelo = obtener_modelo_resolucion(db, id_modelo_documento, tramite.id_paso)
    return construir_borrador(tramite, modelo)


@app.post("/api/resolucion-tramites/{tramite_ref}/generar-borrador")
def generar_borrador_resolucion(
    tramite_ref: str,
    payload: GenerarBorradorPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    modelo = obtener_modelo_resolucion(db, payload.id_modelo_documento, tramite.id_paso)
    try:
        fecha = datetime.strptime(payload.fecha_resolucion, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="La fecha debe tener formato AAAA-MM-DD.") from exc
    ruta = None
    try:
        ruta = aplicar_borrador_generado(
            db, tramite, modelo, payload.contenido.strip(), payload.numero_resolucion.strip(), fecha,
            current_user, payload.referencia_origen,
        )
        db.commit()
    except Exception:
        db.rollback()
        if ruta and ruta.exists():
            ruta.unlink()
        raise
    db.refresh(tramite)
    return {"status": "ok", "tramite": serializar_tramite(tramite, detalle=True)}


@app.post("/api/resolucion-tramites/generar-borradores-lote")
def generar_borradores_lote(
    payload: GenerarBorradoresLotePayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    referencias = list(dict.fromkeys(item.strip() for item in payload.tramites if item.strip()))
    if len(referencias) != len(payload.tramites):
        raise HTTPException(status_code=400, detail="No repitas trámites en la generación por lote.")
    tramites = [obtener_tramite(db, referencia) for referencia in referencias]
    if not tramites:
        raise HTTPException(status_code=400, detail="Selecciona al menos un trámite.")
    if len({tramite.id_paso for tramite in tramites}) != 1:
        raise HTTPException(status_code=409, detail="Un lote solo puede contener trámites del mismo paso.")
    modelo = obtener_modelo_resolucion(db, payload.id_modelo_documento, tramites[0].id_paso)
    rutas = []
    try:
        # Validar el lote completo antes de crear el primer Word o alterar estados.
        numeros = set()
        for tramite in tramites:
            if not tramite.numero_resolucion or not tramite.fecha_resolucion:
                raise HTTPException(status_code=409, detail=f"{tramite.expediente.nombre_alumno}: falta número o fecha de resolución.")
            if tramite.numero_resolucion in numeros:
                raise HTTPException(status_code=409, detail="El lote contiene números de resolución repetidos.")
            numeros.add(tramite.numero_resolucion)
            validar_preparacion_generada(db, tramite, modelo, tramite.numero_resolucion, tramite.fecha_resolucion, tramite.referencia_origen)
        for tramite in tramites:
            vista = construir_borrador(tramite, modelo, tramite.numero_resolucion, tramite.fecha_resolucion)
            rutas.append(aplicar_borrador_generado(
                db, tramite, modelo, vista["contenido"], tramite.numero_resolucion, tramite.fecha_resolucion,
                current_user, tramite.referencia_origen,
            ))
        db.commit()
    except Exception:
        db.rollback()
        for ruta in rutas:
            if ruta.exists():
                ruta.unlink()
        raise
    return {"status": "ok", "cantidad": len(tramites), "tramites": [serializar_tramite(tramite) for tramite in tramites]}


@app.post("/api/resolucion-tramites/remitir-direccion-lote")
def remitir_resoluciones_direccion_lote(
    payload: RemitirDireccionLotePayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    referencias = list(dict.fromkeys(item.strip() for item in payload.tramites if item.strip()))
    if len(referencias) != len(payload.tramites):
        raise HTTPException(status_code=400, detail="No repitas trámites en la remisión por lote.")
    tramites = [obtener_tramite(db, referencia) for referencia in referencias]
    for tramite in tramites:
        if tramite.estado != "en_elaboracion_secretaria":
            raise HTTPException(status_code=409, detail=f"{tramite.expediente.nombre_alumno}: el trámite no está listo para remitir.")
        validar_remision_direccion(tramite, regla_aplicada(db, tramite))
    for tramite in tramites:
        cambiar_estado_tramite(
            db, tramite, "listo_para_direccion", "remitido_a_direccion_lote", current_user,
            "Word remitido a Dirección como parte de un lote validado.",
            {"cantidad_lote": len(tramites)},
        )
        tramite.expediente.sub_estado = "Pendiente_Firma_Direccion"
    db.commit()
    return {"status": "ok", "cantidad": len(tramites), "tramites": [serializar_tramite(tramite) for tramite in tramites]}


@app.get("/api/resolucion-tramites")
def listar_resolucion_tramites(
    estado: Optional[str] = None,
    id_paso: Optional[int] = None,
    busqueda: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    query = db.query(models.ResolucionTramite).join(models.ExpedienteTesis)
    if estado:
        estados = [item.strip() for item in estado.split(",") if item.strip()]
        query = query.filter(models.ResolucionTramite.estado.in_(estados))
    if id_paso:
        query = query.filter(models.ResolucionTramite.id_paso == id_paso)
    if busqueda:
        like = f"%{busqueda.strip()}%"
        query = query.filter(
            or_(
                models.ResolucionTramite.numero_resolucion.like(like),
                models.ResolucionTramite.tipo_resolucion.like(like),
                models.ExpedienteTesis.nombre_alumno.like(like),
                models.ExpedienteTesis.codigo_alumno.like(like),
                models.ExpedienteTesis.titulo_tesis.like(like),
            )
        )
    query = query.order_by(models.ResolucionTramite.fecha_actualizacion.desc())
    total, total_pages, items = paginar(query, page, per_page)
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": [serializar_tramite(item) for item in items],
    }


@app.get("/api/resolucion-tramites/{tramite_ref}")
def detalle_resolucion_tramite(
    tramite_ref: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    return serializar_tramite(obtener_tramite(db, tramite_ref), detalle=True)


@app.post("/api/expedientes/{expediente_ref}/resolucion-tramites")
def crear_resolucion_tramite(
    expediente_ref: str,
    payload: DerivarResolucionPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    expediente = obtener_expediente_por_ref(db, expediente_ref)
    ticket = None
    if payload.ticket_id:
        ticket = obtener_ticket_por_ref(db, str(payload.ticket_id))
        if ticket.id_expediente != expediente.id_expediente:
            raise HTTPException(status_code=400, detail="El ticket no pertenece a este expediente.")
    paso_objetivo = int(payload.id_paso or expediente.id_paso_actual)
    regla = regla_vigente(db, paso_objetivo)
    tramite, creado = derivar_a_secretaria(
        db,
        expediente,
        current_user,
        payload.tipo_resolucion,
        ticket,
        payload.referencia_origen,
        regla,
        id_paso=paso_objetivo,
    )
    expediente.sub_estado = "Derivado_Secretaria"
    expediente.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(
        db,
        expediente,
        "Derivado",
        f"Trámite de {payload.tipo_resolucion} derivado a Secretaría Académica.",
        current_user.nombre_completo,
    )
    db.commit()
    db.refresh(tramite)
    return {"status": "ok", "creado": creado, "tramite": serializar_tramite(tramite, detalle=True)}


@app.post("/api/resolucion-tramites/{tramite_ref}/revisar")
def revisar_resolucion_tramite(
    tramite_ref: str,
    payload: RevisarTramitePayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    if tramite.estado != "derivado_secretaria":
        raise HTTPException(status_code=409, detail="El trámite ya fue revisado por Secretaría Académica.")
    if payload.accion == "Observar" and not (payload.nota or "").strip():
        raise HTTPException(status_code=400, detail="Indica qué debe subsanar el tramitador.")
    nuevo_estado = "en_elaboracion_secretaria" if payload.accion == "Aceptar" else "observado_tramitador"
    accion = "revision_secretaria_aceptada" if payload.accion == "Aceptar" else "observado_por_secretaria"
    cambiar_estado_tramite(db, tramite, nuevo_estado, accion, current_user, payload.nota)
    tramite.expediente.sub_estado = "En_Secretaria" if payload.accion == "Aceptar" else "Observado_Tramitador"
    db.commit()
    return {"status": "ok", "tramite": serializar_tramite(tramite, detalle=True)}


@app.post("/api/resolucion-tramites/{tramite_ref}/preparar")
def preparar_resolucion_tramite(
    tramite_ref: str,
    numero_resolucion: str = Form(...),
    fecha_resolucion: str = Form(...),
    requiere_consulta_previa: bool = Form(False),
    referencia_origen: Optional[str] = Form(None),
    decision_numeracion: Optional[str] = Form(None),
    nota_numeracion: Optional[str] = Form(None),
    nota: Optional[str] = Form(None),
    archivo_word: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    if tramite.estado not in {"en_elaboracion_secretaria", "observado_por_direccion"}:
        raise HTTPException(status_code=409, detail="El trámite no está disponible para elaborar o corregir el Word.")
    try:
        fecha = datetime.strptime(fecha_resolucion, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="La fecha debe tener formato AAAA-MM-DD.") from exc
    numero = numero_resolucion.strip()
    if decision_numeracion not in {None, "regular", "no_emitida", "archivo", "anulada"}:
        raise HTTPException(status_code=422, detail="La decisión de numeración no es válida.")
    inspeccion_numeracion = validar_numeracion_operativa(db, tramite, numero, decision_numeracion, nota_numeracion)

    regla = regla_aplicada(db, tramite)
    # Una regla puede ser parcial por canal o evidencia pendiente y, aun así,
    # tener la consulta previa ya decidida. Ese hecho no debe quedar opcional.
    consulta_reglada = regla.requiere_consulta_previa if regla else None
    if consulta_reglada is False and tramite.consultas:
        raise HTTPException(status_code=409, detail="La regla aplicada no admite consulta previa; revisa las consultas existentes antes de continuar.")

    anterior = tramite.estado
    tramite.numero_resolucion = numero
    tramite.fecha_resolucion = fecha
    if tramite.vigencia_meses:
        tramite.fecha_vencimiento = sumar_meses(fecha, tramite.vigencia_meses)
    tramite.requiere_consulta_previa = consulta_reglada if consulta_reglada is not None else requiere_consulta_previa
    tramite.referencia_origen = (referencia_origen or "").strip() or None
    if archivo_word:
        url, nombre, _ = guardar_archivo_tramite(tramite, archivo_word, "word")
        tramite.borrador_version = (tramite.borrador_version or 0) + (1 if tramite.borrador_word_url else 0)
        tramite.borrador_word_url = url
        tramite.borrador_word_nombre = nombre
    if anterior == "observado_por_direccion":
        tramite.estado = "en_elaboracion_secretaria"
        tramite.observacion_actual = None
    tramite.fecha_actualizacion = datetime.utcnow()
    registrar_evento_tramite(
        db,
        tramite,
        "borrador_preparado" if anterior != "observado_por_direccion" else "borrador_corregido",
        current_user,
        anterior,
        nota,
        {
            "numero": numero,
            "decision_numeracion": decision_numeracion or "regular",
            "nota_numeracion": nota_numeracion,
            "inspeccion_numeracion": inspeccion_numeracion,
            "version": tramite.borrador_version,
            "requiere_consulta": tramite.requiere_consulta_previa,
            "borrador_word_url": tramite.borrador_word_url,
            "borrador_word_nombre": tramite.borrador_word_nombre,
        },
    )
    db.commit()
    return {"status": "ok", "tramite": serializar_tramite(tramite, detalle=True)}


@app.post("/api/resolucion-tramites/{tramite_ref}/consultas")
def crear_consultas_resolucion(
    tramite_ref: str,
    payload: CrearConsultasPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    participantes = [item.model_dump() for item in payload.participantes]
    regla = regla_aplicada(db, tramite)
    validar_consultas_segun_regla(tramite, participantes, regla, payload.modalidad_respuesta)
    frontend_url = valor_configuracion("EPG_FRONTEND_PUBLIC_URL", EPG_PUBLIC_BASE_URL).rstrip("/")
    enlaces = crear_consultas_tramite(
        db, tramite, participantes, current_user, frontend_url,
        payload.vigencia_dias, payload.modalidad_respuesta,
        payload.asunto, payload.mensaje,
    )
    db.commit()
    return {
        "status": "ok",
        "advertencia": "Estos enlaces se comparten manualmente; el sistema no envió mensajes.",
        "consultas": enlaces,
    }


def serializar_plantilla_consulta(item):
    return {
        "id_plantilla": item.id_plantilla,
        "nombre": item.nombre,
        "asunto": item.asunto,
        "mensaje": item.mensaje,
        "modalidad_respuesta": item.modalidad_respuesta,
        "activa": item.activa,
        "creado_por": item.creado_por_nombre,
        "fecha_actualizacion": item.fecha_actualizacion.isoformat() if item.fecha_actualizacion else None,
    }


@app.get("/api/resolucion-consulta-plantillas")
def listar_plantillas_consulta(
    incluir_inactivas: bool = False,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    query = db.query(models.ConsultaPlantilla)
    if not incluir_inactivas:
        query = query.filter(models.ConsultaPlantilla.activa == True)
    items = query.order_by(models.ConsultaPlantilla.nombre).all()
    return {"data": [serializar_plantilla_consulta(item) for item in items]}


@app.post("/api/resolucion-consulta-plantillas")
def crear_plantilla_consulta(
    payload: ConsultaPlantillaPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    item = models.ConsultaPlantilla(
        **payload.model_dump(),
        id_creado_por=current_user.id_usuario,
        creado_por_nombre=current_user.nombre_completo,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"status": "ok", "plantilla": serializar_plantilla_consulta(item)}


@app.put("/api/resolucion-consulta-plantillas/{id_plantilla}")
def actualizar_plantilla_consulta(
    id_plantilla: int,
    payload: ConsultaPlantillaPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    item = db.query(models.ConsultaPlantilla).filter(models.ConsultaPlantilla.id_plantilla == id_plantilla).first()
    if not item:
        raise HTTPException(status_code=404, detail="Plantilla de consulta no encontrada.")
    for campo, valor in payload.model_dump().items():
        setattr(item, campo, valor)
    db.commit()
    return {"status": "ok", "plantilla": serializar_plantilla_consulta(item)}


@app.get("/api/consultas-resolucion/{token}")
def ver_consulta_resolucion(token: str, db: Session = Depends(get_db)):
    consulta = obtener_consulta_por_token(db, token)
    tramite = consulta.tramite
    return {
        "consulta": serializar_consulta(consulta, incluir_interno=False),
        "tramite": {
            "tipo_resolucion": tramite.tipo_resolucion,
            "paso": tramite.paso.nombre_paso if tramite.paso else None,
            "estudiante": tramite.expediente.nombre_alumno,
            "titulo_tesis": tramite.expediente.titulo_tesis,
        },
        "vencida": consulta.fecha_expiracion < datetime.utcnow(),
    }


@app.post("/api/consultas-resolucion/{token}/responder")
def responder_consulta_resolucion(
    token: str,
    payload: ResponderConsultaPayload,
    db: Session = Depends(get_db),
):
    consulta = responder_consulta(db, obtener_consulta_por_token(db, token), payload.respuesta, payload.nota)
    db.commit()
    return {"status": "ok", "consulta": serializar_consulta(consulta, incluir_interno=False)}


@app.post("/api/consultas-resolucion/{token}/responder-con-evidencia")
def responder_consulta_con_evidencia(
    token: str,
    respuesta: str = Form(...),
    nota: Optional[str] = Form(None),
    constancia_aceptada: bool = Form(False),
    archivo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    consulta = obtener_consulta_por_token(db, token)
    if consulta.estado != "Pendiente":
        raise HTTPException(status_code=409, detail="Esta consulta ya fue respondida.")
    if consulta.fecha_expiracion < datetime.utcnow():
        raise HTTPException(status_code=410, detail="El enlace de consulta venció.")
    if respuesta == "Aceptar" and consulta.modalidad_respuesta == "Documento" and not archivo:
        raise HTTPException(status_code=400, detail="Esta consulta requiere adjuntar un documento.")
    if respuesta == "Aceptar" and consulta.modalidad_respuesta == "Constancia" and not constancia_aceptada:
        raise HTTPException(status_code=400, detail="Debes aceptar la declaración de constancia para responder.")
    evidencia = guardar_evidencia_consulta(consulta, archivo) if archivo else None
    consulta = responder_consulta(
        db, consulta, respuesta, nota, evidencia, constancia_aceptada,
    )
    db.commit()
    return {"status": "ok", "consulta": serializar_consulta(consulta, incluir_interno=False)}


@app.get("/api/resolucion-consultas/{consulta_uuid}/evidencia")
def descargar_evidencia_consulta(
    consulta_uuid: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    consulta = db.query(models.ResolucionConsulta).filter(models.ResolucionConsulta.uuid == consulta_uuid).first()
    if not consulta or not consulta.respuesta_archivo_url:
        raise HTTPException(status_code=404, detail="Evidencia de consulta no encontrada.")
    carpeta_base = Path(valor_configuracion("EPG_PRIVATE_UPLOADS_DIR", "/opt/sistema_posgrado/uploads_privados"))
    carpeta = carpeta_base / consulta.tramite.expediente.uuid / "consultas" / consulta.uuid
    archivos = list(carpeta.glob("evidencia.*"))
    if len(archivos) != 1:
        raise HTTPException(status_code=404, detail="El archivo de evidencia no está disponible.")
    return FileResponse(archivos[0], filename=consulta.respuesta_archivo_nombre or archivos[0].name)


@app.post("/api/resolucion-tramites/{tramite_ref}/remitir-direccion")
def remitir_resolucion_direccion(
    tramite_ref: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    if tramite.estado != "en_elaboracion_secretaria":
        raise HTTPException(status_code=409, detail="El trámite no está listo para remitir a Dirección.")
    validar_remision_direccion(tramite, regla_aplicada(db, tramite))
    cambiar_estado_tramite(
        db,
        tramite,
        "listo_para_direccion",
        "remitido_a_direccion",
        current_user,
        "Word remitido para revisión, firma con ReFirma y devolución en PDF.",
    )
    tramite.expediente.sub_estado = "Pendiente_Firma_Direccion"
    db.commit()
    return {"status": "ok", "tramite": serializar_tramite(tramite, detalle=True)}


@app.post("/api/resolucion-tramites/{tramite_ref}/observar-direccion")
def observar_resolucion_direccion(
    tramite_ref: str,
    payload: NotaTramitePayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    if tramite.estado != "listo_para_direccion":
        raise HTTPException(status_code=409, detail="La resolución no está pendiente de Dirección.")
    cambiar_estado_tramite(db, tramite, "observado_por_direccion", "devuelto_con_observaciones", current_user, payload.nota)
    tramite.expediente.sub_estado = "Observado_Direccion"
    db.commit()
    return {"status": "ok", "tramite": serializar_tramite(tramite, detalle=True)}


@app.post("/api/resolucion-tramites/{tramite_ref}/firmar")
def firmar_resolucion_tramite(
    tramite_ref: str,
    archivo_pdf: UploadFile = File(...),
    nota: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    if tramite.estado != "listo_para_direccion":
        raise HTTPException(status_code=409, detail="La resolución no está pendiente de firma en Dirección.")
    url, nombre, archivo_hash = guardar_archivo_tramite(tramite, archivo_pdf, "firmado")
    resolucion_legacy = models.ResolucionFirma(
        id_expediente=tramite.id_expediente,
        id_paso_asociado=tramite.id_paso,
        tipo_documento=f"{tramite.numero_resolucion} - {tramite.tipo_resolucion}",
        archivo_drive_url=url,
        estado_firma="Firmado",
        fecha_firma=datetime.utcnow(),
    )
    db.add(resolucion_legacy)
    db.flush()
    tramite.id_resolucion_firma = resolucion_legacy.id_resolucion
    tramite.pdf_firmado_url = url
    tramite.pdf_firmado_nombre = nombre
    tramite.pdf_firmado_hash = archivo_hash
    tramite.fecha_firma = datetime.utcnow()
    cambiar_estado_tramite(
        db,
        tramite,
        "devuelto_tramitador",
        "firmado_y_devuelto",
        current_user,
        nota or "PDF firmado con ReFirma cargado por Dirección y devuelto al tramitador.",
        {"id_resolucion_firma": resolucion_legacy.id_resolucion, "sha256": archivo_hash},
    )
    regla = regla_aplicada(db, tramite)
    sin_notificacion = debe_cerrar_por_resolucion_cargada(tramite, regla)
    if sin_notificacion:
        cambiar_estado_tramite(
            db, tramite, "notificado_confirmado", "resolucion_cargada_cierre_p7", current_user,
            "Trámite P7 concluido al cargar la resolución firmada; no requiere notificación.",
            {"regla_version": regla.version},
        )
        tramite.expediente.sub_estado = None
        if tramite.ticket:
            referencia = f"firma:{resolucion_legacy.id_resolucion}"
            relacion, _ = proponer_resolucion(
                db, tramite.ticket, referencia, current_user,
                "Resolución P7 cargada en el repositorio institucional.", origen="flujo_resolucion",
            )
            confirmar_resolucion(
                db, tramite.ticket, relacion, current_user,
                "P7 concluido por resolución cargada; no corresponde notificación al estudiante.",
                origen="flujo_resolucion", decision_cierre="resolucion_cargada",
            )
    else:
        tramite.expediente.sub_estado = "Pendiente_Notificacion"
    movimiento_nota = (
        f"Resolución {tramite.numero_resolucion} cargada; P7 concluido sin notificación."
        if sin_notificacion
        else f"Resolución {tramite.numero_resolucion} firmada y devuelta al tramitador."
    )
    registrar_movimiento(
        db,
        tramite.expediente,
        "Resolucion_Cargada",
        movimiento_nota,
        current_user.nombre_completo,
    )
    db.commit()
    return {"status": "ok", "tramite": serializar_tramite(tramite, detalle=True)}


@app.post("/api/resolucion-tramites/{tramite_ref}/notificaciones")
def registrar_destinatario_resolucion(
    tramite_ref: str,
    payload: RegistrarNotificacionPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    item = registrar_notificacion_tramite(
        db,
        tramite,
        current_user,
        payload.destinatario_tipo,
        payload.destinatario_nombre,
        payload.destinatario_referencia,
        payload.canal,
    )
    db.commit()
    return {"status": "ok", "notificacion": serializar_notificacion(item)}


@app.post("/api/resolucion-tramites/{tramite_ref}/notificaciones/{id_notificacion}/confirmar")
def confirmar_destinatario_resolucion(
    tramite_ref: str,
    id_notificacion: int,
    payload: ConfirmarNotificacionPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    tramite = obtener_tramite(db, tramite_ref)
    item = db.query(models.ResolucionNotificacion).filter(
        models.ResolucionNotificacion.id_notificacion == id_notificacion
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Notificación no encontrada.")
    confirmar_notificacion_tramite(
        db, tramite, item, current_user, payload.evidencia,
        regla_aplicada(db, tramite),
    )
    if tramite.estado == "notificado_confirmado" and tramite.ticket and tramite.id_resolucion_firma:
        referencia = f"firma:{tramite.id_resolucion_firma}"
        relacion, _ = proponer_resolucion(db, tramite.ticket, referencia, current_user, "Resolución firmada del trámite institucional.")
        confirmar_resolucion(db, tramite.ticket, relacion, current_user, payload.evidencia)
        if decision_actual_ticket(tramite.ticket).get("decision") != "resolucion_notificada":
            registrar_decision(
                db,
                tramite.ticket,
                "resolucion_notificada",
                current_user,
                payload.evidencia,
                resolucion_ref=referencia,
            )
        tramite.expediente.sub_estado = None
        registrar_movimiento(
            db,
            tramite.expediente,
            "Notificado",
            f"Resolución {tramite.numero_resolucion} notificada y confirmada.",
            current_user.nombre_completo,
        )
    db.commit()
    return {"status": "ok", "tramite": serializar_tramite(tramite, detalle=True)}


@app.get("/api/directora/pendientes")
def listar_pendientes_directora(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_directora_o_admin),
):
    expedientes = (
        db.query(models.ExpedienteTesis)
        .filter(models.ExpedienteTesis.sub_estado.in_(["Derivado_Directora", "Pendiente_Dictaminantes", "Pendiente_Firma"]))
        .order_by(models.ExpedienteTesis.fecha_ultimo_movimiento.desc())
        .all()
    )
    return {"total": len(expedientes), "data": [serializar_expediente_detalle(db, exp) for exp in expedientes]}


@app.post("/api/resoluciones/{id_resolucion}/aprobar")
def aprobar_resolucion(
    id_resolucion: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_directora_o_admin),
):
    resolucion = db.query(models.ResolucionFirma).filter(models.ResolucionFirma.id_resolucion == id_resolucion).first()
    if not resolucion:
        raise HTTPException(status_code=404, detail="Resolucion no encontrada")
    resolucion.estado_firma = "Firmado"
    resolucion.fecha_firma = datetime.utcnow()
    exp = db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.id_expediente == resolucion.id_expediente).first()
    if exp:
        exp.sub_estado = None
        registrar_movimiento(db, exp, "Avanzado", f"Resolucion {id_resolucion} aprobada.", current_user.nombre_completo)
    db.commit()
    return {"status": "ok", "id_resolucion": id_resolucion}


def _leer_pdf_desde_zip_historico(ruta_zip: Path, source_path: str, numero: str | None = None, anio: str | None = None) -> tuple[bytes, str]:
    """Abre por ruta exacta o por número/año cuando una ruta Drive antigua cambió."""
    with zipfile.ZipFile(ruta_zip) as archivo_zip:
        try:
            return archivo_zip.read(source_path), Path(source_path).name
        except KeyError:
            coincidencia = re.search(r"(?<!\d)(\d{3,4})[-_\s]+(20\d{2})(?!\d)", source_path)
            numero = (numero or (coincidencia.group(1) if coincidencia else "")).zfill(4)
            anio = anio or (coincidencia.group(2) if coincidencia else "")
            if not numero or not anio:
                raise
            objetivo = f"{numero}-{anio}"
            candidatos = [nombre for nombre in archivo_zip.namelist() if nombre.lower().endswith('.pdf') and objetivo in ascii_mayusculas(nombre).replace(' ', '-')]
            if not candidatos:
                raise
            # Si hay rectificaciones con el mismo número, la coincidencia de
            # palabras del nombre original decide; nunca se devuelve el primero.
            palabras = {p for p in ascii_mayusculas(Path(source_path).stem).split() if len(p) >= 4 and not p.isdigit()}
            elegido = max(candidatos, key=lambda nombre: len(palabras & set(ascii_mayusculas(Path(nombre).stem).split())))
            return archivo_zip.read(elegido), Path(elegido).name


@app.get("/api/resoluciones/{id_resolucion}/archivo")
def descargar_resolucion_historica(
    id_resolucion: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Entrega el PDF histórico desde su ZIP, sin publicar la bóveda por Nginx."""
    resolucion = db.query(models.ResolucionFirma).filter(models.ResolucionFirma.id_resolucion == id_resolucion).first()
    if not resolucion:
        raise HTTPException(status_code=404, detail="Resolución no encontrada.")
    source_path = (resolucion.archivo_drive_url or "").strip()
    if not source_path or re.match(r"^https?://", source_path, flags=re.I):
        raise HTTPException(status_code=409, detail="Esta resolución no corresponde a un PDF histórico local.")
    ruta_relativa = Path(source_path)
    if ruta_relativa.is_absolute() or ".." in ruta_relativa.parts or ruta_relativa.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="La referencia del archivo histórico no es válida.")
    raiz_drive = (ROOT / "data" / "drive_resoluciones" / "raw").resolve()
    ruta_drive = (raiz_drive / ruta_relativa).resolve()
    if raiz_drive in ruta_drive.parents and ruta_drive.is_file():
        return FileResponse(
            ruta_drive,
            filename=ruta_drive.name,
            media_type="application/pdf",
            content_disposition_type="inline",
        )
    ruta_zip = Path(os.getenv(
        "EPG_RESOLUCIONES_ZIP",
        "/opt/sistema_posgrado/data/input/resoluciones/2026/RESOLUCIONES FIRMADAS-20260707T150151Z-3-001.zip",
    ))
    if not ruta_zip.is_file():
        raise HTTPException(status_code=404, detail="La bóveda histórica de resoluciones no está disponible.")
    try:
        contenido, nombre = _leer_pdf_desde_zip_historico(ruta_zip, source_path)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="El PDF histórico no está dentro de la bóveda.") from exc
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=500, detail="La bóveda histórica de resoluciones está dañada.") from exc
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(nombre)}"},
    )


@app.get("/api/dictaminantes/pendientes")
def listar_pendientes_dictaminante(id_docente: Optional[int] = None, db: Session = Depends(get_db)):
    query = (
        db.query(models.AsignacionTesis)
        .filter(models.AsignacionTesis.rol_asignado == "Dictaminante", models.AsignacionTesis.estado_asignacion == "Activo")
        .join(models.AceptacionDictaminante)
        .filter(models.AceptacionDictaminante.estado_aceptacion == "Pendiente")
    )
    if id_docente:
        query = query.filter(models.AsignacionTesis.id_docente == id_docente)

    asignaciones = query.order_by(models.AsignacionTesis.fecha_asignacion.desc()).all()
    data = []
    for asig in asignaciones:
        data.append(
            {
                "id_asignacion": asig.id_asignacion,
                "id_aceptacion": asig.aceptacion.id_aceptacion if asig.aceptacion else None,
                "docente": asig.docente.nombre_completo if asig.docente else None,
                "expediente": serializar_expediente_lista(asig.expediente),
                "fecha_asignacion": asig.fecha_asignacion.strftime("%Y-%m-%d %H:%M:%S") if asig.fecha_asignacion else None,
            }
        )
    return {"total": len(data), "data": data}


@app.post("/api/dictaminantes/aceptaciones/{id_aceptacion}/responder")
def responder_aceptacion(
    id_aceptacion: int,
    estado: str,
    nota: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    if estado not in ("Aceptado", "Rechazado"):
        raise HTTPException(status_code=400, detail="estado debe ser Aceptado o Rechazado")
    aceptacion = (
        db.query(models.AceptacionDictaminante)
        .filter(models.AceptacionDictaminante.id_aceptacion == id_aceptacion)
        .first()
    )
    if not aceptacion:
        raise HTTPException(status_code=404, detail="Aceptacion no encontrada")
    aceptacion.estado_aceptacion = estado
    aceptacion.nota = nota
    aceptacion.fecha_respuesta = datetime.utcnow()
    if estado == "Rechazado":
        aceptacion.asignacion.estado_asignacion = "Renuncia"

    exp = aceptacion.asignacion.expediente
    registrar_movimiento(
        db,
        exp,
        "Observado" if estado == "Rechazado" else "Avanzado",
        f"Dictaminante {estado.lower()}.",
        current_user.nombre_completo,
    )
    db.commit()
    return {"status": "ok", "estado_aceptacion": estado}


@app.get("/api/docentes")
def listar_docentes(db: Session = Depends(get_db)):
    docentes = db.query(models.Docente).order_by(models.Docente.nombre_completo).all()
    resultados = []
    for docente in docentes:
        carga_actual = (
            db.query(models.AsignacionTesis)
            .filter(models.AsignacionTesis.id_docente == docente.id_docente, models.AsignacionTesis.estado_asignacion == "Activo")
            .count()
        )
        resultados.append(
            {
                "id_docente": docente.id_docente,
                "dni": docente.dni,
                "nombre_completo": docente.nombre_completo,
                "correo": docente.correo,
                "correo_institucional": docente.correo_institucional,
                "correo_personal": docente.correo_personal,
                "especialidad": docente.especialidad,
                "tipo_contrato": docente.tipo_contrato,
                "estado": docente.estado,
                "max_tesis_permitidas": docente.max_tesis_permitidas,
                "carga_actual": carga_actual,
                "disponible": carga_actual < docente.max_tesis_permitidas and docente.estado == "Activo",
            }
        )
    return {"total": len(resultados), "data": resultados}


@app.post("/api/docentes")
def crear_docente(
    dni: str,
    nombre_completo: str,
    correo: Optional[str] = None,
    correo_institucional: Optional[str] = None,
    correo_personal: Optional[str] = None,
    especialidad: Optional[str] = None,
    tipo_contrato: str = "Indeterminado",
    max_tesis: int = 5,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    docente = models.Docente(
        dni=dni,
        nombre_completo=nombre_completo,
        correo=correo,
        correo_institucional=correo_institucional or (correo if correo and correo.lower().endswith("@uandina.edu.pe") else None),
        correo_personal=correo_personal or (correo if correo and not correo.lower().endswith("@uandina.edu.pe") else None),
        especialidad=especialidad,
        tipo_contrato=tipo_contrato,
        max_tesis_permitidas=max_tesis,
    )
    db.add(docente)
    db.commit()
    db.refresh(docente)
    return {"id_docente": docente.id_docente, "nombre_completo": docente.nombre_completo}


@app.put("/api/docentes/{id_docente}")
def actualizar_docente(
    id_docente: int,
    nombre_completo: str,
    correo: Optional[str] = None,
    correo_institucional: Optional[str] = None,
    correo_personal: Optional[str] = None,
    especialidad: Optional[str] = None,
    tipo_contrato: str = "Indeterminado",
    estado: str = "Activo",
    max_tesis: int = 5,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    docente = db.query(models.Docente).filter(models.Docente.id_docente == id_docente).first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    docente.nombre_completo = nombre_completo
    docente.correo = correo
    docente.correo_institucional = correo_institucional
    docente.correo_personal = correo_personal
    docente.especialidad = especialidad
    docente.tipo_contrato = tipo_contrato
    docente.estado = estado
    docente.max_tesis_permitidas = max_tesis
    db.commit()
    return {"status": "ok"}


@app.get("/api/pasos")
def listar_pasos(db: Session = Depends(get_db)):
    pasos = db.query(models.PasoFlujo).order_by(models.PasoFlujo.id_paso).all()
    return [{"id_paso": p.id_paso, "nombre_paso": p.nombre_paso, "descripcion": p.descripcion} for p in pasos]


@app.post("/api/admin/importar-excel")
def importar_excel(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    from importador_excel import importar_excel_expedientes

    resultado = importar_excel_expedientes(db, archivo.file, usuario_nombre=current_user.nombre_completo)
    return resultado


@app.get("/api/dictaminante/{uuid}")
def obtener_dictaminante(uuid: str, db: Session = Depends(get_db)):
    asig = db.query(models.AsignacionTesis).filter(models.AsignacionTesis.uuid == uuid).first()
    if not asig:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return {
        "uuid": asig.uuid,
        "titulo_tesis": asig.expediente.titulo_tesis,
        "alumno": asig.expediente.nombre_alumno,
        "docente": asig.docente.nombre_completo,
        "rol": asig.rol_asignado,
        "estado_actual": asig.aceptacion.estado_aceptacion if asig.aceptacion else "Pendiente",
        "archivos": [
            {"id": a.id_adjunto, "nombre": a.nombre_archivo}
            for t in asig.expediente.tickets for a in t.adjuntos
        ] if asig.expediente.tickets else []
    }


@app.post("/api/dictaminante/{uuid}/responder")
def responder_dictaminante(
    uuid: str,
    respuesta: str = Query(...),
    nota: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    asig = db.query(models.AsignacionTesis).filter(models.AsignacionTesis.uuid == uuid).first()
    if not asig:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    if respuesta not in ["Aceptado", "Rechazado"]:
        raise HTTPException(status_code=400, detail="Respuesta inválida")
        
    if not asig.aceptacion:
        asig.aceptacion = models.AceptacionDictaminante(id_asignacion=asig.id_asignacion)
    
    asig.aceptacion.estado_aceptacion = respuesta
    asig.aceptacion.nota = nota
    asig.aceptacion.fecha_respuesta = datetime.utcnow()
    
    registrar_movimiento(
        db, 
        asig.expediente, 
        "Clasificado", 
        f"Dictaminante {asig.docente.nombre_completo} respondió: {respuesta} - {nota or ''}",
        "Sistema (Link Mágico)"
    )
    db.commit()
    return {"status": "ok", "respuesta": respuesta}


# ──────────────────────────────────────────────────────────────────────────────
# EJE 3: Gestión de contraseñas
# ──────────────────────────────────────────────────────────────────────────────

@app.put("/api/auth/cambiar-password")
def cambiar_mi_password(
    payload: CambiarPasswordPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Cambio autenticado de contraseña; es la única salida del acceso restringido."""
    cambiar_password_propia(current_user, payload.password_actual, payload.nueva_password)
    # Una contraseña nueva inicia una sesión nueva: evita que el navegador siga
    # usando un token emitido antes de completar el cambio obligatorio.
    revocar_sesiones(db, current_user.id_usuario, "cambio_password", tipo=TIPO_NORMAL)
    db.commit()
    return {
        "status": "ok",
        "mensaje": "Contraseña actualizada. Inicia sesión nuevamente.",
        "debe_cambiar_password": False,
        "requiere_inicio_sesion": True,
        "fecha_cambio_password": current_user.fecha_cambio_password.isoformat(),
    }


@app.put("/api/usuarios/{id_usuario}/cambiar-password")
async def cambiar_password(
    id_usuario: int,
    request: Request,
    nueva_password: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Compatibilidad para autogestión y reinicio administrativo sin exponer claves."""
    datos = {}
    if "application/json" in request.headers.get("content-type", "").lower():
        try:
            datos = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="No se pudo leer la contraseña.")
    nueva_password = nueva_password or datos.get("nueva_password") or ""
    password_actual = datos.get("password_actual")
    if current_user.id_usuario != id_usuario and current_user.rol != "Administrador":
        raise HTTPException(status_code=403, detail="Sin permisos para cambiar esta contraseña.")
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if current_user.id_usuario == id_usuario:
        cambiar_password_propia(usuario, password_actual, nueva_password)
        mensaje = "Contraseña actualizada correctamente."
    else:
        restablecer_password_por_admin(usuario, nueva_password)
        mensaje = "Contraseña restablecida. La persona deberá cambiarla al ingresar."
    db.commit()
    return {"status": "ok", "mensaje": mensaje, "debe_cambiar_password": bool(usuario.debe_cambiar_password)}


@app.get("/api/auth/me")
def obtener_perfil(current_user: models.UsuarioSistema = Depends(get_current_user)):
    """Devuelve el perfil del usuario autenticado por el token JWT."""
    return {
        "id_usuario": current_user.id_usuario,
        "nombre_completo": current_user.nombre_completo,
        "correo": current_user.correo,
        "rol": current_user.rol,
        "debe_cambiar_password": bool(current_user.debe_cambiar_password),
        "fecha_cambio_password": current_user.fecha_cambio_password.isoformat() if current_user.fecha_cambio_password else None,
    }


@app.get("/api/reglas-resolucion")
def listar_reglas_resolucion(
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Consulta interna del catálogo vigente; no revela ni ejecuta integraciones externas."""
    reglas = (
        db.query(models.ReglaResolucionPaso)
        .order_by(models.ReglaResolucionPaso.id_paso, models.ReglaResolucionPaso.id_regla.desc())
        .all()
    )
    vigentes = {}
    for regla in reglas:
        vigentes.setdefault(regla.id_paso, regla)
    return {"data": [serializar_regla(regla) for regla in vigentes.values()]}


@app.put("/api/reglas-resolucion/{id_paso}")
def actualizar_regla_resolucion(
    id_paso: int,
    payload: ActualizarReglaResolucionPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    regla = regla_vigente(db, id_paso)
    if not regla:
        raise HTTPException(status_code=404, detail="No existe una regla vigente para este paso.")
    regla = versionar_regla(db, regla, payload.model_dump(exclude_unset=True), current_user)
    db.commit()
    db.refresh(regla)
    return serializar_regla(regla)


# ──────────────────────────────────────────────────────────────────────────────
# EJE 9: Control de versiones de revisiones de tesis
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/expedientes/{expediente_ref}/revisiones")
def listar_revisiones(expediente_ref: str, db: Session = Depends(get_db)):
    """Lista todas las revisiones/versiones de documentos de un expediente."""
    exp = obtener_expediente_por_ref(db, expediente_ref)
    revisiones = (
        db.query(models.RevisionTesis)
        .filter(models.RevisionTesis.id_expediente == exp.id_expediente)
        .order_by(models.RevisionTesis.fecha_revision.asc())
        .all()
    )
    return {
        "total": len(revisiones),
        "data": [
            {
                "id_revision": r.id_revision,
                "version_documento": r.version_documento,
                "tipo_revision": r.tipo_revision,
                "descripcion_observacion": r.descripcion_observacion,
                "archivo_observado_url": r.archivo_observado_url,
                "archivo_corregido_url": r.archivo_corregido_url,
                "fecha_revision": r.fecha_revision.strftime("%Y-%m-%d %H:%M:%S"),
                "fecha_correccion": r.fecha_correccion.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_correccion else None,
                "estado": r.estado,
                "docente": r.docente.nombre_completo if r.docente else None,
            }
            for r in revisiones
        ],
    }


@app.post("/api/expedientes/{expediente_ref}/revisiones")
def crear_revision(
    expediente_ref: str,
    tipo_revision: str = "Observacion",
    descripcion_observacion: Optional[str] = None,
    archivo_observado_url: Optional[str] = None,
    id_docente: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Registra una nueva observación/revisión de documento en el expediente."""
    exp = obtener_expediente_por_ref(db, expediente_ref)

    # Calcular la siguiente versión
    ultima_version = (
        db.query(models.RevisionTesis)
        .filter(models.RevisionTesis.id_expediente == exp.id_expediente)
        .count()
    )

    revision = models.RevisionTesis(
        id_expediente=exp.id_expediente,
        id_docente=id_docente,
        version_documento=ultima_version + 1,
        tipo_revision=tipo_revision,
        descripcion_observacion=descripcion_observacion,
        archivo_observado_url=archivo_observado_url,
        estado="Pendiente",
    )
    db.add(revision)
    registrar_movimiento(
        db,
        exp,
        "Observado",
        f"Revisión V{ultima_version + 1} registrada: {descripcion_observacion or tipo_revision}",
        current_user.nombre_completo,
    )
    db.commit()
    db.refresh(revision)
    return {
        "status": "ok",
        "id_revision": revision.id_revision,
        "version_documento": revision.version_documento,
    }


@app.put("/api/revisiones/{id_revision}/corregido")
def marcar_corregido(
    id_revision: int,
    archivo_corregido_url: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Marca una revisión como corregida, opcionalmente adjuntando el documento corregido."""
    revision = db.query(models.RevisionTesis).filter(models.RevisionTesis.id_revision == id_revision).first()
    if not revision:
        raise HTTPException(status_code=404, detail="Revisión no encontrada")
    revision.estado = "Corregido"
    revision.fecha_correccion = datetime.utcnow()
    if archivo_corregido_url:
        revision.archivo_corregido_url = archivo_corregido_url
    db.commit()
    return {"status": "ok", "id_revision": id_revision, "estado": "Corregido"}


@app.put("/api/revisiones/{id_revision}/aceptado")
def marcar_aceptado(
    id_revision: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Marca una revisión como aceptada (el docente aprueba la corrección)."""
    revision = db.query(models.RevisionTesis).filter(models.RevisionTesis.id_revision == id_revision).first()
    if not revision:
        raise HTTPException(status_code=404, detail="Revisión no encontrada")
    revision.estado = "Aceptado"
    revision.tipo_revision = "Aprobacion"
    db.commit()
    return {"status": "ok", "id_revision": id_revision, "estado": "Aceptado"}


# ──────────────────────────────────────────────────────────────────────────────
# EJE 8: Responder en osTicket via Playwright (inyección headless)
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/api/tickets/{ticket_ref}/responder-osticket")
def responder_en_osticket(
    ticket_ref: str,
    mensaje: str,
    tipo: str = Query("nota_interna", description="'nota_interna', 'respuesta_cliente' u 'observacion_estudiante'"),
    confirmar_envio: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Guarda nota local o crea una salida pendiente; E1 no escribe en osTicket."""
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    if not ticket.numero_visual:
        raise HTTPException(status_code=400, detail="El ticket no tiene número visual de osTicket")
    if tipo not in {"nota_interna", "respuesta_cliente", "observacion_estudiante"}:
        raise HTTPException(status_code=400, detail="Tipo de mensaje no permitido")
    if not mensaje.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacio")
    datos = dict(ticket.datos_extraidos or {})
    mensajes = list(datos.get("mensajes_locales") or [])
    mensajes.append(
        {
            "tipo": tipo,
            "mensaje": mensaje,
            "usuario": current_user.nombre_completo,
            "fecha": datetime.utcnow().isoformat(),
        }
    )
    datos["mensajes_locales"] = mensajes
    ticket.datos_extraidos = datos

    item = None
    creada = None
    if tipo in {"respuesta_cliente", "observacion_estudiante"}:
        es_observacion = tipo == "observacion_estudiante"
        payload = {
            "mensaje": mensaje.strip(),
            "ticket_numero": ticket.numero_visual,
            "cerrar_despues_de_responder": es_observacion,
        }
        validar_payload_salida(payload)
        prefijo = "osticket.observar" if es_observacion else "osticket.reply"
        clave = f"{prefijo}:{ticket.uuid}:{hashlib.sha256(mensaje.strip().encode('utf-8')).hexdigest()[:32]}"
        item, creada = crear_solicitud(
            db,
            actor=current_user,
            target_system="osticket",
            action_type="ticket.observar_y_cerrar" if es_observacion else "ticket.respuesta_cliente",
            subject_type="ticket",
            subject_uuid=ticket.uuid,
            idempotency_key=clave,
            payload=payload,
            ticket=ticket,
            expediente=ticket.expediente,
            sustento="Observación al estudiante solicitada desde bandeja" if es_observacion else "Respuesta al cliente solicitada desde bandeja",
        )
        registrar_accion(
            db, ticket, "observacion_solicitada" if es_observacion else "respuesta_cliente_solicitada",
            current_user, mensaje, {"outbox_uuid": item.uuid, "cerrar_despues": es_observacion},
        )
        sincronizar_accion_legacy(ticket, "observacion_solicitada" if es_observacion else "respuesta_cliente_solicitada", current_user, mensaje, tipo=tipo)
    else:
        registrar_accion(db, ticket, "nota_interna", current_user, mensaje, {"tipo": tipo})
        sincronizar_accion_legacy(ticket, "nota_interna", current_user, mensaje, tipo=tipo)

    # Registrar en historial local sin bloquear
    if ticket.id_expediente:
        exp = db.query(models.ExpedienteTesis).filter(
            models.ExpedienteTesis.id_expediente == ticket.id_expediente
        ).first()
        if exp:
            registrar_movimiento(
                db, exp, "Clasificado",
                f"{'Observación solicitada para aprobación' if tipo == 'observacion_estudiante' else 'Respuesta solicitada para aprobación' if tipo == 'respuesta_cliente' else 'Nota interna registrada'} #{ticket.numero_visual}: {mensaje[:200]}",
                current_user.nombre_completo,
            )
    db.commit()

    return {
        "status": "pendiente_aprobacion" if tipo in {"respuesta_cliente", "observacion_estudiante"} else "registrado_local",
        "ticket_id": ticket.ticket_id,
        "numero_visual": ticket.numero_visual,
        "tipo": tipo,
        "outbox_uuid": item.uuid if item else None,
        "creada": creada,
        "confirmar_envio": confirmar_envio,
    }


# ──────────────────────────────────────────────────────────────────────────────
# EJE 7: Sync Histórico Excel (Fuzzy Matching)
# ──────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=12)
def _leer_csv_conciliacion(ruta_texto: str, mtime_ns: int) -> tuple[dict, ...]:
    """Evita releer reportes históricos completos en cada navegación.

    El mtime forma parte de la llave: al regenerar un reporte, la siguiente
    petición lo relee automáticamente sin requerir reiniciar FastAPI.
    """
    del mtime_ns
    with Path(ruta_texto).open(encoding="utf-8") as archivo:
        return tuple(csv.DictReader(archivo))


@lru_cache(maxsize=4)
def _evidencias_conciliacion(ruta_texto: str, mtime_ns: int) -> dict[str, tuple[dict, ...]]:
    del mtime_ns
    evidencias: dict[str, list[dict]] = defaultdict(list)
    with Path(ruta_texto).open(encoding="utf-8") as archivo:
        for fila_catalogo in csv.DictReader(archivo):
            evidencias[fila_catalogo["clave_identidad"]].append({
                "id_documento": fila_catalogo["id_documento"],
                "resolucion": fila_catalogo["resolucion"],
                "fecha": fila_catalogo["fecha_resolucion"],
                "paso": fila_catalogo["paso"],
                "titulo": fila_catalogo["titulo_tesis"],
                "archivo": Path(fila_catalogo["source_path"]).name,
                "estudiante": fila_catalogo["nombre_fuente"],
                "grado": fila_catalogo["grado"],
                "programa": fila_catalogo["programa_normalizado"],
                "modalidad": fila_catalogo.get("modalidad") or "SIN_MODALIDAD",
            })
    return {clave: tuple(items) for clave, items in evidencias.items()}

@app.get("/api/admin/conciliacion-identidades")
def listar_conciliacion_identidades(
    tipo: str = Query("expediente", pattern="^(expediente|ticket|antecedente|legado)$"),
    estado: str = Query("pendiente", pattern="^(pendiente|identificado|todos)$"),
    q: str = Query("", max_length=160),
    limite: int = Query(100, ge=1, le=300),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    fuentes = {
        "expediente": (ROOT / "data" / "identidades_academicas" / "expedientes_impacto_migracion.csv", "id_expediente_actual", "estado_migracion"),
        "legado": (ROOT / "data" / "identidades_academicas" / "expedientes_impacto_migracion.csv", "id_expediente_actual", "estado_migracion"),
        "ticket": (ROOT / "data" / "identidades_academicas" / "tickets_remapeo_propuesto.csv", "ticket_id", "estado_propuesta"),
        "antecedente": (ROOT / "data" / "identidades_academicas" / "antecedentes_faltantes_p3_o_mas.csv", "clave_identidad", "pasos_previos_no_detectados"),
    }
    ruta, llave, campo_estado = fuentes[tipo]
    if not ruta.exists():
        raise HTTPException(status_code=409, detail="Aún no existe el reporte de conciliación. Ejecuta el análisis histórico.")
    filas = _leer_csv_conciliacion(str(ruta), ruta.stat().st_mtime_ns)
    ruta_catalogo = ROOT / "data" / "identidades_academicas" / "catalogo_identidades.csv"
    evidencias_por_clave = {}
    if ruta_catalogo.exists():
        evidencias_por_clave = _evidencias_conciliacion(
            str(ruta_catalogo), ruta_catalogo.stat().st_mtime_ns,
        )
    existentes = {
        (item.tipo_caso, item.referencia): item
        for item in db.query(models.ConciliacionIdentidad).filter(models.ConciliacionIdentidad.tipo_caso == tipo).all()
    }
    termino = normalizar_texto_busqueda(q)
    salida = []
    filas_visibles = []
    pendientes_reales = 0
    identificados = 0

    def trayectoria_compatible_con_expediente(fila: dict, clave: str) -> bool:
        """No ofrece Psicología para un expediente de Ingeniería Civil.

        Esta validación de presentación es intencionalmente redundante con el
        catálogo: protege la decisión humana si un CSV antiguo o una extracción
        defectuosa llega a incluir una trayectoria que no corresponde.
        """
        if tipo not in {"expediente", "legado"}:
            return True
        partes = clave.split("|", 3)
        if len(partes) != 4:
            return False
        nombre_candidato, grado_candidato, programa_candidato, _modalidad_candidata = partes
        nombre_actual = clave_nombre(fila.get("estudiante") or "")
        if nombre_actual and not nombres_equivalentes(nombre_actual, nombre_candidato):
            return False
        grado_actual = (fila.get("grado_actual") or "").strip()
        if grado_actual and grado_actual != grado_candidato:
            return False
        programa_actual = normalizar_texto_busqueda(fila.get("programa_actual") or "")
        programa_actual = re.sub(
            r"^(?:maestria|magister|doctorado|doctor)\s+(?:en|de)\s+",
            "",
            programa_actual,
            flags=re.IGNORECASE,
        ).strip()
        programa_normalizado = normalizar_texto_busqueda(programa_candidato)
        return not programa_actual or programa_actual == programa_normalizado

    for fila in filas:
        referencia = str(fila.get(llave) or "")
        # La pestaña de históricos es una consulta de los verdaderos legados,
        # no una vista "todos" del archivo de impacto. Un expediente que el
        # reproceso ya pudo vincular (como migrable_unico) debe desaparecer de
        # aquí automáticamente y seguir su flujo normal.
        if tipo == "legado" and fila.get("estado_migracion") != "sin_coincidencia_fuerte":
            continue
        decision = existentes.get((tipo, referencia))
        resuelto = bool(decision and decision.accion != "pendiente")
        claves_origen = [
            clave for clave in (fila.get("claves_candidatas") or fila.get("clave_identidad_propuesta") or "").split(" | ")
            if clave and trayectoria_compatible_con_expediente(fila, clave)
        ]
        requiere_decision = (
            tipo == "antecedente"
            or (tipo == "expediente" and fila.get("estado_migracion") != "migrable_unico" and bool(claves_origen))
            or (tipo == "ticket" and fila.get("estado_operativo") != "Archivado_historico" and (
                fila.get("estado_propuesta") == "ambiguo"
                or fila.get("candidato_archivo_historico") == "si"
                or fila.get("conflicto_academico") == "si"
            ))
        )
        identificado_automaticamente = (
            (tipo == "expediente" and fila.get("estado_migracion") in {"migrable_unico", "confirmado_humano"})
            or (tipo == "ticket" and fila.get("estado_propuesta") in {"propuesto", "confirmado_humano"})
        )
        if identificado_automaticamente:
            identificados += 1
        if requiere_decision and not resuelto:
            pendientes_reales += 1
        if estado == "pendiente" and resuelto:
            continue
        if estado == "pendiente" and not requiere_decision:
            continue
        if estado == "identificado" and not identificado_automaticamente:
            continue
        texto = " ".join(str(valor or "") for valor in fila.values())
        if termino and termino not in normalizar_texto_busqueda(texto):
            continue
        filas_visibles.append((fila, referencia, decision, resuelto, claves_origen, requiere_decision, identificado_automaticamente))

    # El resumen se calcula sobre todo el reporte, pero la vista sólo necesita
    # los elementos de la página solicitada.
    filas_visibles = filas_visibles[:limite]

    # Los detalles de origen se consultan en lote. Antes se hacía una consulta
    # por expediente y otra por sus firmas, dejando la pantalla con un N+1.
    referencias_expediente = [int(item[1]) for item in filas_visibles if tipo in {"expediente", "legado"} and item[1].isdigit()]
    referencias_ticket = [int(item[1]) for item in filas_visibles if tipo == "ticket" and item[1].isdigit()]
    expedientes_origen = {}
    firmas_por_expediente = defaultdict(list)
    tickets_origen = {}
    if referencias_expediente:
        expedientes_origen = {
            item.id_expediente: item for item in db.query(models.ExpedienteTesis).filter(
                models.ExpedienteTesis.id_expediente.in_(referencias_expediente)
            ).all()
        }
        for resolucion in db.query(models.ResolucionFirma).filter(
            models.ResolucionFirma.id_expediente.in_(referencias_expediente)
        ).all():
            firmas_por_expediente[resolucion.id_expediente].append(resolucion)
    if referencias_ticket:
        tickets_origen = {
            item.ticket_id: item for item in db.query(models.TicketOsticket).options(
                selectinload(models.TicketOsticket.adjuntos)
            ).filter(models.TicketOsticket.ticket_id.in_(referencias_ticket)).all()
        }

    for fila, referencia, decision, _resuelto, claves_origen, requiere_decision, identificado_automaticamente in filas_visibles:
        origen = None
        datos_salida = dict(fila)
        if tipo in {"expediente", "legado"}:
            expediente_origen = expedientes_origen.get(int(referencia)) if referencia.isdigit() else None
            if expediente_origen:
                origen = {
                    "resoluciones_vinculadas": [
                        {
                            "id_resolucion": resolucion.id_resolucion,
                            "paso": resolucion.id_paso_asociado,
                            "tipo": resolucion.tipo_documento or "Resolución histórica",
                            "fecha": resolucion.fecha_firma.date().isoformat() if resolucion.fecha_firma else "",
                            "archivo": Path(resolucion.archivo_drive_url or "").name or "Archivo sin nombre",
                            "disponible": bool(resolucion.archivo_drive_url),
                        }
                        for resolucion in sorted(
                            firmas_por_expediente[expediente_origen.id_expediente],
                            key=lambda item: (item.fecha_firma or item.fecha_solicitud or datetime.min),
                            reverse=True,
                        )
                    ]
                }
        if tipo == "ticket":
            ticket_origen = tickets_origen.get(int(referencia)) if referencia.isdigit() else None
            if ticket_origen:
                # El CSV es un plan de análisis; el vínculo vigente debe leerse
                # de la base. Así una desvinculación por conflicto no conserva
                # visualmente un expediente antiguo en la ficha del ticket.
                datos_salida["id_expediente_actual"] = str(ticket_origen.id_expediente or "")
                datos_salida["estado_operativo"] = ticket_origen.estado_operativo or ""
                origen = {
                    "asunto": ticket_origen.asunto or "Sin asunto",
                    "fecha": ticket_origen.fecha_creacion_osticket.isoformat(),
                    "cuerpo": (ticket_origen.cuerpo or "").strip()[:1800],
                    "adjuntos": [adjunto.nombre_archivo for adjunto in ticket_origen.adjuntos],
                }
        salida.append({
            "referencia": referencia,
            "tipo": tipo,
            "estado_origen": fila.get(campo_estado, ""),
            # La UI no debe inferir el estado a partir de si existe una decisión
            # humana: una coincidencia única ya está identificada y no se revisa.
            "requiere_decision": requiere_decision,
            "identificado_automaticamente": identificado_automaticamente,
            "datos": datos_salida,
            "decision": {
                "accion": decision.accion,
                "clave_identidad": decision.clave_identidad,
                "nota": decision.nota,
                "resuelto_por": decision.resuelto_por_nombre,
                "fecha": decision.fecha_resolucion.isoformat() if decision.fecha_resolucion else None,
            } if decision else None,
            "trayectorias": [
                {
                    "clave": clave,
                    "documentos": sorted(evidencias_por_clave.get(clave, []), key=lambda documento: documento["fecha"], reverse=True)[:12],
                }
                for clave in claves_origen
            ],
            "origen": origen,
        })
    resumen = {
        "total": sum(
            1 for fila in filas
            if tipo == "antecedente"
            or (tipo == "legado" and fila.get("estado_migracion") == "sin_coincidencia_fuerte")
            or (tipo == "expediente" and fila.get("estado_migracion") != "migrable_unico" and any(
                clave and trayectoria_compatible_con_expediente(fila, clave)
                for clave in (fila.get("claves_candidatas") or "").split(" | ")
            ))
            or (tipo == "ticket" and fila.get("estado_operativo") != "Archivado_historico" and (
                fila.get("estado_propuesta") == "ambiguo"
                or fila.get("candidato_archivo_historico") == "si"
                or fila.get("conflicto_academico") == "si"
            ))
        ),
        "pendientes": pendientes_reales,
        "identificados": identificados,
    }
    return {"resumen": resumen, "casos": salida[:limite]}


@app.get("/api/admin/conciliacion-operativa-tickets")
def listar_clasificacion_operativa_tickets(
    cola: str = Query("revision", pattern="^(revision|activos|todos)$"),
    q: str = Query("", max_length=160),
    limite: int = Query(200, ge=1, le=300),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    """Mesa de destino local: no mezcla identidad histórica con operación."""
    ruta_plan = ROOT / "data" / "identidades_academicas" / "tickets_remapeo_propuesto.csv"
    ruta_catalogo = ROOT / "data" / "identidades_academicas" / "catalogo_identidades.csv"
    plan_por_ticket = {}
    if ruta_plan.exists():
        for fila in _leer_csv_conciliacion(str(ruta_plan), ruta_plan.stat().st_mtime_ns):
            if (fila.get("ticket_id") or "").isdigit():
                plan_por_ticket[int(fila["ticket_id"])] = fila
    evidencias = _evidencias_conciliacion(str(ruta_catalogo), ruta_catalogo.stat().st_mtime_ns) if ruta_catalogo.exists() else {}
    decisiones = {
        item.referencia: item
        for item in db.query(models.ConciliacionIdentidad).filter(
            models.ConciliacionIdentidad.tipo_caso == "ticket"
        ).all()
    }
    termino = normalizar_texto_busqueda(q)
    salida = []
    estados_cola = {
        "revision": ("Revision_historica", "Revision_identidad"),
        "activos": ("Activo",),
        "todos": ("Activo", "Revision_historica", "Revision_identidad"),
    }[cola]
    tickets_cola = db.query(models.TicketOsticket).filter(
        models.TicketOsticket.estado_operativo.in_(estados_cola)
    ).order_by(models.TicketOsticket.fecha_creacion_osticket.desc()).all()
    for ticket in tickets_cola:
        registro = decisiones.get(str(ticket.ticket_id))
        decision_operativa = decision_actual_ticket(ticket).get("decision")
        # Una decisión de identidad (por ejemplo, conservar sin vínculo) no es
        # un cierre operativo. Debe seguir visible para que el tramitador
        # decida si el ticket permanece activo, se archiva con sustento o está
        # fuera del proceso.
        if decision_operativa or (registro and registro.accion in {
            "archivar_historico", "reactivar", "mantener_activo", "fuera_proceso"
        }):
            continue
        texto = " ".join((ticket.numero_visual or "", ticket.nombre_estudiante_osticket or "", ticket.asunto or "", ticket.cuerpo or ""))
        if termino and termino not in normalizar_texto_busqueda(texto):
            continue
        plan = plan_por_ticket.get(ticket.ticket_id, {})
        claves = [clave for clave in (plan.get("claves_candidatas") or plan.get("clave_identidad_propuesta") or "").split(" | ") if clave]
        datos = {
            "numero_visual": ticket.numero_visual,
            "estudiante": ticket.nombre_estudiante_osticket or "Sin nombre detectado",
            "codigo": ticket.codigo_alumno_osticket or "",
            "asunto": ticket.asunto or "Sin asunto",
            "fecha_ticket": ticket.fecha_creacion_osticket.date().isoformat(),
            "expediente_vinculado": ticket.id_expediente or "",
            "estado_operativo": ticket.estado_operativo,
            "situacion_actual": situacion_operativa_ticket(ticket),
            "paso_sugerido": plan.get("paso_sugerido") or "",
            "resultado_documental": plan.get("estado_propuesta") or "sin evidencia histórica",
            "lectura_operativa": ((ticket.datos_extraidos or {}).get("clasificacion_operativa") or {}).get("motivo") or "Sin lectura operativa registrada",
        }
        salida.append({
            "referencia": str(ticket.ticket_id), "tipo": "ticket", "estado_origen": ticket.estado_operativo,
            "requiere_decision": True, "identificado_automaticamente": False, "modo_operativo": True,
            "datos": datos,
            "decision": {"accion": registro.accion, "nota": registro.nota} if registro else None,
            "trayectorias": [
                {"clave": clave, "documentos": sorted(evidencias.get(clave, []), key=lambda doc: doc["fecha"], reverse=True)[:8]}
                for clave in claves
            ],
            "origen": {
                "fecha": ticket.fecha_creacion_osticket.isoformat(), "cuerpo": (ticket.cuerpo or "")[:1800],
                "adjuntos": [adjunto.nombre_archivo for adjunto in ticket.adjuntos],
            },
        })
    return {
        "resumen": {"pendientes": len(salida), "cola": cola, "tickets_en_cola": len(salida)},
        "casos": salida[:limite],
    }


@app.get("/api/admin/conciliacion-duplicados")
def listar_duplicados_trayectoria(
    estado: str = Query("pendiente", pattern="^(pendiente|decididos|todos)$"),
    q: str = Query("", max_length=160),
    limite: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    """Mesa de preparación de fusiones; no mueve datos todavía."""
    ruta = ROOT / "data" / "identidades_academicas" / "expedientes_duplicados_misma_trayectoria.csv"
    if not ruta.exists():
        raise HTTPException(status_code=409, detail="Aún no existe el reporte de duplicados históricos.")
    grupos: dict[str, list[dict]] = defaultdict(list)
    for fila in _leer_csv_conciliacion(str(ruta), ruta.stat().st_mtime_ns):
        clave = fila.get("clave_trayectoria") or ""
        if clave:
            grupos[clave].append(fila)
    decisiones = {
        item.referencia: item for item in db.query(models.ConciliacionIdentidad).filter(
            models.ConciliacionIdentidad.tipo_caso == "duplicado"
        ).all()
    }
    termino = normalizar_texto_busqueda(q)
    seleccionados = []
    for clave, filas in grupos.items():
        referencia = f"DUP-{hashlib.sha256(clave.encode('utf-8')).hexdigest()[:32]}"
        decision = decisiones.get(referencia)
        decidido = bool(decision and decision.accion != "pendiente")
        if estado == "pendiente" and decidido:
            continue
        if estado == "decididos" and not decidido:
            continue
        texto = " ".join(str(valor or "") for fila in filas for valor in fila.values())
        if termino and termino not in normalizar_texto_busqueda(texto):
            continue
        seleccionados.append((clave, filas, decision))
    seleccionados.sort(key=lambda item: min(int(fila["id_expediente_actual"]) for fila in item[1]))
    ids = [int(fila["id_expediente_actual"]) for _, filas, _ in seleccionados[:limite] for fila in filas]
    expedientes = {
        item.id_expediente: item for item in db.query(models.ExpedienteTesis).filter(
            models.ExpedienteTesis.id_expediente.in_(ids)
        ).all()
    }
    firmas = defaultdict(int)
    tickets = defaultdict(int)
    requisitos = defaultdict(int)
    firmas_detalle = defaultdict(list)
    tickets_detalle = defaultdict(list)
    requisitos_estado = defaultdict(lambda: defaultdict(int))
    if ids:
        for ident, total in db.query(models.ResolucionFirma.id_expediente, func.count()).filter(
            models.ResolucionFirma.id_expediente.in_(ids)
        ).group_by(models.ResolucionFirma.id_expediente):
            firmas[ident] = total
        for ident, total in db.query(models.TicketOsticket.id_expediente, func.count()).filter(
            models.TicketOsticket.id_expediente.in_(ids)
        ).group_by(models.TicketOsticket.id_expediente):
            tickets[ident] = total
        for ident, total in db.query(models.ExpedienteRequisito.id_expediente, func.count()).filter(
            models.ExpedienteRequisito.id_expediente.in_(ids)
        ).group_by(models.ExpedienteRequisito.id_expediente):
            requisitos[ident] = total
        for resolucion in db.query(models.ResolucionFirma).filter(
            models.ResolucionFirma.id_expediente.in_(ids)
        ).all():
            archivo = Path(resolucion.archivo_drive_url or "").name or "Resolución sin nombre"
            firmas_detalle[resolucion.id_expediente].append({
                "id_resolucion": resolucion.id_resolucion,
                "paso": resolucion.id_paso_asociado,
                "fecha": (resolucion.fecha_firma or resolucion.fecha_solicitud).date().isoformat() if (resolucion.fecha_firma or resolucion.fecha_solicitud) else "",
                "tipo": resolucion.tipo_documento or "Resolución histórica",
                "archivo": archivo,
                "disponible": bool(resolucion.archivo_drive_url),
            })
        for ticket in db.query(models.TicketOsticket).filter(
            models.TicketOsticket.id_expediente.in_(ids)
        ).all():
            tickets_detalle[ticket.id_expediente].append({
                "ticket_id": ticket.ticket_id,
                "numero_visual": ticket.numero_visual,
                "asunto": ticket.asunto or "Sin asunto",
                "fecha": ticket.fecha_creacion_osticket.date().isoformat() if ticket.fecha_creacion_osticket else "",
                "estado": ticket.estado_operativo,
            })
        for requisito in db.query(models.ExpedienteRequisito).filter(
            models.ExpedienteRequisito.id_expediente.in_(ids)
        ).all():
            requisitos_estado[requisito.id_expediente][requisito.estado or "Pendiente"] += 1
    salida = []
    for clave, filas, decision in seleccionados[:limite]:
        candidatos = []
        for fila in sorted(filas, key=lambda item: int(item["id_expediente_actual"])):
            ident = int(fila["id_expediente_actual"])
            exp = expedientes.get(ident)
            codigo_guardado = (exp.codigo_alumno if exp else fila.get("codigo_actual")) or ""
            codigo = normalizar_codigo_matricula(codigo_guardado)
            candidatos.append({
                "id_expediente": ident,
                "estudiante": fila.get("estudiante") or (exp.nombre_alumno if exp else ""),
                "programa": fila.get("programa_actual") or (exp.programa if exp else ""),
                "grado": fila.get("grado_actual") or (exp.grado_postula if exp else ""),
                "codigo": codigo,
                "codigo_invalido": codigo_guardado if codigo_guardado and not codigo else "",
                "estado": fila.get("estado_actual") or (exp.estado_expediente if exp else ""),
                "paso": exp.id_paso_actual if exp else None,
                "titulo": exp.titulo_tesis if exp else fila.get("titulo_actual") or "",
                "fecha_inicio": exp.fecha_inicio_tramite.date().isoformat() if exp and exp.fecha_inicio_tramite else "",
                "fecha_ultimo_movimiento": exp.fecha_ultimo_movimiento.date().isoformat() if exp and exp.fecha_ultimo_movimiento else "",
                "resoluciones": firmas[ident],
                "tickets": tickets[ident],
                "requisitos": requisitos[ident],
                "resoluciones_detalle": sorted(firmas_detalle[ident], key=lambda item: item["fecha"], reverse=True),
                "tickets_detalle": sorted(tickets_detalle[ident], key=lambda item: item["fecha"], reverse=True),
                "requisitos_estado": dict(requisitos_estado[ident]),
            })
        salida.append({
            "referencia": clave,
            "tipo": "duplicado",
            "requiere_decision": True,
            "identificado_automaticamente": False,
            "datos": {
                "estudiante": filas[0].get("estudiante") or "",
                "programa": filas[0].get("programa_actual") or "",
                "grado": filas[0].get("grado_actual") or "",
                "cantidad_expedientes": len(candidatos),
            },
            "duplicados": candidatos,
            "decision": {
                "accion": decision.accion, "clave_identidad": decision.clave_identidad,
                "nota": decision.nota, "fecha": decision.fecha_resolucion.isoformat() if decision.fecha_resolucion else None,
            } if decision else None,
        })
    return {
        "resumen": {"pendientes": sum(1 for _, _, item in seleccionados if not item or item.accion == "pendiente"), "total": len(grupos)},
        "casos": salida,
    }


@app.get("/api/resoluciones/documentos/{id_documento}/archivo")
def abrir_documento_resolucion(
    id_documento: int,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    documento = db.query(models.ResolucionDocumento).filter(models.ResolucionDocumento.id_documento == id_documento).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento de resolución no encontrado.")
    source_path = (documento.source_path or "").strip()
    ruta_relativa = Path(source_path)
    if not source_path or ruta_relativa.is_absolute() or ".." in ruta_relativa.parts or ruta_relativa.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="La referencia del PDF no es válida.")

    # Las resoluciones incorporadas desde Drive ya existen como archivos locales
    # bajo la bóveda cruda; las más antiguas pueden vivir únicamente en el ZIP.
    raiz_drive = (ROOT / "data" / "drive_resoluciones" / "raw").resolve()
    ruta_drive = (raiz_drive / ruta_relativa).resolve()
    if raiz_drive in ruta_drive.parents and ruta_drive.is_file():
        return FileResponse(
            ruta_drive,
            filename=ruta_drive.name,
            media_type="application/pdf",
            content_disposition_type="inline",
        )
    ruta_zip = Path(os.getenv("EPG_RESOLUCIONES_ZIP", "/opt/sistema_posgrado/data/input/resoluciones/2026/RESOLUCIONES FIRMADAS-20260707T150151Z-3-001.zip"))
    try:
        contenido, nombre = _leer_pdf_desde_zip_historico(
            ruta_zip, source_path, documento.resolucion_numero, str(documento.resolucion_anio or "") or None,
        )
    except (KeyError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="El PDF no está disponible en la bóveda local.")
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=500, detail="La bóveda histórica de resoluciones está dañada.") from exc
    return Response(content=contenido, media_type="application/pdf", headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(nombre)}"})


@app.post("/api/admin/conciliacion-identidades/{tipo}/{referencia}")
def resolver_conciliacion_identidad(
    tipo: str,
    referencia: str,
    payload: ResolverConciliacionPayload,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    if tipo not in {"expediente", "ticket", "antecedente", "legado", "duplicado"}:
        raise HTTPException(status_code=404, detail="Tipo de caso no reconocido.")
    item = db.query(models.ConciliacionIdentidad).filter(
        models.ConciliacionIdentidad.tipo_caso == tipo,
        models.ConciliacionIdentidad.referencia == referencia,
    ).first()
    if not item:
        item = models.ConciliacionIdentidad(tipo_caso=tipo, referencia=referencia)
        db.add(item)
    item.accion = payload.accion
    item.clave_identidad = payload.clave_identidad or None
    item.nota = payload.nota or None
    item.id_resuelto_por = current_user.id_usuario
    item.resuelto_por_nombre = current_user.nombre_completo
    item.fecha_resolucion = datetime.utcnow() if payload.accion != "pendiente" else None
    if tipo == "ticket" and payload.accion in {"archivar_historico", "reactivar", "mantener_activo", "fuera_proceso"}:
        try:
            ticket_id = int(referencia)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Referencia de ticket inválida.") from exc
        ticket = db.query(models.TicketOsticket).filter(models.TicketOsticket.ticket_id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado.")
        ticket.estado_operativo = {
            "archivar_historico": "Archivado_historico",
            "fuera_proceso": "Fuera_proceso",
        }.get(payload.accion, "Activo")
    db.commit()
    return {"ok": True, "referencia": referencia, "accion": item.accion}

@app.post("/api/admin/sync-historico")
def sync_historico_excel(
    archivo: UploadFile = File(...),
    umbral_similaridad: int = Query(85, ge=60, le=100),
    modo_dry_run: bool = Query(True, description="Si True, solo simula sin modificar la BD"),
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_admin),
):
    """
    Cruza el Excel histórico con los expedientes en BD usando Fuzzy Matching (Levenshtein).
    En modo dry_run=True, solo reporta lo que haría sin modificar nada.
    """
    try:
        from sync_historico_excel import sync_excel_con_bd
        resultado = sync_excel_con_bd(db, archivo.file, umbral_similaridad, modo_dry_run)
        return resultado
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="Módulo sync_historico_excel no disponible. Verifica que thefuzz esté instalado."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en sync: {str(e)}")


def verificar_inventario_capacidades() -> None:
    faltantes = rutas_mutables_sin_politica(app.routes)
    if faltantes:
        raise RuntimeError("Rutas mutables sin capacidad declarada: " + "; ".join(faltantes))


@app.on_event("startup")
def validar_inicio_e1() -> None:
    verificar_inventario_capacidades()
