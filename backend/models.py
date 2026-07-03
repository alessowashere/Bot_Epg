from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# 1. Diccionario de Pasos del Flujo
class PasoFlujo(Base):
    __tablename__ = "cat_pasos_flujo"
    
    id_paso = Column(Integer, primary_key=True)
    nombre_paso = Column(String(150), nullable=False)
    descripcion = Column(Text)

# 2. Usuarios del Sistema
class UsuarioSistema(Base):
    __tablename__ = "usuarios_sistema"
    
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre_completo = Column(String(150), nullable=False)
    correo = Column(String(150), unique=True, nullable=False)
    rol = Column(Enum('Administrador', 'Recepcion', 'Directora'), nullable=False)
    activo = Column(Boolean, default=True)

# 3. Docentes (Carga laboral y contratos)
class Docente(Base):
    __tablename__ = "docentes"
    
    id_docente = Column(Integer, primary_key=True, autoincrement=True)
    dni = Column(String(15), unique=True, nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    especialidad = Column(String(150))
    tipo_contrato = Column(Enum('Semestral', 'Indeterminado', 'Tiempo Completo', 'Medio Tiempo'), nullable=False)
    estado = Column(Enum('Activo', 'Inactivo', 'De Licencia'), default='Activo')
    max_tesis_permitidas = Column(Integer, default=5)

    asignaciones = relationship("AsignacionTesis", back_populates="docente")

# 4. Expedientes (El núcleo del alumno)
class ExpedienteTesis(Base):
    __tablename__ = "expedientes_tesis"
    
    id_expediente = Column(Integer, primary_key=True, autoincrement=True)
    codigo_alumno = Column(String(20), nullable=False)
    nombre_alumno = Column(String(150), nullable=False)
    grado_postula = Column(Enum('Maestro', 'Doctor'), nullable=False)
    titulo_tesis = Column(Text)
    id_paso_actual = Column(Integer, ForeignKey('cat_pasos_flujo.id_paso'), default=1)
    estado_expediente = Column(Enum('En Proceso', 'Observado', 'Archivado_Graduado', 'Caduco'), default='En Proceso')
    fecha_inicio_tramite = Column(DateTime, default=datetime.utcnow)
    fecha_ultimo_movimiento = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    carpeta_drive_url = Column(String(500))

    paso_actual = relationship("PasoFlujo", foreign_keys=[id_paso_actual])
    asignaciones = relationship("AsignacionTesis", back_populates="expediente", cascade="all, delete-orphan")
    historial = relationship("HistorialMovimiento", back_populates="expediente", cascade="all, delete-orphan", order_by="HistorialMovimiento.fecha_movimiento")

# 5. Asignaciones Tesis (Relación Muchos a Muchos: expediente ↔ docentes)
class AsignacionTesis(Base):
    __tablename__ = "asignaciones_tesis"
    
    id_asignacion = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente = Column(Integer, ForeignKey('expedientes_tesis.id_expediente', ondelete="CASCADE"))
    id_docente = Column(Integer, ForeignKey('docentes.id_docente', ondelete="CASCADE"))
    rol_asignado = Column(Enum('Asesor', 'Dictaminante', 'Replicante', 'Jurado'), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    estado_asignacion = Column(Enum('Activo', 'Concluido', 'Renuncia'), default='Activo')

    expediente = relationship("ExpedienteTesis", back_populates="asignaciones")
    docente = relationship("Docente", back_populates="asignaciones")

# 6. Tickets Extraídos (osTicket)
class TicketOsticket(Base):
    __tablename__ = "tickets_osticket"
    
    ticket_id = Column(Integer, primary_key=True)
    numero_visual = Column(String(20), nullable=False)
    id_expediente = Column(Integer, ForeignKey('expedientes_tesis.id_expediente', ondelete="CASCADE"), nullable=True)
    asunto = Column(String(255))
    cuerpo = Column(Text)
    estado_scraping = Column(Enum('Nuevo', 'Adjuntos_Descargados', 'Procesado', 'Error'), default='Nuevo')
    fecha_creacion_osticket = Column(DateTime, nullable=False)
    fecha_extraccion = Column(DateTime, default=datetime.utcnow)
    # Datos estructurados extraídos del cuerpo y PDFs (se llena bajo demanda)
    datos_extraidos = Column(JSON, nullable=True)

    adjuntos = relationship("TicketAdjunto", back_populates="ticket", cascade="all, delete-orphan")
    expediente = relationship("ExpedienteTesis", foreign_keys=[id_expediente])

# 7. Adjuntos de Tickets
class TicketAdjunto(Base):
    __tablename__ = "ticket_adjuntos"
    
    id_adjunto = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets_osticket.ticket_id', ondelete="CASCADE"))
    nombre_archivo = Column(String(255), nullable=False)
    ruta_local = Column(String(500), nullable=False)

    ticket = relationship("TicketOsticket", back_populates="adjuntos")

# 8. Resoluciones y Firmas
class ResolucionFirma(Base):
    __tablename__ = "resoluciones_firmas"
    
    id_resolucion = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente = Column(Integer, ForeignKey('expedientes_tesis.id_expediente', ondelete="CASCADE"))
    id_paso_asociado = Column(Integer, ForeignKey('cat_pasos_flujo.id_paso'))
    tipo_documento = Column(String(100))
    archivo_drive_url = Column(String(500))
    estado_firma = Column(Enum('Pendiente_Directora', 'Firmado', 'Rechazado'), default='Pendiente_Directora')
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_firma = Column(DateTime, nullable=True)

# 9. NUEVO: Historial de Movimientos del Expediente
class HistorialMovimiento(Base):
    __tablename__ = "historial_movimientos"
    
    id_movimiento = Column(Integer, primary_key=True, autoincrement=True)
    id_expediente = Column(Integer, ForeignKey('expedientes_tesis.id_expediente', ondelete="CASCADE"), nullable=False)
    id_paso = Column(Integer, ForeignKey('cat_pasos_flujo.id_paso'), nullable=True)
    accion = Column(Enum('Creado', 'Clasificado', 'Avanzado', 'Observado', 'Desarchivado', 'Archivado'), nullable=False)
    nota = Column(Text, nullable=True)
    usuario_nombre = Column(String(150), nullable=True)  # Nombre del usuario que actuó
    fecha_movimiento = Column(DateTime, default=datetime.utcnow)

    expediente = relationship("ExpedienteTesis", back_populates="historial")
    paso = relationship("PasoFlujo", foreign_keys=[id_paso])
