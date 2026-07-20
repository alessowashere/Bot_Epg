"""Relee tickets y adjuntos locales para renovar evidencia de identidad.

No vincula expedientes ni cambia el estado operativo: sólo actualiza la
extracción estructurada para que el planificador posterior decida con evidencia
actualizada.
"""
from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from database import SessionLocal
from extractor import extraer_datos_cuerpo, extraer_todos_adjuntos, generar_resumen_ticket
from identidad_academica import normalizar_codigo_matricula
import models

ROOT = Path('/opt/sistema_posgrado')
REPORTE = ROOT / 'data' / 'tickets' / 'relectura_identidad_tickets.csv'
ESTADO_RELECTURA = ROOT / 'data' / 'tickets' / 'estado_relectura_adjuntos.json'
MARCA_RELECTURA = 'adjuntos_profundo_20260720_v2'


def leer(ticket: dict) -> dict:
    adjuntos = ticket['adjuntos']
    resultado = extraer_todos_adjuntos(adjuntos)
    cuerpo = extraer_datos_cuerpo(ticket['cuerpo'])
    estructurados = {**resultado['datos_extraidos_pdfs'], **cuerpo}
    resumen = generar_resumen_ticket(ticket['asunto'], ticket['cuerpo'], resultado['texto_combinado'])
    return {
        'ticket_id': ticket['ticket_id'], 'estructurados': estructurados, 'resumen': resumen,
        'archivos_procesados': resultado['archivos_procesados'], 'detalle': resultado['detalle_archivos'],
    }


def _guardar_progreso(**datos) -> None:
    ESTADO_RELECTURA.parent.mkdir(parents=True, exist_ok=True)
    ESTADO_RELECTURA.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _guardar_reporte(reporte: list[dict]) -> None:
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    with REPORTE.open('w', newline='', encoding='utf-8') as archivo:
        writer = csv.DictWriter(
            archivo,
            fieldnames=['ticket_id', 'grado_antes', 'grado_despues', 'titulo_detectado', 'archivos_leidos', 'estado', 'detalle'],
        )
        writer.writeheader()
        writer.writerows(reporte)


