from datetime import datetime
import uuid as uuid_lib

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


def nuevo_uuid():
    return str(uuid_lib.uuid4())


class PasoFlujo(Base):
    __tablename__ = "cat_pasos_flujo"

    id_paso = Column(Integer, primary_key=True)
    nombre_paso = Column(String(150), nullable=False)
    descripcion = Column(Text)
    reglas_resolucion = relationship(
        "ReglaResolucionPaso",
        back_populates="paso",
        cascade="all, delete-orphan",
        # La versión es texto (2026.1, 2026.10); el identificador conserva el
        # orden real de las revisiones sin caer en un orden lexicográfico.
        order_by="ReglaResolucionPaso.id_regla.desc()",
    )


class UsuarioSistema(Base):
    __tablename__ = "usuarios_sistema"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre_completo = Column(String(150), nullable=False)
    correo = Column(String(150), unique=True, nullable=False)
    usuario_login = Column(String(80), unique=True, nullable=True, index=True)
    rol = Column(
        Enum("Administrador", "Recepcion", "Secretaria_Academica", "Directora", "Dictaminante", "Coordinacion_EPG"),
        nullable=False,
    )
    activo = Column(Boolean, default=True)
    password_hash = Column(String(255), nullable=True)  # NULL = login sin contraseña (modo legacy)
    debe_cambiar_password = Column(Boolean, nullable=False, default=False)
    fecha_cambio_password = Column(DateTime, nullable=True)


class SesionUsuario(Base):
    """Sesión revocable del servidor; el JWT por sí solo no concede acceso."""
    __tablename__ = "sesiones_usuario"

    jti = Column(String(36), primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(30), nullable=False, default="normal", index=True)
    id_administrador_origen = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    dispositivo_hash = Column(String(64), nullable=False)
    activa = Column(Boolean, nullable=False, default=True, index=True)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime, nullable=False, index=True)
    fecha_ultimo_uso = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_revocacion = Column(DateTime, nullable=True)
    motivo_revocacion = Column(String(100), nullable=True)

    usuario = relationship("UsuarioSistema", foreign_keys=[id_usuario])
    administrador_origen = relationship("UsuarioSistema", foreign_keys=[id_administrador_origen])


