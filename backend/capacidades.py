"""Matriz central de capacidades para rutas mutables de la API EPG-UAC."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


METODOS_MUTABLES = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@dataclass(frozen=True)
class PoliticaCapacidad:
    nombre: str
    roles: frozenset[str] = frozenset()
    publico: bool = False


def politica(nombre: str, *roles: str, publico: bool = False) -> PoliticaCapacidad:
    return PoliticaCapacidad(nombre=nombre, roles=frozenset(roles), publico=publico)


# La clave es (método HTTP, path declarado por FastAPI), no la URL concreta.
# Esta lista es deliberadamente exhaustiva: añadir una mutación sin política hace
# fallar el arranque y las pruebas de inventario.
POLITICAS_MUTABLES: dict[tuple[str, str], PoliticaCapacidad] = {
    ("POST", "/api/auth/login"): politica("auth.iniciar_sesion", publico=True),
    ("POST", "/api/auth/vista-rol"): politica("auth.vista_rol", "Administrador"),
    ("POST", "/api/auth/logout"): politica(
        "auth.cerrar_sesion", "Administrador", "Recepcion", "Secretaria_Academica", "Directora", "Dictaminante"
    ),
    ("POST", "/api/auth/cerrar-otras-sesiones"): politica(
        "auth.cerrar_otras_sesiones", "Administrador", "Recepcion", "Secretaria_Academica", "Directora", "Dictaminante"
    ),
    ("PUT", "/api/auth/cambiar-password"): politica(
        "usuario.contrasena.cambiar", "Administrador", "Recepcion", "Secretaria_Academica", "Directora", "Dictaminante"
    ),
    ("POST", "/api/usuarios"): politica("usuario.administrar", "Administrador"),
    ("PUT", "/api/usuarios/{id_usuario}"): politica("usuario.administrar", "Administrador"),
    ("DELETE", "/api/usuarios/{id_usuario}"): politica("usuario.administrar", "Administrador"),
    ("PUT", "/api/usuarios/{id_usuario}/cambiar-password"): politica(
        "usuario.contrasena.cambiar", "Administrador", "Recepcion", "Secretaria_Academica", "Directora", "Dictaminante"
    ),
    ("PUT", "/api/reglas-resolucion/{id_paso}"): politica(
        "resolucion.reglas.validar", "Administrador"
    ),
    ("POST", "/api/tickets/{ticket_ref}/decision"): politica(
        "ticket.decision.proponer", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/resoluciones/proponer"): politica(
        "ticket.resolucion.proponer", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/resoluciones/{id_relacion}/confirmar"): politica(
        "ticket.resolucion.confirmar", "Administrador", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/resoluciones/{id_relacion}/descartar"): politica(
        "ticket.resolucion.confirmar", "Administrador", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/vincular-expediente"): politica(
        "ticket.vincular", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/crear-expediente-inicial"): politica(
        "expediente.inicial.crear", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/enviar-secretaria"): politica(
        "resolucion.tramite.derivar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/preparar-derivacion"): politica(
        "resolucion.tramite.derivar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/desvincular-expediente"): politica(
        "ticket.vincular", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/extraer-datos"): politica(
        "ticket.extraer", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/clasificar"): politica(
        "ticket.clasificar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/cambiar-estado"): politica(
        "ticket.estado.cambiar", "Administrador", "Directora"
    ),
    ("POST", "/api/tickets/{ticket_ref}/responder-osticket"): politica(
        "ticket.salida.solicitar", "Administrador", "Recepcion", "Directora"
    ),
    ("PUT", "/api/resoluciones/{id_documento}"): politica(
        "resolucion.revisar", "Administrador", "Directora"
    ),
    ("POST", "/api/resoluciones/{id_resolucion}/aprobar"): politica(
        "resolucion.firma.aprobar", "Administrador", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/requisitos/inicializar"): politica(
        "expediente.requisito.inicializar", "Administrador", "Secretaria_Academica"
    ),
    ("PUT", "/api/expedientes/{expediente_ref}/requisitos/{id_expediente_requisito}"): politica(
        "expediente.requisito.presentar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/requisitos/{id_expediente_requisito}/archivos/asignar"): politica(
        "expediente.requisito.presentar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/requisitos/{id_expediente_requisito}/archivos/subir"): politica(
        "expediente.requisito.presentar", "Administrador", "Recepcion", "Directora"
    ),
    ("DELETE", "/api/expedientes/{expediente_ref}/requisitos/{id_expediente_requisito}/archivos/{id_requisito_archivo}"): politica(
        "expediente.requisito.presentar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/avanzar"): politica(
        "expediente.avanzar", "Administrador", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/observar"): politica(
        "expediente.observar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/derivar-directora"): politica(
        "expediente.derivar", "Administrador", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/cargar-resolucion-directa"): politica(
        "expediente.resolucion.cargar", "Administrador", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/cambiar-titulo"): politica(
        "expediente.titulo.editar", "Administrador", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/asignar-dictaminantes"): politica(
        "expediente.dictaminante.asignar", "Administrador", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/notificar"): politica(
        "ticket.salida.solicitar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/revisiones"): politica(
        "revision.crear", "Administrador", "Directora", "Dictaminante"
    ),
    ("PUT", "/api/revisiones/{id_revision}/corregido"): politica(
        "revision.corregir", "Administrador", "Recepcion", "Directora"
    ),
    ("PUT", "/api/revisiones/{id_revision}/aceptado"): politica(
        "revision.aceptar", "Administrador", "Directora", "Dictaminante"
    ),
    ("POST", "/api/dictaminantes/aceptaciones/{id_aceptacion}/responder"): politica(
        "dictaminante.responder", "Administrador", "Directora", "Dictaminante"
    ),
    ("POST", "/api/dictaminante/{uuid}/responder"): politica(
        "dictaminante.enlace_publico.responder", publico=True
    ),
    ("POST", "/api/docentes"): politica("docente.administrar", "Administrador"),
    ("PUT", "/api/docentes/{id_docente}"): politica("docente.administrar", "Administrador"),
    ("POST", "/api/admin/importar-excel"): politica("admin.importar", "Administrador"),
    ("POST", "/api/admin/sync-historico"): politica("admin.sync_historico", "Administrador"),
    ("POST", "/api/admin/conciliacion-identidades/{tipo}/{referencia}"): politica("admin.conciliar_identidades", "Administrador"),
    ("POST", "/api/integraciones/outbox"): politica(
        "ticket.salida.solicitar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/integraciones/outbox/{outbox_uuid}/aprobar"): politica(
        "ticket.salida.aprobar", "Administrador", "Directora"
    ),
    ("POST", "/api/integraciones/outbox/{outbox_uuid}/cancelar"): politica(
        "ticket.salida.cancelar", "Administrador", "Recepcion", "Directora"
    ),
    ("POST", "/api/expedientes/{expediente_ref}/resolucion-tramites"): politica(
        "resolucion.tramite.derivar", "Administrador", "Recepcion"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/revisar"): politica(
        "resolucion.tramite.revisar", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/preparar"): politica(
        "resolucion.tramite.preparar", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/descartar-borrador"): politica(
        "resolucion.tramite.preparar", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/generar-borrador"): politica(
        "resolucion.borrador.generar", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/generar-borrador-oficial"): politica(
        "resolucion.borrador.generar", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/resolucion-tramites/generar-borradores-lote"): politica(
        "resolucion.borrador.generar", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/consultas"): politica(
        "resolucion.consulta.crear", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/resolucion-consulta-plantillas"): politica(
        "resolucion.consulta.plantilla", "Administrador", "Secretaria_Academica"
    ),
    ("PUT", "/api/resolucion-consulta-plantillas/{id_plantilla}"): politica(
        "resolucion.consulta.plantilla", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/consultas-resolucion/{token}/responder"): politica(
        "resolucion.consulta.publica.responder", publico=True
    ),
    ("POST", "/api/consultas-resolucion/{token}/responder-con-evidencia"): politica(
        "resolucion.consulta.publica.responder", publico=True
    ),
    ("POST", "/api/onlyoffice/callback/{tramite_ref}"): politica(
        "resolucion.borrador.onlyoffice.callback", publico=True
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/remitir-direccion"): politica(
        "resolucion.tramite.remitir", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/resolucion-tramites/remitir-direccion-lote"): politica(
        "resolucion.tramite.remitir", "Administrador", "Secretaria_Academica"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/observar-direccion"): politica(
        "resolucion.tramite.observar_direccion", "Administrador", "Directora"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/firmar"): politica(
        "resolucion.tramite.firmar", "Administrador", "Directora"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/notificaciones"): politica(
        "resolucion.notificacion.registrar", "Administrador", "Recepcion"
    ),
    ("POST", "/api/resolucion-tramites/{tramite_ref}/notificaciones/{id_notificacion}/confirmar"): politica(
        "resolucion.notificacion.confirmar", "Administrador", "Recepcion"
    ),
}


def obtener_politica(path: str, methods: Iterable[str]) -> PoliticaCapacidad | None:
    for method in methods:
        politica_encontrada = POLITICAS_MUTABLES.get((method.upper(), path))
        if politica_encontrada:
            return politica_encontrada
    return None


def rutas_mutables_sin_politica(routes: Iterable[object]) -> list[str]:
    faltantes = []
    for route in routes:
        path = getattr(route, "path", None)
        methods = set(getattr(route, "methods", set()) or set())
        mutables = methods & METODOS_MUTABLES
        if path and mutables and not obtener_politica(path, mutables):
            faltantes.append(f"{','.join(sorted(mutables))} {path}")
    return sorted(faltantes)