def ejecutar(aplicar: bool, lote: int, forzar: bool = False, workers: int = 1) -> dict:
    db = SessionLocal()
    try:
        todos = db.query(models.TicketOsticket).order_by(models.TicketOsticket.ticket_id).all()
        pendientes = [
            ticket for ticket in todos
            if forzar or (ticket.datos_extraidos or {}).get('origen_relectura') != MARCA_RELECTURA
        ]
        tickets = pendientes if lote <= 0 else pendientes[:lote]
        cargas = [
            {
                'ticket_id': ticket.ticket_id,
                'asunto': ticket.asunto or '',
                'cuerpo': ticket.cuerpo or '',
                'adjuntos': [{'nombre_archivo': a.nombre_archivo, 'ruta_local': a.ruta_local} for a in ticket.adjuntos],
            }
            for ticket in tickets
        ]
        reporte = []
        fallos = {}
        total = len(tickets)
        tamanio_lote = 24
        _guardar_progreso(estado='ejecutando', total=total, procesados=0, errores=0, inicio=datetime.utcnow().isoformat())
        # Guardar cada lote evita acumular PDFs, OCR y textos de 1,470 tickets
        # en memoria. Si un adjunto falla, el resto del avance queda persistido.
        for inicio_lote in range(0, total, tamanio_lote):
            cargas_lote = cargas[inicio_lote:inicio_lote + tamanio_lote]
            lecturas, fallos = {}, {}
            with ThreadPoolExecutor(max_workers=max(1, min(workers, 2))) as executor:
                futuros = {executor.submit(leer, carga): carga['ticket_id'] for carga in cargas_lote}
                for futuro in as_completed(futuros):
                    ticket_id = futuros[futuro]
                    try:
                        lecturas[ticket_id] = futuro.result()
                    except Exception as exc:
                        fallos[ticket_id] = str(exc)

            for ticket in tickets[inicio_lote:inicio_lote + tamanio_lote]:
                lectura = lecturas.get(ticket.ticket_id)
                if not lectura:
                    reporte.append({'ticket_id': ticket.ticket_id, 'grado_antes': '', 'grado_despues': '', 'titulo_detectado': '', 'archivos_leidos': 0, 'estado': 'error', 'detalle': fallos.get(ticket.ticket_id, 'Error de lectura no especificado')[:300]})
                    continue
                ticket_id = ticket.ticket_id
                previo = dict(ticket.datos_extraidos or {})
                claves_operativas = {k: previo[k] for k in ('decisiones','decision_actual','mensajes_locales','acciones_locales','resolucion_ticket_confirmada','vinculacion') if k in previo}
                antes = ((previo.get('resumen') or {}).get('grado_detectado') or '')
                despues = lectura['resumen'].get('grado_detectado') or ''
                titulo = (lectura['estructurados'].get('caratula') or {}).get('titulo_tesis') or lectura['estructurados'].get('titulo_tesis') or ''
                reporte.append({'ticket_id': ticket_id, 'grado_antes': antes, 'grado_despues': despues, 'titulo_detectado': titulo[:180], 'archivos_leidos': lectura['archivos_procesados'], 'estado': 'ok', 'detalle': ''})
                if aplicar:
                    ticket.datos_extraidos = {
                        **claves_operativas, 'datos_estructurados': lectura['estructurados'], 'resumen': lectura['resumen'],
                        'archivos_procesados': lectura['archivos_procesados'],
                        'detalle_archivos': [{'nombre': d['nombre'], 'paginas': d.get('paginas', 0), 'datos': d.get('datos', {}), 'texto_preview': d.get('texto_preview', ''), 'error': d.get('error')} for d in lectura['detalle']],
                        'fecha_extraccion': datetime.utcnow().isoformat(), 'origen_relectura': MARCA_RELECTURA,
                    }
                    ticket.fecha_extraccion = datetime.utcnow()
                    # Una lectura integral satisfactoria reemplaza estados técnicos
                    # antiguos; de otro modo la UI sigue mostrando errores ya resueltos.
                    ticket.estado_scraping = "Datos_Extraidos"
                    codigo = normalizar_codigo_matricula(lectura['estructurados'].get('codigo_alumno') or lectura['resumen'].get('datos_alumno', {}).get('codigo'))
                    if not ticket.codigo_alumno_osticket and codigo:
                        ticket.codigo_alumno_osticket = codigo
            if aplicar:
                db.commit()
            _guardar_reporte(reporte)
            _guardar_progreso(
                estado='ejecutando', total=total, procesados=min(inicio_lote + tamanio_lote, total),
                errores=sum(1 for item in reporte if item['estado'] == 'error'),
                inicio=datetime.utcnow().isoformat(),
            )
        _guardar_progreso(estado='completado', total=total, procesados=total, errores=sum(1 for item in reporte if item['estado'] == 'error'), fin=datetime.utcnow().isoformat())
        return {'modo': 'aplicar' if aplicar else 'simulacion', 'marca_relectura': MARCA_RELECTURA, 'tickets_releidos': sum(1 for item in reporte if item['estado'] == 'ok'), 'errores': sum(1 for item in reporte if item['estado'] == 'error'), 'pendientes_restantes': max(0, len(pendientes) - len(tickets)), 'con_adjuntos_leidos': sum(1 for x in reporte if x['estado'] == 'ok' and x['archivos_leidos']), 'grados_actualizados': sum(1 for x in reporte if x['estado'] == 'ok' and x['grado_antes'] != x['grado_despues']), 'reporte': str(REPORTE)}
    except Exception:
        db.rollback(); raise
    finally: db.close()


if __name__ == '__main__':
    p=argparse.ArgumentParser(description='Relectura local de cuerpo y adjuntos de tickets sin decidir ni vincular casos.')
    p.add_argument('--aplicar', action='store_true')
    p.add_argument('--lote', type=int, default=25, help='0 procesa todos los tickets seleccionados.')
    p.add_argument('--forzar', action='store_true', help='Relee también tickets ya procesados por esta versión.')
    p.add_argument('--workers', type=int, default=1, help='Máximo 2 lectores locales para proteger el servidor.')
    args = p.parse_args()
    print(json.dumps(ejecutar(args.aplicar, args.lote, args.forzar, args.workers), ensure_ascii=False, indent=2))