class ReglaResolucionPaso(Base):
    """Configuración institucional versionada del circuito de resolución por paso."""
    __tablename__ = "cat_reglas_resolucion_paso"
    __table_args__ = (UniqueConstraint("id_paso", "version", name="uq_regla_resolucion_paso_version"),)

    id_regla = Column(Integer, primary_key=True, autoincrement=True)
    id_paso = Column(Integer, ForeignKey("cat_pasos_flujo.id_paso", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(30), nullable=False, default="2026.1")
    estado_validacion = Column(String(30), nullable=False, default="Pendiente_Validacion", index=True)
    sistema_origen = Column(String(80), nullable=True)
    requiere_resolucion_direccion = Column(Boolean, nullable=True)
    requiere_consulta_previa = Column(Boolean, nullable=True)
    tipos_participantes = Column(JSON, nullable=True)
    cantidad_aceptaciones = Column(Integer, nullable=True)
    destinatarios_obligatorios = Column(JSON, nullable=True)
    vigencia_meses = Column(Integer, nullable=True)
    plazo_consulta_dias = Column(Integer, nullable=True)
    modalidades_respuesta = Column(JSON, nullable=True)
    nota_validacion = Column(Text, nullable=True)
    actualizado_por = Column(String(150), nullable=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    paso = relationship("PasoFlujo", back_populates="reglas_resolucion")


class Docente(Base):
    __tablename__ = "docentes"

    id_docente = Column(Integer, primary_key=True, autoincrement=True)
    dni = Column(String(15), unique=True, nullable=True)  # Nullable: docentes auto-creados desde PDF pueden no tener DNI
    nombre_completo = Column(String(150), nullable=False)
    correo = Column(String(150), nullable=True)
    correo_institucional = Column(String(150), nullable=True)
    correo_personal = Column(String(150), nullable=True)
    especialidad = Column(String(150))
    tipo_contrato = Column(Enum("Semestral", "Indeterminado", "Tiempo Completo", "Medio Tiempo"), nullable=False)
    estado = Column(Enum("Activo", "Inactivo", "De Licencia"), default="Activo")
    max_tesis_permitidas = Column(Integer, default=5)
    telefono = Column(String(40), nullable=True)
    direccion = Column(String(255), nullable=True)
    condicion_laboral = Column(String(100), nullable=True)
    titulo_profesional = Column(Text, nullable=True)
    universidad_procedencia = Column(Text, nullable=True)
    estado_verificacion = Column(String(40), nullable=False, default="Pendiente", index=True)
    fecha_verificacion = Column(DateTime, nullable=True)
    fuente_actualizacion = Column(String(255), nullable=True)

    asignaciones = relationship("AsignacionTesis", back_populates="docente")
    grados = relationship("DocenteGrado", back_populates="docente", cascade="all, delete-orphan")
    programas = relationship("DocentePrograma", back_populates="docente", cascade="all, delete-orphan")
    actividades = relationship("DocenteActividad", back_populates="docente", cascade="all, delete-orphan")
    documentos = relationship("DocenteDocumento", back_populates="docente", cascade="all, delete-orphan")
    actualizaciones = relationship("DocenteActualizacion", back_populates="docente", cascade="all, delete-orphan")


class ProgramaPosgrado(Base):
    __tablename__ = "programas_posgrado"

    id_programa = Column(Integer, primary_key=True, autoincrement=True)
    nivel = Column(String(20), nullable=False, index=True)
    nombre = Column(String(250), nullable=False, unique=True, index=True)
    slug = Column(String(250), nullable=True)
    url_fuente = Column(String(500), nullable=True)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    fecha_sincronizacion = Column(DateTime, nullable=False, default=datetime.utcnow)


class DocenteGrado(Base):
    __tablename__ = "docente_grados"
    __table_args__ = (UniqueConstraint("id_docente", "tipo", "denominacion", "fecha_diploma", name="uq_docente_grado_evidencia"),)
    id_grado = Column(Integer, primary_key=True, autoincrement=True)
    id_docente = Column(Integer, ForeignKey("docentes.id_docente", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(40), nullable=False, index=True)
    denominacion = Column(Text, nullable=False)
    universidad = Column(Text, nullable=True)
    pais = Column(String(100), nullable=True)
    fecha_diploma = Column(Date, nullable=True, index=True)
    fuente = Column(String(120), nullable=False, default="Padron EPG")
    verificado = Column(Boolean, nullable=False, default=False)
    docente = relationship("Docente", back_populates="grados")


class DocentePrograma(Base):
    __tablename__ = "docente_programas"
    __table_args__ = (UniqueConstraint("id_docente", "nivel", "programa", name="uq_docente_programa"),)
    id_programa_docente = Column(Integer, primary_key=True, autoincrement=True)
    id_docente = Column(Integer, ForeignKey("docentes.id_docente", ondelete="CASCADE"), nullable=False, index=True)
    id_programa_catalogo = Column(Integer, ForeignKey("programas_posgrado.id_programa", ondelete="SET NULL"), nullable=True, index=True)
    nivel = Column(String(20), nullable=False, index=True)
    programa = Column(String(200), nullable=False, index=True)
    tipo_vinculo = Column(String(30), nullable=False, default="Afinidad", index=True)
    especialidad = Column(String(200), nullable=True)
    estado = Column(String(30), nullable=False, default="Propuesto")
    fuente = Column(String(120), nullable=False, default="Padron EPG")
    docente = relationship("Docente", back_populates="programas")
    catalogo = relationship("ProgramaPosgrado", foreign_keys=[id_programa_catalogo])


class DocenteActividad(Base):
    __tablename__ = "docente_actividades"
    __table_args__ = (UniqueConstraint("id_docente", "periodo", "programa", name="uq_docente_actividad_periodo"),)
    id_actividad = Column(Integer, primary_key=True, autoincrement=True)
    id_docente = Column(Integer, ForeignKey("docentes.id_docente", ondelete="CASCADE"), nullable=False, index=True)
    periodo = Column(String(20), nullable=False, index=True)
    mes = Column(String(20), nullable=True, index=True)
    periodo_academico = Column(String(40), nullable=True, index=True)
    tipo_actividad = Column(String(60), nullable=False, default="Dictado")
    programa = Column(String(200), nullable=False, default="Sin especificar")
    detalle = Column(Text, nullable=True)
    registros = Column(Integer, nullable=False, default=1)
    fuente = Column(String(120), nullable=False, default="Programacion academica")
    docente = relationship("Docente", back_populates="actividades")


class DocenteTramite(Base):
    __tablename__ = "docente_tramites"
    id_tramite_docente = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    id_docente = Column(Integer, ForeignKey("docentes.id_docente", ondelete="SET NULL"), nullable=True, index=True)
    canal = Column(String(30), nullable=False)
    tipo = Column(String(100), nullable=False, index=True)
    estado = Column(String(30), nullable=False, default="Recibido", index=True)
    referencia = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=True)
    archivo_url = Column(String(500), nullable=True)
    fecha_recepcion = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por_nombre = Column(String(150), nullable=True)
    docente = relationship("Docente", foreign_keys=[id_docente])
    documentos = relationship("DocenteTramiteDocumento", back_populates="tramite", cascade="all, delete-orphan")
    eventos = relationship("DocenteTramiteEvento", back_populates="tramite", cascade="all, delete-orphan", order_by="DocenteTramiteEvento.fecha_registro")


class DocenteTramiteDocumento(Base):
    __tablename__ = "docente_tramite_documentos"
    id_documento = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    id_tramite_docente = Column(Integer, ForeignKey("docente_tramites.id_tramite_docente", ondelete="CASCADE"), nullable=False, index=True)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    hash_sha256 = Column(String(64), nullable=False, index=True)
    cargado_por_nombre = Column(String(150), nullable=True)
    fecha_carga = Column(DateTime, nullable=False, default=datetime.utcnow)
    tramite = relationship("DocenteTramite", back_populates="documentos")


class DocenteTramiteEvento(Base):
    __tablename__ = "docente_tramite_eventos"
    id_evento = Column(Integer, primary_key=True, autoincrement=True)
    id_tramite_docente = Column(Integer, ForeignKey("docente_tramites.id_tramite_docente", ondelete="CASCADE"), nullable=False, index=True)
    accion = Column(String(60), nullable=False)
    estado_anterior = Column(String(30), nullable=True)
    estado_nuevo = Column(String(30), nullable=True)
    nota = Column(Text, nullable=True)
    usuario_nombre = Column(String(150), nullable=True)
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)
    tramite = relationship("DocenteTramite", back_populates="eventos")


class DocenteDocumento(Base):
    __tablename__ = "docente_documentos"
    id_documento_docente = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    id_docente = Column(Integer, ForeignKey("docentes.id_docente", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(40), nullable=False, default="Otro", index=True)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    hash_sha256 = Column(String(64), nullable=False, index=True)
    texto_extraido = Column(Text, nullable=True)
    estado_revision = Column(String(30), nullable=False, default="Pendiente", index=True)
    nota_revision = Column(Text, nullable=True)
    cargado_por_nombre = Column(String(150), nullable=True)
    fecha_carga = Column(DateTime, nullable=False, default=datetime.utcnow)
    docente = relationship("Docente", back_populates="documentos")


class DocenteActualizacion(Base):
    __tablename__ = "docente_actualizaciones"

    id_actualizacion = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    id_docente = Column(Integer, ForeignKey("docentes.id_docente", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    estado = Column(String(30), nullable=False, default="Pendiente_envio", index=True)
    correos_destino = Column(JSON, nullable=True)
    payload_propuesto = Column(JSON, nullable=True)
    nota_revision = Column(Text, nullable=True)
    fecha_expiracion = Column(DateTime, nullable=False)
    fecha_primer_acceso = Column(DateTime, nullable=True)
    fecha_envio = Column(DateTime, nullable=True)
    fecha_respuesta = Column(DateTime, nullable=True)
    fecha_revision = Column(DateTime, nullable=True)
    creado_por_nombre = Column(String(150), nullable=True)
    docente = relationship("Docente", back_populates="actualizaciones")
    documentos = relationship("DocenteActualizacionDocumento", back_populates="actualizacion", cascade="all, delete-orphan")


class DocenteActualizacionDocumento(Base):
    __tablename__ = "docente_actualizacion_documentos"

    id_documento = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    id_actualizacion = Column(Integer, ForeignKey("docente_actualizaciones.id_actualizacion", ondelete="CASCADE"), nullable=False, index=True)
    tipo = Column(String(40), nullable=False, default="Otro", index=True)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    hash_sha256 = Column(String(64), nullable=False, index=True)
    texto_extraido = Column(Text, nullable=True)
    datos_sugeridos = Column(JSON, nullable=True)
    estado_revision = Column(String(30), nullable=False, default="Pendiente", index=True)
    nota_revision = Column(Text, nullable=True)
    fecha_carga = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizacion = relationship("DocenteActualizacion", back_populates="documentos")


class ExpedienteTesis(Base):
    __tablename__ = "expedientes_tesis"

    id_expediente = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    codigo_alumno = Column(String(20), nullable=False)
    nombre_alumno = Column(String(150), nullable=False)
    grado_postula = Column(Enum("Maestro", "Doctor"), nullable=False)
    programa = Column(String(250), nullable=True)
    titulo_tesis = Column(Text)
    id_paso_actual = Column(Integer, ForeignKey("cat_pasos_flujo.id_paso"), default=1)
    estado_expediente = Column(Enum("En Proceso", "Observado", "Archivado_Graduado", "Caduco"), default="En Proceso")
    sub_estado = Column(String(50), nullable=True)
    fecha_inicio_tramite = Column(DateTime, default=datetime.utcnow)
    fecha_ultimo_movimiento = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    carpeta_drive_url = Column(String(500))

    paso_actual = relationship("PasoFlujo", foreign_keys=[id_paso_actual])
    asignaciones = relationship("AsignacionTesis", back_populates="expediente", cascade="all, delete-orphan")
    historial = relationship(
        "HistorialMovimiento",
        back_populates="expediente",
        cascade="all, delete-orphan",
        order_by="HistorialMovimiento.fecha_movimiento",
    )
    tickets = relationship("TicketOsticket", back_populates="expediente", cascade="save-update, merge")
    requisitos = relationship(
        "ExpedienteRequisito",
        back_populates="expediente",
        cascade="all, delete-orphan",
        order_by="ExpedienteRequisito.id_expediente_requisito",
    )
    revisiones = relationship(
        "RevisionTesis",
        back_populates="expediente",
        cascade="all, delete-orphan",
        order_by="RevisionTesis.fecha_revision",
    )
    tramites_resolucion = relationship(
        "ResolucionTramite",
        back_populates="expediente",
        cascade="all, delete-orphan",
        order_by="ResolucionTramite.fecha_creacion",
    )


class AsignacionTesis(Base):
    __tablename__ = "asignaciones_tesis"

    id_asignacion = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="CASCADE"))
    id_docente = Column(Integer, ForeignKey("docentes.id_docente", ondelete="CASCADE"))
    rol_asignado = Column(Enum("Asesor", "Dictaminante", "Replicante", "Jurado"), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    estado_asignacion = Column(Enum("Activo", "Concluido", "Renuncia"), default="Activo")

    expediente = relationship("ExpedienteTesis", back_populates="asignaciones")
    docente = relationship("Docente", back_populates="asignaciones")
    aceptacion = relationship(
        "AceptacionDictaminante",
        back_populates="asignacion",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AceptacionDictaminante(Base):
    __tablename__ = "aceptaciones_dictaminante"

    id_aceptacion = Column(Integer, primary_key=True, autoincrement=True)
    id_asignacion = Column(Integer, ForeignKey("asignaciones_tesis.id_asignacion", ondelete="CASCADE"), nullable=False)
    estado_aceptacion = Column(Enum("Pendiente", "Aceptado", "Rechazado"), default="Pendiente")
    nota = Column(Text, nullable=True)
    fecha_respuesta = Column(DateTime, nullable=True)

    asignacion = relationship("AsignacionTesis", back_populates="aceptacion")


class TicketOsticket(Base):
    __tablename__ = "tickets_osticket"

    ticket_id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    numero_visual = Column(String(20), nullable=False)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="CASCADE"), nullable=True)
    asunto = Column(String(255))
    cuerpo = Column(Text)
    estado_scraping = Column(
        Enum(
            "Pendiente_Descarga",
            "Archivos_Descargados",
            "Datos_Extraidos",
            "Clasificado",
            "Notificado",
            "Error",
        ),
        default="Pendiente_Descarga",
    )
    nombre_estudiante_osticket = Column(String(200), nullable=True)
    email_estudiante = Column(String(200), nullable=True)
    codigo_alumno_osticket = Column(String(30), nullable=True)
    fecha_creacion_osticket = Column(DateTime, nullable=False)
    fecha_extraccion = Column(DateTime, default=datetime.utcnow)
    datos_extraidos = Column(JSON, nullable=True)
    estado_operativo = Column(String(30), nullable=False, default="Activo", index=True)

    adjuntos = relationship("TicketAdjunto", back_populates="ticket", cascade="all, delete-orphan")
    expediente = relationship("ExpedienteTesis", foreign_keys=[id_expediente], back_populates="tickets")
    decisiones_normalizadas = relationship(
        "TicketDecision",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketDecision.fecha_registro",
    )
    acciones_normalizadas = relationship(
        "TicketAction",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketAction.fecha_registro",
    )
    resoluciones_ticket = relationship(
        "TicketResolucion",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketResolucion.fecha_propuesta",
    )


class TicketAdjunto(Base):
    __tablename__ = "ticket_adjuntos"

    id_adjunto = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets_osticket.ticket_id", ondelete="CASCADE"))
    nombre_archivo = Column(String(255), nullable=False)
    ruta_local = Column(String(500), nullable=False)

    ticket = relationship("TicketOsticket", back_populates="adjuntos")


class ResolucionFirma(Base):
    __tablename__ = "resoluciones_firmas"

    id_resolucion = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="CASCADE"))
    id_paso_asociado = Column(Integer, ForeignKey("cat_pasos_flujo.id_paso"))
    tipo_documento = Column(String(100))
    archivo_drive_url = Column(String(500))
    estado_firma = Column(Enum("Pendiente_Directora", "Firmado", "Rechazado"), default="Pendiente_Directora")
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_firma = Column(DateTime, nullable=True)


