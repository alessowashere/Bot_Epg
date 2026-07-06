from datetime import datetime
import uuid as uuid_lib

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from database import Base


def nuevo_uuid():
    return str(uuid_lib.uuid4())


class PasoFlujo(Base):
    __tablename__ = "cat_pasos_flujo"

    id_paso = Column(Integer, primary_key=True)
    nombre_paso = Column(String(150), nullable=False)
    descripcion = Column(Text)


class UsuarioSistema(Base):
    __tablename__ = "usuarios_sistema"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre_completo = Column(String(150), nullable=False)
    correo = Column(String(150), unique=True, nullable=False)
    rol = Column(Enum("Administrador", "Recepcion", "Directora", "Dictaminante"), nullable=False)
    activo = Column(Boolean, default=True)


class Docente(Base):
    __tablename__ = "docentes"

    id_docente = Column(Integer, primary_key=True, autoincrement=True)
    dni = Column(String(15), unique=True, nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    correo = Column(String(150), nullable=True)
    especialidad = Column(String(150))
    tipo_contrato = Column(Enum("Semestral", "Indeterminado", "Tiempo Completo", "Medio Tiempo"), nullable=False)
    estado = Column(Enum("Activo", "Inactivo", "De Licencia"), default="Activo")
    max_tesis_permitidas = Column(Integer, default=5)

    asignaciones = relationship("AsignacionTesis", back_populates="docente")


class ExpedienteTesis(Base):
    __tablename__ = "expedientes_tesis"

    id_expediente = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=nuevo_uuid, index=True)
    codigo_alumno = Column(String(20), nullable=False)
    nombre_alumno = Column(String(150), nullable=False)
    grado_postula = Column(Enum("Maestro", "Doctor"), nullable=False)
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

    adjuntos = relationship("TicketAdjunto", back_populates="ticket", cascade="all, delete-orphan")
    expediente = relationship("ExpedienteTesis", foreign_keys=[id_expediente])


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
