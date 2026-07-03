from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from database import engine, SessionLocal, Base
from datetime import datetime
from typing import Optional
import models
from extractor import extraer_datos_cuerpo, extraer_todos_adjuntos

# Crear tablas nuevas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Sistema de Posgrado UAC",
    description="Motor Backend para la gestión de expedientes de tesis — EPG UAC",
    version="2.0.0",
    root_path="/bot-posgrado"
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

# ═══════════════════════════════════════════════════════════════════
# SALUD DEL SERVIDOR
# ═══════════════════════════════════════════════════════════════════

@app.get("/")
def estado_servidor():
    return {"status": "online", "mensaje": "🚀 API EPG-UAC v2.0 Operativa"}


# ═══════════════════════════════════════════════════════════════════
# AUTENTICACIÓN SIMPLE (sin contraseña, solo verifica que el usuario exista)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/usuarios")
def listar_usuarios(db: Session = Depends(get_db)):
    """Retorna todos los usuarios activos para el selector de login."""
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
def login(id_usuario: int, db: Session = Depends(get_db)):
    """Login simple: el usuario selecciona su nombre y confirma."""
    usuario = db.query(models.UsuarioSistema).filter(
        models.UsuarioSistema.id_usuario == id_usuario,
        models.UsuarioSistema.activo == True
    ).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "id_usuario": usuario.id_usuario,
        "nombre_completo": usuario.nombre_completo,
        "correo": usuario.correo,
        "rol": usuario.rol,
    }

@app.post("/api/usuarios")
def crear_usuario(
    nombre_completo: str,
    correo: str,
    rol: str,
    db: Session = Depends(get_db)
):
    u = models.UsuarioSistema(nombre_completo=nombre_completo, correo=correo, rol=rol)
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id_usuario": u.id_usuario, "nombre_completo": u.nombre_completo, "rol": u.rol}

@app.put("/api/usuarios/{id_usuario}")
def actualizar_usuario(
    id_usuario: int,
    nombre_completo: str,
    correo: str,
    rol: str,
    activo: bool = True,
    db: Session = Depends(get_db)
):
    u = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id_usuario == id_usuario).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    u.nombre_completo = nombre_completo
    u.correo = correo
    u.rol = rol
    u.activo = activo
    db.commit()
    return {"status": "ok"}

@app.delete("/api/usuarios/{id_usuario}")
def eliminar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    u = db.query(models.UsuarioSistema).filter(models.UsuarioSistema.id_usuario == id_usuario).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    u.activo = False
    db.commit()
    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD — KPIs
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/dashboard/kpis")
def obtener_kpis(db: Session = Depends(get_db)):
    """Retorna conteos clave para el dashboard."""
    total_tickets = db.query(models.TicketOsticket).count()
    tickets_nuevos = db.query(models.TicketOsticket).filter(
        models.TicketOsticket.estado_scraping == 'Adjuntos_Descargados',
        models.TicketOsticket.id_expediente == None
    ).count()
    total_expedientes = db.query(models.ExpedienteTesis).count()
    expedientes_en_proceso = db.query(models.ExpedienteTesis).filter(
        models.ExpedienteTesis.estado_expediente == 'En Proceso'
    ).count()
    expedientes_observados = db.query(models.ExpedienteTesis).filter(
        models.ExpedienteTesis.estado_expediente == 'Observado'
    ).count()
    graduados = db.query(models.ExpedienteTesis).filter(
        models.ExpedienteTesis.estado_expediente == 'Archivado_Graduado'
    ).count()

    # Distribución de expedientes por paso
    por_paso = []
    pasos = db.query(models.PasoFlujo).order_by(models.PasoFlujo.id_paso).all()
    for paso in pasos:
        count = db.query(models.ExpedienteTesis).filter(
            models.ExpedienteTesis.id_paso_actual == paso.id_paso,
            models.ExpedienteTesis.estado_expediente == 'En Proceso'
        ).count()
        por_paso.append({
            "id_paso": paso.id_paso,
            "nombre_paso": paso.nombre_paso,
            "total": count
        })

    return {
        "tickets_sincronizados": total_tickets,
        "tickets_sin_clasificar": tickets_nuevos,
        "total_expedientes": total_expedientes,
        "en_proceso": expedientes_en_proceso,
        "observados": expedientes_observados,
        "graduados": graduados,
        "distribucion_pasos": por_paso
    }


