from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# 1. Diccionario de Pasos
class PasoFlujo(Base):
    __tablename__ = "cat_pasos_flujo"
    
    id_paso = Column(Integer, primary_key=True)
    nombre_paso = Column(String(150), nullable=False)
    descripcion = Column(Text)

# 2. Expedientes (El núcleo del alumno)
class ExpedienteTesis(Base):
    __tablename__ = "expedientes_tesis"
    
    id_expediente = Column(Integer, primary_key=True, index=True, autoincrement=True)
    codigo_alumno = Column(String(20), nullable=False, index=True)
    nombre_alumno = Column(String(150), nullable=False)
    grado_postula = Column(Enum('Maestro', 'Doctor'), nullable=False)
    titulo_tesis = Column(Text)
    id_paso_actual = Column(Integer, ForeignKey('cat_pasos_flujo.id_paso'), default=1)
    estado_expediente = Column(Enum('En Proceso', 'Observado', 'Archivado_Graduado', 'Caduco'), default='En Proceso')
    fecha_inicio_tramite = Column(DateTime, default=datetime.utcnow)
    carpeta_drive_url = Column(String(500))

    # Relación para poder consultar el paso fácilmente
    paso_actual = relationship("PasoFlujo")

# 3. Tickets Extraídos (osTicket)
class TicketOsticket(Base):
    __tablename__ = "tickets_osticket"
    
    ticket_id = Column(Integer, primary_key=True, index=True) # ID real de osTicket
    numero_visual = Column(String(20), nullable=False)
    id_expediente = Column(Integer, ForeignKey('expedientes_tesis.id_expediente'), nullable=True)
    asunto = Column(String(255))
    cuerpo = Column(Text)
    estado_scraping = Column(Enum('Nuevo', 'Adjuntos_Descargados', 'Procesado', 'Error'), default='Nuevo')
    fecha_creacion_osticket = Column(DateTime, nullable=False)
    fecha_extraccion = Column(DateTime, default=datetime.utcnow)

# 4. Adjuntos
class TicketAdjunto(Base):
    __tablename__ = "ticket_adjuntos"
    
    id_adjunto = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets_osticket.ticket_id', ondelete="CASCADE"))
    nombre_archivo = Column(String(255), nullable=False)
    ruta_local = Column(String(500), nullable=False)
