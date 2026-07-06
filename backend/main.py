import math
import os
import uuid as uuid_lib
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlalchemy.orm import Session

import models
from auth import (
    crear_token_acceso,
    get_current_admin,
    get_current_user,
    get_current_directora_o_admin,
    hashear_password,
    verificar_password,
)
from database import Base, SessionLocal, engine
from extractor import extraer_datos_cuerpo, extraer_todos_adjuntos, generar_resumen_ticket


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Sistema de Posgrado UAC",
    description="Motor Backend para la gestion de expedientes de tesis - EPG UAC",
    version="3.0.0",
    root_path="/bot-posgrado",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def es_uuid(valor: str) -> bool:
    try:
        uuid_lib.UUID(str(valor))
        return True
    except ValueError:
        return False


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
        "nombre_archivo": adj.nombre_archivo,
    }


def serializar_ticket(ticket, detalle=False):
    expediente_uuid = ticket.expediente.uuid if ticket.expediente else None
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
        "datos_extraidos": ticket.datos_extraidos or {},
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
            "resoluciones": [
                {
                    "id_resolucion": r.id_resolucion,
                    "id_paso_asociado": r.id_paso_asociado,
                    "tipo_documento": r.tipo_documento,
                    "archivo_drive_url": r.archivo_drive_url,
                    "estado_firma": r.estado_firma,
                    "fecha_solicitud": r.fecha_solicitud.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_solicitud else None,
                    "fecha_firma": r.fecha_firma.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_firma else None,
                }
                for r in resoluciones
            ],
        }
    )
    return data


def ejecutar_extraccion(db: Session, ticket: models.TicketOsticket):
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
    
    # Intentar clasificar y actualizar BD usando la carátula extraída
    caratula = datos_fusionados.get("caratula")
    if caratula:
        codigo = ticket.codigo_alumno_osticket or datos_fusionados.get("codigo_alumno") or caratula.get("alumno_orcid")
        if codigo:
            codigo = codigo.split('@')[0][:15]
        
        exp = None
        if codigo:
            exp = db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.codigo_alumno == codigo).first()
        elif caratula.get("nombre_alumno"):
            exp = db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.nombre_alumno == caratula["nombre_alumno"]).first()
            
        if not exp and codigo:
            exp = models.ExpedienteTesis(
                codigo_alumno=codigo,
                nombre_alumno=caratula.get("nombre_alumno") or ticket.nombre_estudiante_osticket or "Desconocido",
                grado_postula=caratula.get("grado_postula") or "Maestro",
                titulo_tesis=caratula.get("titulo_tesis"),
                id_paso_actual=1,
                estado_expediente="En Proceso",
            )
            db.add(exp)
            db.flush()
            registrar_movimiento(db, exp, "Creado", "Expediente creado automáticamente por extracción de PDF", "Sistema (IA)")
        elif exp:
            if caratula.get("titulo_tesis"):
                exp.titulo_tesis = caratula["titulo_tesis"]
            if caratula.get("nombre_alumno"):
                exp.nombre_alumno = caratula["nombre_alumno"]
            if caratula.get("grado_postula"):
                exp.grado_postula = caratula["grado_postula"]
            db.flush()
            
        if exp:
            ticket.id_expediente = exp.id_expediente
            ticket.estado_scraping = "Clasificado"
            
            nombre_asesor = caratula.get("nombre_asesor")
            if nombre_asesor:
                docente = db.query(models.Docente).filter(models.Docente.nombre_completo == nombre_asesor).first()
                if not docente:
                    docente = models.Docente(
                        dni=f"PEN-{uuid_lib.uuid4().hex[:6].upper()}",
                        nombre_completo=nombre_asesor,
                        correo=None,
                        tipo_contrato="Semestral",
                        estado="Activo",
                        max_tesis_permitidas=5
                    )
                    db.add(docente)
                    db.flush()
                
                existe_asig = db.query(models.AsignacionTesis).filter(
                    models.AsignacionTesis.id_expediente == exp.id_expediente,
                    models.AsignacionTesis.id_docente == docente.id_docente,
                    models.AsignacionTesis.rol_asignado == "Asesor"
                ).first()
                
                if not existe_asig:
                    asig = models.AsignacionTesis(
                        id_expediente=exp.id_expediente,
                        id_docente=docente.id_docente,
                        rol_asignado="Asesor",
                        estado_asignacion="Activo",
                    )
                    db.add(asig)
                    db.flush()

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
            "rol": u.rol,
        }
        for u in usuarios
    ]