# ═══════════════════════════════════════════════════════════════════
# TICKETS (Bandeja del bot)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/tickets")
def obtener_bandeja_tickets(
    solo_sin_clasificar: bool = False,
    db: Session = Depends(get_db)
):
    """Retorna tickets con sus adjuntos. Opcionalmente filtra los no vinculados a expediente."""
    query = db.query(models.TicketOsticket).order_by(
        models.TicketOsticket.fecha_creacion_osticket.desc()
    )
    if solo_sin_clasificar:
        query = query.filter(models.TicketOsticket.id_expediente == None)

    tickets_db = query.all()
    resultados = []
    for ticket in tickets_db:
        lista_adjuntos = [
            {
                "id_archivo": adj.id_adjunto,
                "nombre": adj.nombre_archivo,
                "url_visor": adj.ruta_local
            }
            for adj in ticket.adjuntos
        ]
        resultados.append({
            "ticket_id": ticket.ticket_id,
            "numero_visual": ticket.numero_visual,
            "asunto": ticket.asunto,
            "estado": ticket.estado_scraping,
            "id_expediente": ticket.id_expediente,
            "fecha": ticket.fecha_creacion_osticket.strftime("%Y-%m-%d %H:%M:%S"),
            "adjuntos": lista_adjuntos,
            "datos_extraidos": ticket.datos_extraidos or {}
        })
    return {"total_tickets": len(resultados), "data": resultados}