class ResolucionTramite(Base):
    """Circuito institucional de elaboración, firma y notificación de una resolución."""
    __tablename__ = "resolucion_tramites"

    id_tramite = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    id_expediente = Column(
        Integer,
        ForeignKey("expedientes_tesis.id_expediente", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticket_id = Column(Integer, ForeignKey("tickets_osticket.ticket_id", ondelete="SET NULL"), nullable=True, index=True)
    id_resolucion_firma = Column(
        Integer,
        ForeignKey("resoluciones_firmas.id_resolucion", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    id_paso = Column(Integer, ForeignKey("cat_pasos_flujo.id_paso"), nullable=False, index=True)
    tipo_resolucion = Column(String(150), nullable=False)
    numero_resolucion = Column(String(50), nullable=True, index=True)
    fecha_resolucion = Column(DateTime, nullable=True)
    estado = Column(String(50), nullable=False, default="derivado_secretaria", index=True)
    sistema_origen = Column(String(50), nullable=False, default="Sistema EPG")
    referencia_origen = Column(String(150), nullable=True)
    requiere_consulta_previa = Column(Boolean, nullable=False, default=False)
    regla_version_aplicada = Column(String(30), nullable=True)
    vigencia_meses = Column(Integer, nullable=True)
    fecha_vencimiento = Column(DateTime, nullable=True)
    borrador_word_url = Column(String(500), nullable=True)
    borrador_word_nombre = Column(String(255), nullable=True)
    borrador_version = Column(Integer, nullable=False, default=1)
    pdf_firmado_url = Column(String(500), nullable=True)
    pdf_firmado_nombre = Column(String(255), nullable=True)
    pdf_firmado_hash = Column(String(64), nullable=True)
    observacion_actual = Column(Text, nullable=True)
    id_creado_por = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    creado_por_nombre = Column(String(150), nullable=True)
    creado_por_rol = Column(String(50), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    fecha_firma = Column(DateTime, nullable=True)
    fecha_notificacion = Column(DateTime, nullable=True)

    expediente = relationship("ExpedienteTesis", back_populates="tramites_resolucion")
    ticket = relationship("TicketOsticket", foreign_keys=[ticket_id])
    resolucion_firma = relationship("ResolucionFirma", foreign_keys=[id_resolucion_firma])
    paso = relationship("PasoFlujo", foreign_keys=[id_paso])
    creado_por = relationship("UsuarioSistema", foreign_keys=[id_creado_por])
    eventos = relationship(
        "ResolucionTramiteEvento",
        back_populates="tramite",
        cascade="all, delete-orphan",
        order_by="ResolucionTramiteEvento.fecha_registro",
    )
    consultas = relationship(
        "ResolucionConsulta",
        back_populates="tramite",
        cascade="all, delete-orphan",
        order_by="ResolucionConsulta.fecha_creacion",
    )
    notificaciones = relationship(
        "ResolucionNotificacion",
        back_populates="tramite",
        cascade="all, delete-orphan",
        order_by="ResolucionNotificacion.fecha_creacion",
    )


class ResolucionTramiteEvento(Base):
    __tablename__ = "resolucion_tramite_eventos"

    id_evento = Column(Integer, primary_key=True, autoincrement=True)
    id_tramite = Column(
        Integer,
        ForeignKey("resolucion_tramites.id_tramite", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    accion = Column(String(80), nullable=False)
    estado_anterior = Column(String(50), nullable=True)
    estado_nuevo = Column(String(50), nullable=False)
    nota = Column(Text, nullable=True)
    detalle = Column(JSON, nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    usuario_nombre = Column(String(150), nullable=True)
    usuario_rol = Column(String(50), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    tramite = relationship("ResolucionTramite", back_populates="eventos")
    usuario = relationship("UsuarioSistema", foreign_keys=[id_usuario])


class ResolucionConsulta(Base):
    """Consulta previa de disponibilidad; todavía no constituye designación."""
    __tablename__ = "resolucion_consultas"
    __table_args__ = (UniqueConstraint("id_tramite", "id_docente", "tipo_participacion", name="uq_consulta_tramite_docente_rol"),)

    id_consulta = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    id_tramite = Column(
        Integer,
        ForeignKey("resolucion_tramites.id_tramite", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_docente = Column(Integer, ForeignKey("docentes.id_docente", ondelete="RESTRICT"), nullable=False, index=True)
    tipo_participacion = Column(String(50), nullable=False)
    estado = Column(String(20), nullable=False, default="Pendiente", index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    fecha_expiracion = Column(DateTime, nullable=False)
    nota_respuesta = Column(Text, nullable=True)
    modalidad_respuesta = Column(String(30), nullable=False, default="Respuesta")
    canal_correo = Column(String(20), nullable=False, default="institucional")
    correos_destino = Column(JSON, nullable=True)
    asunto_consulta = Column(String(255), nullable=True)
    mensaje_consulta = Column(Text, nullable=True)
    respuesta_archivo_url = Column(String(500), nullable=True)
    respuesta_archivo_nombre = Column(String(255), nullable=True)
    respuesta_archivo_hash = Column(String(64), nullable=True)
    constancia_aceptada = Column(Boolean, nullable=False, default=False)
    fecha_respuesta = Column(DateTime, nullable=True)
    fecha_primer_acceso = Column(DateTime, nullable=True)
    fecha_ultimo_acceso = Column(DateTime, nullable=True)
    cantidad_accesos = Column(Integer, nullable=False, default=0)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    tramite = relationship("ResolucionTramite", back_populates="consultas")
    docente = relationship("Docente", foreign_keys=[id_docente])


class ConsultaPlantilla(Base):
    """Texto reutilizable para invitaciones de consulta a docentes."""
    __tablename__ = "resolucion_consulta_plantillas"

    id_plantilla = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(120), nullable=False)
    asunto = Column(String(255), nullable=False)
    mensaje = Column(Text, nullable=False)
    modalidad_respuesta = Column(String(30), nullable=False, default="Respuesta")
    activa = Column(Boolean, nullable=False, default=True)
    id_creado_por = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    creado_por_nombre = Column(String(150), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    creado_por = relationship("UsuarioSistema", foreign_keys=[id_creado_por])


class ResolucionNotificacion(Base):
    """Constancia local de notificación realizada por el tramitador."""
    __tablename__ = "resolucion_notificaciones"

    id_notificacion = Column(Integer, primary_key=True, autoincrement=True)
    id_tramite = Column(
        Integer,
        ForeignKey("resolucion_tramites.id_tramite", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    destinatario_tipo = Column(String(40), nullable=False)
    destinatario_nombre = Column(String(180), nullable=False)
    destinatario_referencia = Column(String(200), nullable=True)
    canal = Column(String(50), nullable=False)
    estado = Column(String(20), nullable=False, default="Pendiente", index=True)
    evidencia = Column(Text, nullable=True)
    id_registrado_por = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    registrado_por_nombre = Column(String(150), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_confirmacion = Column(DateTime, nullable=True)

    tramite = relationship("ResolucionTramite", back_populates="notificaciones")
    registrado_por = relationship("UsuarioSistema", foreign_keys=[id_registrado_por])


class ResolucionDocumento(Base):
    """Staging de resoluciones PDF antes de crear/actualizar expedientes."""
    __tablename__ = "resoluciones_documentos"

    id_documento = Column(Integer, primary_key=True, autoincrement=True)
    source_hash = Column(String(64), unique=True, nullable=False, index=True)
    source_path = Column(String(500), nullable=False)
    archivo_normalizado = Column(String(255), nullable=True)
    resolucion_numero = Column(String(30), nullable=True)
    resolucion_anio = Column(Integer, nullable=True)
    fecha_resolucion = Column(DateTime, nullable=True)
    expediente_admin = Column(String(30), nullable=True)
    codigo_alumno = Column(String(30), nullable=True)
    nombre_alumno = Column(String(200), nullable=True)
    grado_postula = Column(Enum("Maestro", "Doctor"), nullable=True)
    programa = Column(String(250), nullable=True)
    titulo_tesis = Column(Text, nullable=True)
    tipo_resolucion = Column(String(120), nullable=True)
    id_paso_inferido = Column(Integer, ForeignKey("cat_pasos_flujo.id_paso"), nullable=True)
    docentes_detectados = Column(JSON, nullable=True)
    texto_preview = Column(Text, nullable=True)
    estado_revision = Column(Enum("Pendiente", "OK", "Observado", "Importado", "Descartado"), default="Pendiente")
    observaciones = Column(Text, nullable=True)
    fecha_extraccion = Column(DateTime, default=datetime.utcnow)

    paso_inferido = relationship("PasoFlujo", foreign_keys=[id_paso_inferido])


class TicketDecision(Base):
    """Auditoría normalizada de decisiones operativas tomadas sobre un ticket."""
    __tablename__ = "ticket_decisiones"

    id_decision = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets_osticket.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="SET NULL"), nullable=True, index=True)
    decision = Column(String(50), nullable=False, index=True)
    nota = Column(Text, nullable=True)
    destino = Column(String(200), nullable=True)
    resolucion_ref_legacy = Column(String(80), nullable=True)
    estado_anterior = Column(String(50), nullable=True)
    estado_nuevo = Column(String(50), nullable=True)
    origen = Column(String(50), nullable=False, default="interfaz")
    id_usuario = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    usuario_nombre = Column(String(150), nullable=True)
    usuario_rol = Column(String(50), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    ticket = relationship("TicketOsticket", back_populates="decisiones_normalizadas")
    expediente = relationship("ExpedienteTesis", foreign_keys=[id_expediente])
    usuario = relationship("UsuarioSistema", foreign_keys=[id_usuario])


class TicketAction(Base):
    """Bitácora técnica y humana de vínculos, notas y acciones locales del ticket."""
    __tablename__ = "ticket_acciones"

    id_accion = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets_osticket.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="SET NULL"), nullable=True, index=True)
    accion = Column(String(100), nullable=False, index=True)
    nota = Column(Text, nullable=True)
    detalle = Column(JSON, nullable=True)
    origen = Column(String(50), nullable=False, default="interfaz")
    id_usuario = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    usuario_nombre = Column(String(150), nullable=True)
    usuario_rol = Column(String(50), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    ticket = relationship("TicketOsticket", back_populates="acciones_normalizadas")
    expediente = relationship("ExpedienteTesis", foreign_keys=[id_expediente])
    usuario = relationship("UsuarioSistema", foreign_keys=[id_usuario])


class IntegrationOutbox(Base):
    """Solicitud local para una integración; E1 no la ejecuta externamente."""
    __tablename__ = "integration_outbox"

    id_outbox = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    target_system = Column(String(80), nullable=False, index=True)
    action_type = Column(String(120), nullable=False, index=True)
    subject_type = Column(String(80), nullable=False)
    subject_uuid = Column(String(36), nullable=False, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets_osticket.ticket_id", ondelete="SET NULL"), nullable=True, index=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="SET NULL"), nullable=True, index=True)
    idempotency_key = Column(String(190), unique=True, nullable=False)
    payload = Column(JSON, nullable=False)
    payload_hash = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="borrador", index=True)
    requested_by = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    requested_role = Column(String(50), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    approved_by = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    approved_role = Column(String(50), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    cancelled_by = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    external_reference = Column(String(255), nullable=True)
    error_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    ticket = relationship("TicketOsticket", foreign_keys=[ticket_id])
    expediente = relationship("ExpedienteTesis", foreign_keys=[id_expediente])
    solicitante = relationship("UsuarioSistema", foreign_keys=[requested_by])
    aprobador = relationship("UsuarioSistema", foreign_keys=[approved_by])
    cancelador = relationship("UsuarioSistema", foreign_keys=[cancelled_by])
    eventos = relationship(
        "IntegrationOutboxEvent",
        back_populates="outbox",
        cascade="all, delete-orphan",
        order_by="IntegrationOutboxEvent.fecha_registro",
    )


class IntegrationOutboxEvent(Base):
    """Auditoría inmutable de cada transición de una solicitud de salida."""
    __tablename__ = "integration_outbox_eventos"

    id_evento = Column(Integer, primary_key=True, autoincrement=True)
    id_outbox = Column(Integer, ForeignKey("integration_outbox.id_outbox", ondelete="CASCADE"), nullable=False, index=True)
    accion = Column(String(80), nullable=False)
    estado_anterior = Column(String(32), nullable=True)
    estado_nuevo = Column(String(32), nullable=False)
    sustento = Column(Text, nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    usuario_nombre = Column(String(150), nullable=True)
    usuario_rol = Column(String(50), nullable=True)
    idempotency_key = Column(String(190), nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    outbox = relationship("IntegrationOutbox", back_populates="eventos")
    usuario = relationship("UsuarioSistema", foreign_keys=[id_usuario])


class TicketResolucion(Base):
    """Relación explícita entre un ticket y una resolución del expediente."""
    __tablename__ = "ticket_resoluciones"
    __table_args__ = (
        UniqueConstraint("ticket_id", "id_resolucion_firma", name="uq_ticket_resolucion_firma"),
        UniqueConstraint("ticket_id", "id_resolucion_documento", name="uq_ticket_resolucion_documento"),
    )

    id_ticket_resolucion = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets_osticket.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="SET NULL"), nullable=True, index=True)
    id_resolucion_firma = Column(Integer, ForeignKey("resoluciones_firmas.id_resolucion", ondelete="SET NULL"), nullable=True)
    id_resolucion_documento = Column(Integer, ForeignKey("resoluciones_documentos.id_documento", ondelete="SET NULL"), nullable=True)
    referencia = Column(String(80), nullable=False)
    estado = Column(String(20), nullable=False, default="propuesta", index=True)
    nota = Column(Text, nullable=True)
    origen = Column(String(50), nullable=False, default="interfaz")
    id_propuesto_por = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    propuesto_por_nombre = Column(String(150), nullable=True)
    propuesto_por_rol = Column(String(50), nullable=True)
    fecha_propuesta = Column(DateTime, default=datetime.utcnow, nullable=False)
    id_resuelto_por = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    resuelto_por_nombre = Column(String(150), nullable=True)
    resuelto_por_rol = Column(String(50), nullable=True)
    fecha_resolucion = Column(DateTime, nullable=True)

    ticket = relationship("TicketOsticket", back_populates="resoluciones_ticket")
    expediente = relationship("ExpedienteTesis", foreign_keys=[id_expediente])
    resolucion_firma = relationship("ResolucionFirma", foreign_keys=[id_resolucion_firma])
    resolucion_documento = relationship("ResolucionDocumento", foreign_keys=[id_resolucion_documento])
    propuesto_por = relationship("UsuarioSistema", foreign_keys=[id_propuesto_por])
    resuelto_por = relationship("UsuarioSistema", foreign_keys=[id_resuelto_por])


class ConciliacionIdentidad(Base):
    """Decisión humana reutilizable para una ambigüedad del catálogo histórico."""
    __tablename__ = "conciliaciones_identidad"
    __table_args__ = (UniqueConstraint("tipo_caso", "referencia", name="uq_conciliacion_identidad_caso"),)

    id_conciliacion = Column(Integer, primary_key=True, autoincrement=True)
    tipo_caso = Column(String(40), nullable=False, index=True)
    referencia = Column(String(80), nullable=False, index=True)
    accion = Column(String(40), nullable=False, default="pendiente", index=True)
    clave_identidad = Column(String(600), nullable=True, index=True)
    nota = Column(Text, nullable=True)
    evidencia = Column(JSON, nullable=True)
    id_resuelto_por = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    resuelto_por_nombre = Column(String(150), nullable=True)
    fecha_resolucion = Column(DateTime, nullable=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    resuelto_por = relationship("UsuarioSistema", foreign_keys=[id_resuelto_por])


class TrayectoriaAcademica(Base):
    """Identidad académica canónica construida desde resoluciones verificadas."""
    __tablename__ = "trayectorias_academicas"

    id_trayectoria = Column(Integer, primary_key=True, autoincrement=True)
    id_persona = Column(Integer, ForeignKey("personas_academicas.id_persona", ondelete="SET NULL"), nullable=True, index=True)
    clave_identidad = Column(String(600), nullable=False, unique=True, index=True)
    nombre_alumno = Column(String(200), nullable=False)
    grado_postula = Column(String(20), nullable=False)
    programa = Column(String(250), nullable=True)
    modalidad = Column(String(40), nullable=True)
    codigo_canonico = Column(String(20), nullable=True)
    titulo_tesis = Column(Text, nullable=True)
    paso_actual_documentado = Column(Integer, nullable=True)
    fecha_ultima_resolucion = Column(DateTime, nullable=True)
    origen = Column(String(40), nullable=False, default="catalogo_drive")
    estado_migracion = Column(String(40), nullable=False, default="documentada")
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PersonaAcademica(Base):
    """Persona canónica que puede tener varias trayectorias independientes.

    La identidad personal no reemplaza ni combina expedientes: Maestría,
    Doctorado y futuros casos CAI siguen siendo trayectorias distintas.
    """
    __tablename__ = "personas_academicas"

    id_persona = Column(Integer, primary_key=True, autoincrement=True)
    clave_persona = Column(String(300), nullable=False, unique=True, index=True)
    nombre_canonico = Column(String(200), nullable=False, index=True)
    dni_canonico = Column(String(8), nullable=True, index=True)
    estado_identidad = Column(String(40), nullable=False, default="nombre_consensuado")
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ExpedienteTrayectoriaHistorica(Base):
    __tablename__ = "expedientes_trayectorias_historicas"
    __table_args__ = (UniqueConstraint("id_expediente", name="uq_expediente_trayectoria_historica"),)

    id_relacion = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="CASCADE"), nullable=False, index=True)
    id_trayectoria = Column(Integer, ForeignKey("trayectorias_academicas.id_trayectoria", ondelete="CASCADE"), nullable=False, index=True)
    estado_asociacion = Column(String(40), nullable=False)
    evidencia = Column(JSON, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)


class DocumentoTrayectoriaHistorica(Base):
    __tablename__ = "documentos_trayectorias_historicas"
    __table_args__ = (UniqueConstraint("id_documento", name="uq_documento_trayectoria_historica"),)

    id_relacion = Column(Integer, primary_key=True, autoincrement=True)
    id_documento = Column(Integer, ForeignKey("resoluciones_documentos.id_documento", ondelete="CASCADE"), nullable=False, index=True)
    id_trayectoria = Column(Integer, ForeignKey("trayectorias_academicas.id_trayectoria", ondelete="CASCADE"), nullable=False, index=True)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)


class RequisitoPasoCatalogo(Base):
    """Catálogo versionado de requisitos derivados del anexo institucional."""
    __tablename__ = "cat_requisitos_paso"
    __table_args__ = (UniqueConstraint("codigo", "version", name="uq_requisito_codigo_version"),)

    id_requisito = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(80), nullable=False, index=True)
    version = Column(String(30), nullable=False, default="2026.1")
    id_paso = Column(Integer, ForeignKey("cat_pasos_flujo.id_paso", ondelete="CASCADE"), nullable=False, index=True)
    grado_postula = Column(String(20), nullable=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo_evidencia = Column(String(80), nullable=True)
    canal_tramite = Column(String(80), nullable=True)
    obligatorio = Column(Boolean, nullable=False, default=True)
    condicion_aplicacion = Column(Text, nullable=True)
    orden = Column(Integer, nullable=False, default=0)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    paso = relationship("PasoFlujo", foreign_keys=[id_paso])
    expediente_requisitos = relationship("ExpedienteRequisito", back_populates="requisito", cascade="save-update, merge")


class ExpedienteRequisito(Base):
    """Instancia verificable de un requisito para un expediente concreto."""
    __tablename__ = "expediente_requisitos"
    __table_args__ = (UniqueConstraint("id_expediente", "id_requisito", name="uq_expediente_requisito"),)

    id_expediente_requisito = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="CASCADE"), nullable=False, index=True)
    id_requisito = Column(Integer, ForeignKey("cat_requisitos_paso.id_requisito", ondelete="RESTRICT"), nullable=False, index=True)
    estado = Column(String(20), nullable=False, default="Pendiente", index=True)
    evidencia_url = Column(String(500), nullable=True)
    evidencia_nombre = Column(String(255), nullable=True)
    fuente_evidencia = Column(String(80), nullable=True)
    id_ticket = Column(Integer, ForeignKey("tickets_osticket.ticket_id", ondelete="SET NULL"), nullable=True)
    id_adjunto = Column(Integer, ForeignKey("ticket_adjuntos.id_adjunto", ondelete="SET NULL"), nullable=True)
    observacion = Column(Text, nullable=True)
    id_validado_por = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    validado_por_nombre = Column(String(150), nullable=True)
    validado_por_rol = Column(String(50), nullable=True)
    fecha_validacion = Column(DateTime, nullable=True)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    expediente = relationship("ExpedienteTesis", back_populates="requisitos")
    requisito = relationship("RequisitoPasoCatalogo", back_populates="expediente_requisitos")
    ticket = relationship("TicketOsticket", foreign_keys=[id_ticket])
    adjunto = relationship("TicketAdjunto", foreign_keys=[id_adjunto])
    validado_por = relationship("UsuarioSistema", foreign_keys=[id_validado_por])
    eventos = relationship(
        "ExpedienteRequisitoEvento",
        back_populates="expediente_requisito",
        cascade="all, delete-orphan",
        order_by="ExpedienteRequisitoEvento.fecha_registro",
    )
    archivos = relationship(
        "ExpedienteRequisitoArchivo",
        back_populates="expediente_requisito",
        cascade="all, delete-orphan",
        order_by="ExpedienteRequisitoArchivo.fecha_asignacion",
    )


class ExpedienteRequisitoArchivo(Base):
    """Archivos múltiples clasificados dentro de una caja de requisito."""
    __tablename__ = "expediente_requisito_archivos"
    __table_args__ = (
        UniqueConstraint(
            "id_expediente_requisito",
            "id_adjunto",
            name="uq_requisito_archivo_adjunto",
        ),
    )

    id_requisito_archivo = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente_requisito = Column(
        Integer,
        ForeignKey("expediente_requisitos.id_expediente_requisito", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_ticket = Column(Integer, ForeignKey("tickets_osticket.ticket_id", ondelete="SET NULL"), nullable=True)
    id_adjunto = Column(Integer, ForeignKey("ticket_adjuntos.id_adjunto", ondelete="SET NULL"), nullable=True)
    archivo_url = Column(String(500), nullable=True)
    archivo_nombre = Column(String(255), nullable=False)
    fuente = Column(String(30), nullable=False, default="ticket")
    estado = Column(String(20), nullable=False, default="Presentado")
    id_asignado_por = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    asignado_por_nombre = Column(String(150), nullable=True)
    asignado_por_rol = Column(String(50), nullable=True)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow, nullable=False)

    expediente_requisito = relationship("ExpedienteRequisito", back_populates="archivos")
    ticket = relationship("TicketOsticket", foreign_keys=[id_ticket])
    adjunto = relationship("TicketAdjunto", foreign_keys=[id_adjunto])
    asignado_por = relationship("UsuarioSistema", foreign_keys=[id_asignado_por])


class ExpedienteRequisitoEvento(Base):
    """Auditoría de cambios de requisito sin depender de logs del servidor."""
    __tablename__ = "expediente_requisito_eventos"

    id_evento = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente_requisito = Column(
        Integer,
        ForeignKey("expediente_requisitos.id_expediente_requisito", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    accion = Column(String(80), nullable=False)
    estado_anterior = Column(String(20), nullable=True)
    estado_nuevo = Column(String(20), nullable=True)
    nota = Column(Text, nullable=True)
    detalle = Column(JSON, nullable=True)
    id_usuario = Column(Integer, ForeignKey("usuarios_sistema.id_usuario", ondelete="SET NULL"), nullable=True)
    usuario_nombre = Column(String(150), nullable=True)
    usuario_rol = Column(String(50), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    expediente_requisito = relationship("ExpedienteRequisito", back_populates="eventos")
    usuario = relationship("UsuarioSistema", foreign_keys=[id_usuario])


class HistorialMovimiento(Base):
    __tablename__ = "historial_movimientos"

    id_movimiento = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="CASCADE"), nullable=False)
    id_paso = Column(Integer, ForeignKey("cat_pasos_flujo.id_paso"), nullable=True)
    accion = Column(
        Enum(
            "Creado",
            "Clasificado",
            "Avanzado",
            "Observado",
            "Desarchivado",
            "Archivado",
            "Derivado",
            "Notificado",
            "Titulo_Actualizado",
            "Resolucion_Cargada",
            "Dictaminantes_Asignados",
        ),
        nullable=False,
    )
    nota = Column(Text, nullable=True)
    usuario_nombre = Column(String(150), nullable=True)
    fecha_movimiento = Column(DateTime, default=datetime.utcnow)

    expediente = relationship("ExpedienteTesis", back_populates="historial")
    paso = relationship("PasoFlujo", foreign_keys=[id_paso])


class RevisionTesis(Base):
    """Control de versiones de documentos de tesis observados."""
    __tablename__ = "revisiones_tesis"

    id_revision = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente = Column(Integer, ForeignKey("expedientes_tesis.id_expediente", ondelete="CASCADE"), nullable=False)
    id_docente = Column(Integer, ForeignKey("docentes.id_docente"), nullable=True)  # Docente que hizo la observación
    version_documento = Column(Integer, nullable=False, default=1)  # V1, V2, V3...
    tipo_revision = Column(
        Enum("Observacion", "Corrección", "Aprobacion"),
        nullable=False,
        default="Observacion"
    )
    descripcion_observacion = Column(Text, nullable=True)
    archivo_observado_url = Column(String(500), nullable=True)   # URL del documento con observaciones
    archivo_corregido_url = Column(String(500), nullable=True)   # URL del documento corregido
    fecha_revision = Column(DateTime, default=datetime.utcnow)
    fecha_correccion = Column(DateTime, nullable=True)            # Cuando el alumno entregó corrección
    estado = Column(
        Enum("Pendiente", "Corregido", "Aceptado"),
        default="Pendiente"
    )

    expediente = relationship("ExpedienteTesis", back_populates="revisiones")
    docente = relationship("Docente", foreign_keys=[id_docente])