@app.post("/api/auth/login")
def login(
    correo: str,
    password: str,
    # Compatibilidad legacy: si se pasa id_usuario sin password, modo sin contraseña
    id_usuario: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Login con correo+contraseña (JWT). Modo legacy por id_usuario si no hay hash."""
    if id_usuario and not correo:
        # Modo legacy: buscar por ID sin contraseña (solo si el usuario no tiene hash)
        usuario = db.query(models.UsuarioSistema).filter(
            models.UsuarioSistema.id_usuario == id_usuario,
            models.UsuarioSistema.activo == True,
        ).first()
        if not usuario or usuario.password_hash:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    else:
        usuario = db.query(models.UsuarioSistema).filter(
            models.UsuarioSistema.correo == correo,
            models.UsuarioSistema.activo == True,
        ).first()
        if not usuario:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        if usuario.password_hash:
            # Usuario con contraseña configurada — verificar
            if not verificar_password(password, usuario.password_hash):
                raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        else:
            # Usuario sin contraseña (modo legacy para migración)
            pass

    token = crear_token_acceso({
        "sub": str(usuario.id_usuario),
        "nombre": usuario.nombre_completo,
        "rol": usuario.rol,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "id_usuario": usuario.id_usuario,
        "nombre_completo": usuario.nombre_completo,
        "correo": usuario.correo,
        "rol": usuario.rol,
    }


@app.post("/api/usuarios")
def crear_usuario(nombre_completo: str, correo: str, rol: str, db: Session = Depends(get_db)):
    usuario = models.UsuarioSistema(nombre_completo=nombre_completo, correo=correo, rol=rol)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"id_usuario": usuario.id_usuario, "nombre_completo": usuario.nombre_completo, "rol": usuario.rol}


@app.put("/api/usuarios/{id_usuario}")
def actualizar_usuario(
    id_usuario: int,
    nombre_completo: str,
    correo: str,
    rol: str,
    activo: bool = True,
    db: Session = Depends(get_db),
):
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.nombre_completo = nombre_completo
    usuario.correo = correo
    usuario.rol = rol
    usuario.activo = activo
    db.commit()
    return {"status": "ok"}


@app.delete("/api/usuarios/{id_usuario}")
def eliminar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.activo = False
    db.commit()
    return {"status": "ok"}


@app.get("/api/dashboard/kpis")
def obtener_kpis(db: Session = Depends(get_db)):
    total_tickets = db.query(models.TicketOsticket).count()
    tickets_sin_clasificar = (
        db.query(models.TicketOsticket)
        .filter(models.TicketOsticket.id_expediente == None, models.TicketOsticket.estado_scraping != "Notificado")
        .count()
    )
    total_expedientes = db.query(models.ExpedienteTesis).count()
    expedientes_en_proceso = (
        db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.estado_expediente == "En Proceso").count()
    )
    expedientes_observados = (
        db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.estado_expediente == "Observado").count()
    )
    graduados = (
        db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.estado_expediente == "Archivado_Graduado").count()
    )

    por_paso = []
    for paso in db.query(models.PasoFlujo).order_by(models.PasoFlujo.id_paso).all():
        count = (
            db.query(models.ExpedienteTesis)
            .filter(
                models.ExpedienteTesis.id_paso_actual == paso.id_paso,
                models.ExpedienteTesis.estado_expediente == "En Proceso",
            )
            .count()
        )
        por_paso.append({"id_paso": paso.id_paso, "nombre_paso": paso.nombre_paso, "total": count})

    return {
        "tickets_sincronizados": total_tickets,
        "tickets_sin_clasificar": tickets_sin_clasificar,
        "total_expedientes": total_expedientes,
        "en_proceso": expedientes_en_proceso,
        "observados": expedientes_observados,
        "graduados": graduados,
        "distribucion_pasos": por_paso,
    }


@app.get("/api/tickets")
def obtener_bandeja_tickets(
    solo_sin_clasificar: bool = False,
    busqueda: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.TicketOsticket).order_by(models.TicketOsticket.fecha_creacion_osticket.desc())
    if solo_sin_clasificar:
        query = query.filter(models.TicketOsticket.id_expediente == None)
    if busqueda:
        like = f"%{busqueda.strip()}%"
        query = query.filter(
            or_(
                models.TicketOsticket.numero_visual.like(like),
                models.TicketOsticket.asunto.like(like),
                models.TicketOsticket.nombre_estudiante_osticket.like(like),
                models.TicketOsticket.codigo_alumno_osticket.like(like),
                models.TicketOsticket.email_estudiante.like(like),
            )
        )

    total, total_pages, tickets = paginar(query, page, per_page)
    return {
        "total_tickets": total,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": [serializar_ticket(ticket) for ticket in tickets],
    }


@app.get("/api/tickets/{ticket_ref}")
def obtener_ticket_detalle(ticket_ref: str, db: Session = Depends(get_db)):
    return serializar_ticket(obtener_ticket_por_ref(db, ticket_ref), detalle=True)


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
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
):
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    paso = db.query(models.PasoFlujo).filter(models.PasoFlujo.id_paso == id_paso).first()
    if not paso:
        raise HTTPException(status_code=400, detail="Paso de flujo invalido")

    expediente = models.ExpedienteTesis(
        codigo_alumno=codigo_alumno,
        nombre_alumno=nombre_alumno,
        grado_postula=grado_postula,
        titulo_tesis=titulo_tesis,
        id_paso_actual=id_paso,
        estado_expediente="En Proceso",
    )
    db.add(expediente)
    db.flush()

    ticket.id_expediente = expediente.id_expediente
    ticket.estado_scraping = "Clasificado"
    registrar_movimiento(db, expediente, "Creado", f"Expediente creado desde ticket #{ticket.numero_visual}", usuario_nombre)
    registrar_movimiento(
        db,
        expediente,
        "Clasificado",
        f"Ticket #{ticket.numero_visual} clasificado en Paso {id_paso}: {paso.nombre_paso}",
        usuario_nombre,
    )
    db.commit()
    db.refresh(expediente)

    return {
        "status": "ok",
        "id_expediente": expediente.id_expediente,
        "uuid": expediente.uuid,
        "paso": paso.nombre_paso,
        "mensaje": f"Expediente creado y vinculado al ticket #{ticket.numero_visual}",
    }


@app.post("/api/tickets/{ticket_ref}/cambiar-estado")
def cambiar_estado(ticket_ref: str, nuevo_estado: str, db: Session = Depends(get_db)):
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
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.ExpedienteTesis).order_by(models.ExpedienteTesis.fecha_ultimo_movimiento.desc())
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

    total, total_pages, expedientes = paginar(query, page, per_page)
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "data": [serializar_expediente_lista(exp) for exp in expedientes],
    }


@app.get("/api/expedientes/{expediente_ref}")
def obtener_expediente(expediente_ref: str, db: Session = Depends(get_db)):
    return serializar_expediente_detalle(db, obtener_expediente_por_ref(db, expediente_ref))


@app.post("/api/expedientes/{expediente_ref}/avanzar")
def avanzar_expediente(
    expediente_ref: str,
    nota: Optional[str] = None,
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)

    if exp.id_paso_actual >= 7:
        exp.estado_expediente = "Archivado_Graduado"
        exp.sub_estado = None
        exp.fecha_ultimo_movimiento = datetime.utcnow()
        registrar_movimiento(db, exp, "Archivado", nota or "Expediente completado. Alumno graduado.", usuario_nombre)
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
        usuario_nombre,
    )
    db.commit()
    return {"status": "ok", "nuevo_paso": paso_siguiente, "nombre_paso": paso_obj.nombre_paso if paso_obj else str(paso_siguiente)}


@app.post("/api/expedientes/{expediente_ref}/observar")
def observar_expediente(
    expediente_ref: str,
    nota: str,
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    exp.estado_expediente = "Observado"
    exp.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(db, exp, "Observado", nota, usuario_nombre)
    db.commit()
    return {"status": "ok", "mensaje": "Expediente marcado como observado"}


@app.post("/api/expedientes/{expediente_ref}/derivar-directora")
def derivar_directora(
    expediente_ref: str,
    nota: Optional[str] = None,
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    exp.sub_estado = "Derivado_Directora"
    exp.fecha_ultimo_movimiento = datetime.utcnow()
    registrar_movimiento(db, exp, "Derivado", nota or "Expediente derivado a Directora.", usuario_nombre)
    db.commit()
    return {"status": "ok", "sub_estado": exp.sub_estado}


def guardar_upload_resolucion(exp, archivo: UploadFile) -> str:
    uploads_dir = Path(os.getenv("EPG_UPLOADS_DIR", "/opt/sistema_posgrado/uploads/expedientes"))
    carpeta = uploads_dir / str(exp.uuid) / "resoluciones"
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / archivo.filename
    with destino.open("wb") as f:
        f.write(archivo.file.read())
    public_base = os.getenv("EPG_UPLOADS_PUBLIC_URL", "https://dataepis.uandina.pe:49267/expedientes")
    return f"{public_base}/{exp.uuid}/resoluciones/{archivo.filename}"


@app.post("/api/expedientes/{expediente_ref}/cargar-resolucion-directa")
def cargar_resolucion_directa(
    expediente_ref: str,
    tipo_documento: str = "Resolucion directa",
    archivo_url: Optional[str] = None,
    usuario_nombre: Optional[str] = "Sistema",
    archivo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
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
    registrar_movimiento(db, exp, "Resolucion_Cargada", f"{tipo_documento}: {url}", usuario_nombre)
    db.commit()
    return {"status": "ok", "id_resolucion": resolucion.id_resolucion, "archivo_url": url}


@app.post("/api/expedientes/{expediente_ref}/cambiar-titulo")
def cambiar_titulo(
    expediente_ref: str,
    nuevo_titulo: str,
    nota: Optional[str] = None,
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
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
        usuario_nombre,
    )
    db.commit()
    return {"status": "ok", "titulo_tesis": exp.titulo_tesis}


@app.post("/api/expedientes/{expediente_ref}/asignar-dictaminantes")
def asignar_dictaminantes(
    expediente_ref: str,
    docente_ids: str,
    reemplazar: bool = True,
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
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
    registrar_movimiento(db, exp, "Dictaminantes_Asignados", "Se asignaron 3 dictaminantes.", usuario_nombre)
    db.commit()
    return {"status": "ok", "asignaciones": [a.id_asignacion for a in nuevas], "sub_estado": exp.sub_estado}


@app.post("/api/expedientes/{expediente_ref}/notificar")
def notificar_expediente(
    expediente_ref: str,
    mensaje: str,
    ticket_id: Optional[int] = None,
    archivo_resolucion: Optional[str] = None,
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
):
    exp = obtener_expediente_por_ref(db, expediente_ref)
    resultado_bot = None
    if ticket_id:
        from notificador import notificar_alumno_via_bot

        resultado_bot = notificar_alumno_via_bot(ticket_id, mensaje, archivo_resolucion)
    else:
        for ticket in db.query(models.TicketOsticket).filter(models.TicketOsticket.id_expediente == exp.id_expediente).all():
            ticket.estado_scraping = "Notificado"

    registrar_movimiento(db, exp, "Notificado", mensaje[:500], usuario_nombre)
    db.commit()
    return {"status": "ok", "bot": resultado_bot}


@app.get("/api/directora/pendientes")
def listar_pendientes_directora(db: Session = Depends(get_db)):
    expedientes = (
        db.query(models.ExpedienteTesis)
        .filter(models.ExpedienteTesis.sub_estado.in_(["Derivado_Directora", "Pendiente_Dictaminantes", "Pendiente_Firma"]))
        .order_by(models.ExpedienteTesis.fecha_ultimo_movimiento.desc())
        .all()
    )
    return {"total": len(expedientes), "data": [serializar_expediente_detalle(db, exp) for exp in expedientes]}


@app.post("/api/resoluciones/{id_resolucion}/aprobar")
def aprobar_resolucion(id_resolucion: int, db: Session = Depends(get_db)):
    resolucion = db.query(models.ResolucionFirma).filter(models.ResolucionFirma.id_resolucion == id_resolucion).first()
    if not resolucion:
        raise HTTPException(status_code=404, detail="Resolucion no encontrada")
    resolucion.estado_firma = "Firmado"
    resolucion.fecha_firma = datetime.utcnow()
    exp = db.query(models.ExpedienteTesis).filter(models.ExpedienteTesis.id_expediente == resolucion.id_expediente).first()
    if exp:
        exp.sub_estado = None
        registrar_movimiento(db, exp, "Avanzado", f"Resolucion {id_resolucion} aprobada por Directora.", "Directora")
    db.commit()
    return {"status": "ok", "id_resolucion": id_resolucion}


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
    registrar_movimiento(db, exp, "Observado" if estado == "Rechazado" else "Avanzado", f"Dictaminante {estado.lower()}.", "Dictaminante")
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
    especialidad: Optional[str] = None,
    tipo_contrato: str = "Indeterminado",
    max_tesis: int = 5,
    db: Session = Depends(get_db),
):
    docente = models.Docente(
        dni=dni,
        nombre_completo=nombre_completo,
        correo=correo,
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
    especialidad: Optional[str] = None,
    tipo_contrato: str = "Indeterminado",
    estado: str = "Activo",
    max_tesis: int = 5,
    db: Session = Depends(get_db),
):
    docente = db.query(models.Docente).filter(models.Docente.id_docente == id_docente).first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    docente.nombre_completo = nombre_completo
    docente.correo = correo
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
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
):
    from importador_excel import importar_excel_expedientes

    resultado = importar_excel_expedientes(db, archivo.file, usuario_nombre=usuario_nombre)
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

@app.put("/api/usuarios/{id_usuario}/cambiar-password")
def cambiar_password(
    id_usuario: int,
    nueva_password: str,
    db: Session = Depends(get_db),
    current_user: models.UsuarioSistema = Depends(get_current_user),
):
    """Permite a un usuario cambiar su propia contraseña, o al admin cambiar la de cualquiera."""
    if current_user.id_usuario != id_usuario and current_user.rol != "Administrador":
        raise HTTPException(status_code=403, detail="Sin permisos para cambiar esta contraseña")
    usuario = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if len(nueva_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    usuario.password_hash = hashear_password(nueva_password)
    db.commit()
    return {"status": "ok", "mensaje": "Contraseña actualizada correctamente"}


@app.get("/api/auth/me")
def obtener_perfil(current_user: models.UsuarioSistema = Depends(get_current_user)):
    """Devuelve el perfil del usuario autenticado por el token JWT."""
    return {
        "id_usuario": current_user.id_usuario,
        "nombre_completo": current_user.nombre_completo,
        "correo": current_user.correo,
        "rol": current_user.rol,
    }


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
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
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
        usuario_nombre,
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
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
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
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db),
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
    tipo: str = Query("nota_interna", description="'nota_interna' o 'respuesta_cliente'"),
    usuario_nombre: Optional[str] = "Sistema",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    Inyecta una nota interna o respuesta al ticket real de osTicket
    usando Playwright en background. No bloquea la respuesta HTTP.
    """
    ticket = obtener_ticket_por_ref(db, ticket_ref)
    if not ticket.numero_visual:
        raise HTTPException(status_code=400, detail="El ticket no tiene número visual de osTicket")

    def _inyectar():
        try:
            from notificador import notificar_alumno_via_bot
            notificar_alumno_via_bot(ticket.ticket_id, mensaje)
        except Exception as e:
            print(f"[OSTICKET REPLY] Error al inyectar respuesta: {e}")

    if background_tasks:
        background_tasks.add_task(_inyectar)

    # Registrar en historial local sin bloquear
    if ticket.id_expediente:
        exp = db.query(models.ExpedienteTesis).filter(
            models.ExpedienteTesis.id_expediente == ticket.id_expediente
        ).first()
        if exp:
            registrar_movimiento(
                db, exp, "Notificado",
                f"Respuesta enviada a osTicket #{ticket.numero_visual}: {mensaje[:200]}",
                usuario_nombre
            )
            db.commit()

    return {
        "status": "enviado",
        "ticket_id": ticket.ticket_id,
        "numero_visual": ticket.numero_visual,
        "tipo": tipo,
    }


# ──────────────────────────────────────────────────────────────────────────────
# EJE 7: Sync Histórico Excel (Fuzzy Matching)
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/api/admin/sync-historico")
def sync_historico_excel(
    archivo: UploadFile = File(...),
    umbral_similaridad: int = Query(85, ge=60, le=100),
    modo_dry_run: bool = Query(True, description="Si True, solo simula sin modificar la BD"),
    db: Session = Depends(get_db),
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