@app.get("/api/tickets/{ticket_id}")
def obtener_ticket_detalle(ticket_id: int, db: Session = Depends(get_db)):
    """Retorna el detalle completo de un ticket incluyendo cuerpo y adjuntos."""
    ticket = db.query(models.TicketOsticket).filter(
        models.TicketOsticket.ticket_id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    adjuntos = [
        {
            "id_archivo": adj.id_adjunto,
            "nombre": adj.nombre_archivo,
            "url_visor": adj.ruta_local,
            "ruta_local": adj.ruta_local,
            "nombre_archivo": adj.nombre_archivo
        }
        for adj in ticket.adjuntos
    ]

    return {
        "ticket_id": ticket.ticket_id,
        "numero_visual": ticket.numero_visual,
        "asunto": ticket.asunto,
        "cuerpo": ticket.cuerpo,
        "estado": ticket.estado_scraping,
        "id_expediente": ticket.id_expediente,
        "fecha": ticket.fecha_creacion_osticket.strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_extraccion": ticket.fecha_extraccion.strftime("%Y-%m-%d %H:%M:%S") if ticket.fecha_extraccion else None,
        "adjuntos": adjuntos,
        "datos_extraidos": ticket.datos_extraidos or {}
    }


@app.get("/api/tickets/{ticket_id}/extraer-datos")
def extraer_datos_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Extrae datos estructurados del cuerpo del ticket Y del contenido de todos sus PDFs/DOCXs.
    Guarda el resultado en la columna datos_extraidos del ticket.
    """
    ticket = db.query(models.TicketOsticket).filter(
        models.TicketOsticket.ticket_id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # 1. Extraer del cuerpo del correo
    datos_cuerpo = extraer_datos_cuerpo(ticket.cuerpo or "")

    # 2. Extraer de todos los adjuntos (PDFs, DOCX)
    adjuntos_list = [
        {"nombre_archivo": adj.nombre_archivo, "ruta_local": adj.ruta_local}
        for adj in ticket.adjuntos
    ]
    resultado_adjuntos = extraer_todos_adjuntos(adjuntos_list)

    # 3. Fusionar: los datos de los PDFs complementan los del cuerpo
    datos_fusionados = {**resultado_adjuntos['datos_extraidos_pdfs'], **datos_cuerpo}

    # Guardar en BD
    ticket.datos_extraidos = {
        "datos_estructurados": datos_fusionados,
        "archivos_procesados": resultado_adjuntos['archivos_procesados'],
        "detalle_archivos": [
            {
                "nombre": d['nombre'],
                "paginas": d.get('paginas', 0),
                "datos": d.get('datos', {}),
                "texto_preview": d.get('texto_preview', '')
            }
            for d in resultado_adjuntos['detalle_archivos']
        ],
        "fecha_extraccion": datetime.utcnow().isoformat()
    }
    db.commit()

    return {
        "ticket_id": ticket_id,
        "datos_estructurados": datos_fusionados,
        "archivos_procesados": resultado_adjuntos['archivos_procesados'],
        "detalle_archivos": resultado_adjuntos['detalle_archivos']
    }


@app.post("/api/tickets/{ticket_id}/clasificar")
def clasificar_ticket(
    ticket_id: int,
    id_paso: int,
    nombre_alumno: str,
    codigo_alumno: str,
    grado_postula: str,
    titulo_tesis: Optional[str] = None,
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db)
):
    """
    Clasifica un ticket: crea un expediente (o vincula a uno existente)
    y lo coloca en el paso indicado.
    """
    ticket = db.query(models.TicketOsticket).filter(
        models.TicketOsticket.ticket_id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    paso = db.query(models.PasoFlujo).filter(models.PasoFlujo.id_paso == id_paso).first()
    if not paso:
        raise HTTPException(status_code=400, detail="Paso de flujo inválido")

    # Crear nuevo expediente
    expediente = models.ExpedienteTesis(
        codigo_alumno=codigo_alumno,
        nombre_alumno=nombre_alumno,
        grado_postula=grado_postula,
        titulo_tesis=titulo_tesis,
        id_paso_actual=id_paso,
        estado_expediente='En Proceso'
    )
    db.add(expediente)
    db.flush()  # Para obtener el id_expediente generado

    # Vincular ticket al expediente
    ticket.id_expediente = expediente.id_expediente
    ticket.estado_scraping = 'Procesado'

    # Registrar en historial
    movimiento = models.HistorialMovimiento(
        id_expediente=expediente.id_expediente,
        id_paso=id_paso,
        accion='Clasificado',
        nota=f"Ticket #{ticket.numero_visual} clasificado en Paso {id_paso}: {paso.nombre_paso}",
        usuario_nombre=usuario_nombre
    )
    db.add(movimiento)
    db.commit()

    return {
        "status": "ok",
        "id_expediente": expediente.id_expediente,
        "paso": paso.nombre_paso,
        "mensaje": f"Expediente creado y vinculado al ticket #{ticket.numero_visual}"
    }


# ═══════════════════════════════════════════════════════════════════
# EXPEDIENTES
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/expedientes")
def listar_expedientes(
    id_paso: Optional[int] = None,
    estado: Optional[str] = None,
    busqueda: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lista de expedientes con filtros opcionales por paso, estado y búsqueda de texto."""
    query = db.query(models.ExpedienteTesis).order_by(
        models.ExpedienteTesis.fecha_ultimo_movimiento.desc()
    )
    if id_paso:
        query = query.filter(models.ExpedienteTesis.id_paso_actual == id_paso)
    if estado:
        query = query.filter(models.ExpedienteTesis.estado_expediente == estado)
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            models.ExpedienteTesis.nombre_alumno.like(like) |
            models.ExpedienteTesis.codigo_alumno.like(like) |
            models.ExpedienteTesis.titulo_tesis.like(like)
        )

    expedientes = query.all()
    resultados = []
    for exp in expedientes:
        paso = db.query(models.PasoFlujo).filter(
            models.PasoFlujo.id_paso == exp.id_paso_actual
        ).first()
        resultados.append({
            "id_expediente": exp.id_expediente,
            "codigo_alumno": exp.codigo_alumno,
            "nombre_alumno": exp.nombre_alumno,
            "grado_postula": exp.grado_postula,
            "titulo_tesis": exp.titulo_tesis,
            "id_paso_actual": exp.id_paso_actual,
            "nombre_paso_actual": paso.nombre_paso if paso else "Desconocido",
            "estado_expediente": exp.estado_expediente,
            "fecha_inicio": exp.fecha_inicio_tramite.strftime("%Y-%m-%d") if exp.fecha_inicio_tramite else None,
            "fecha_ultimo_movimiento": exp.fecha_ultimo_movimiento.strftime("%Y-%m-%d") if exp.fecha_ultimo_movimiento else None,
        })
    return {"total": len(resultados), "data": resultados}


@app.get("/api/expedientes/{id_expediente}")
def obtener_expediente(id_expediente: int, db: Session = Depends(get_db)):
    """Detalle completo de un expediente: datos, historial y tickets vinculados."""
    exp = db.query(models.ExpedienteTesis).filter(
        models.ExpedienteTesis.id_expediente == id_expediente
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    paso_actual = db.query(models.PasoFlujo).filter(
        models.PasoFlujo.id_paso == exp.id_paso_actual
    ).first()

    # Historial de movimientos
    historial = []
    for mov in exp.historial:
        paso_mov = db.query(models.PasoFlujo).filter(
            models.PasoFlujo.id_paso == mov.id_paso
        ).first() if mov.id_paso else None
        historial.append({
            "id_movimiento": mov.id_movimiento,
            "accion": mov.accion,
            "nota": mov.nota,
            "usuario_nombre": mov.usuario_nombre,
            "fecha": mov.fecha_movimiento.strftime("%Y-%m-%d %H:%M:%S"),
            "nombre_paso": paso_mov.nombre_paso if paso_mov else None,
            "id_paso": mov.id_paso
        })

    # Tickets vinculados
    tickets = db.query(models.TicketOsticket).filter(
        models.TicketOsticket.id_expediente == id_expediente
    ).all()
    tickets_data = []
    for t in tickets:
        tickets_data.append({
            "ticket_id": t.ticket_id,
            "numero_visual": t.numero_visual,
            "asunto": t.asunto,
            "fecha": t.fecha_creacion_osticket.strftime("%Y-%m-%d"),
            "adjuntos_count": len(t.adjuntos),
            "datos_extraidos": t.datos_extraidos or {}
        })

    # Asignaciones de docentes
    asignaciones = []
    for asig in exp.asignaciones:
        docente = db.query(models.Docente).filter(
            models.Docente.id_docente == asig.id_docente
        ).first()
        asignaciones.append({
            "id_asignacion": asig.id_asignacion,
            "rol_asignado": asig.rol_asignado,
            "estado_asignacion": asig.estado_asignacion,
            "nombre_docente": docente.nombre_completo if docente else "Desconocido",
            "especialidad": docente.especialidad if docente else ""
        })

    return {
        "id_expediente": exp.id_expediente,
        "codigo_alumno": exp.codigo_alumno,
        "nombre_alumno": exp.nombre_alumno,
        "grado_postula": exp.grado_postula,
        "titulo_tesis": exp.titulo_tesis,
        "id_paso_actual": exp.id_paso_actual,
        "nombre_paso_actual": paso_actual.nombre_paso if paso_actual else "Desconocido",
        "estado_expediente": exp.estado_expediente,
        "fecha_inicio": exp.fecha_inicio_tramite.strftime("%Y-%m-%d %H:%M:%S") if exp.fecha_inicio_tramite else None,
        "fecha_ultimo_movimiento": exp.fecha_ultimo_movimiento.strftime("%Y-%m-%d %H:%M:%S") if exp.fecha_ultimo_movimiento else None,
        "carpeta_drive_url": exp.carpeta_drive_url,
        "historial": historial,
        "tickets": tickets_data,
        "asignaciones": asignaciones
    }


@app.post("/api/expedientes/{id_expediente}/avanzar")
def avanzar_expediente(
    id_expediente: int,
    nota: Optional[str] = None,
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db)
):
    """Avanza el expediente al siguiente paso del flujo."""
    exp = db.query(models.ExpedienteTesis).filter(
        models.ExpedienteTesis.id_expediente == id_expediente
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    if exp.id_paso_actual >= 7:
        # Llegó al paso final → Archivar como Graduado
        exp.estado_expediente = 'Archivado_Graduado'
        exp.fecha_ultimo_movimiento = datetime.utcnow()
        movimiento = models.HistorialMovimiento(
            id_expediente=id_expediente,
            id_paso=exp.id_paso_actual,
            accion='Archivado',
            nota=nota or "Expediente completado. Alumno graduado.",
            usuario_nombre=usuario_nombre
        )
        db.add(movimiento)
        db.commit()
        return {"status": "graduado", "mensaje": "El expediente ha sido completado. ¡Alumno graduado!"}

    paso_siguiente = exp.id_paso_actual + 1
    paso_obj = db.query(models.PasoFlujo).filter(
        models.PasoFlujo.id_paso == paso_siguiente
    ).first()

    exp.id_paso_actual = paso_siguiente
    exp.estado_expediente = 'En Proceso'
    exp.fecha_ultimo_movimiento = datetime.utcnow()

    movimiento = models.HistorialMovimiento(
        id_expediente=id_expediente,
        id_paso=paso_siguiente,
        accion='Avanzado',
        nota=nota or f"Aprobado. Avanzado a: {paso_obj.nombre_paso if paso_obj else paso_siguiente}",
        usuario_nombre=usuario_nombre
    )
    db.add(movimiento)
    db.commit()

    return {
        "status": "ok",
        "nuevo_paso": paso_siguiente,
        "nombre_paso": paso_obj.nombre_paso if paso_obj else str(paso_siguiente)
    }


@app.post("/api/expedientes/{id_expediente}/observar")
def observar_expediente(
    id_expediente: int,
    nota: str,
    usuario_nombre: Optional[str] = "Sistema",
    db: Session = Depends(get_db)
):
    """Marca el expediente como Observado con una nota explicativa."""
    exp = db.query(models.ExpedienteTesis).filter(
        models.ExpedienteTesis.id_expediente == id_expediente
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    exp.estado_expediente = 'Observado'
    exp.fecha_ultimo_movimiento = datetime.utcnow()

    movimiento = models.HistorialMovimiento(
        id_expediente=id_expediente,
        id_paso=exp.id_paso_actual,
        accion='Observado',
        nota=nota,
        usuario_nombre=usuario_nombre
    )
    db.add(movimiento)
    db.commit()

    return {"status": "ok", "mensaje": "Expediente marcado como observado"}


# ═══════════════════════════════════════════════════════════════════
# DOCENTES
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/docentes")
def listar_docentes(db: Session = Depends(get_db)):
    docentes = db.query(models.Docente).order_by(models.Docente.nombre_completo).all()
    resultados = []
    for d in docentes:
        carga_actual = db.query(models.AsignacionTesis).filter(
            models.AsignacionTesis.id_docente == d.id_docente,
            models.AsignacionTesis.estado_asignacion == 'Activo'
        ).count()
        resultados.append({
            "id_docente": d.id_docente,
            "dni": d.dni,
            "nombre_completo": d.nombre_completo,
            "especialidad": d.especialidad,
            "tipo_contrato": d.tipo_contrato,
            "estado": d.estado,
            "max_tesis_permitidas": d.max_tesis_permitidas,
            "carga_actual": carga_actual,
            "disponible": carga_actual < d.max_tesis_permitidas and d.estado == 'Activo'
        })
    return {"total": len(resultados), "data": resultados}

@app.post("/api/docentes")
def crear_docente(
    dni: str, nombre_completo: str, especialidad: Optional[str] = None,
    tipo_contrato: str = "Indeterminado", max_tesis: int = 5,
    db: Session = Depends(get_db)
):
    d = models.Docente(
        dni=dni, nombre_completo=nombre_completo, especialidad=especialidad,
        tipo_contrato=tipo_contrato, max_tesis_permitidas=max_tesis
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return {"id_docente": d.id_docente, "nombre_completo": d.nombre_completo}

@app.put("/api/docentes/{id_docente}")
def actualizar_docente(
    id_docente: int, nombre_completo: str, especialidad: Optional[str] = None,
    tipo_contrato: str = "Indeterminado", estado: str = "Activo",
    max_tesis: int = 5, db: Session = Depends(get_db)
):
    d = db.query(models.Docente).filter(models.Docente.id_docente == id_docente).first()
    if not d:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    d.nombre_completo = nombre_completo
    d.especialidad = especialidad
    d.tipo_contrato = tipo_contrato
    d.estado = estado
    d.max_tesis_permitidas = max_tesis
    db.commit()
    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════════════
# PASOS DEL FLUJO (Catálogo)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/pasos")
def listar_pasos(db: Session = Depends(get_db)):
    pasos = db.query(models.PasoFlujo).order_by(models.PasoFlujo.id_paso).all()
    return [{"id_paso": p.id_paso, "nombre_paso": p.nombre_paso, "descripcion": p.descripcion} for p in pasos]


# ═══════════════════════════════════════════════════════════════════
# LEGACY — Mantener compatibilidad con el endpoint anterior
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/tickets/{ticket_id}/cambiar-estado")
def cambiar_estado(ticket_id: int, nuevo_estado: str, db: Session = Depends(get_db)):
    ticket = db.query(models.TicketOsticket).filter(models.TicketOsticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    ticket.estado_scraping = nuevo_estado
    db.commit()
    return {"status": "ok", "nuevo_estado": nuevo_estado}