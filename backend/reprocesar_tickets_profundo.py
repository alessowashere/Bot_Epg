"""Relectura integral local de tickets antes de recalcular sus colas.

No consulta ni modifica osTicket. Relee cuerpo y adjuntos ya descargados,
regenera el plan documental, materializa trayectorias existentes y actualiza
sólo la clasificación local. Las decisiones humanas y los vínculos actuales se
preservan durante toda la operación.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from clasificar_cola_tickets import clasificar
from migrar_trayectorias_academicas import ejecutar as materializar_trayectorias
from materializar_personas_academicas import ejecutar as materializar_personas
from releer_tickets_identidad import ejecutar as releer_tickets
from reconstruir_trayectorias_identidad import main as reconstruir_plan


ESTADO = Path("/opt/sistema_posgrado/data/tickets/estado_reproceso_profundo.json")


def guardar_estado(**datos) -> None:
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    inicio = datetime.now(timezone.utc)
    guardar_estado(estado="ejecutando", inicio=inicio.isoformat(), etapa="relectura_adjuntos")
    try:
        # La marca de versión hace que una reanudación continúe donde quedó;
        # no repite los lotes ya persistidos después de una interrupción.
        relectura = releer_tickets(aplicar=True, lote=0, forzar=False, workers=2)
        guardar_estado(estado="ejecutando", inicio=inicio.isoformat(), etapa="reconstruccion_plan", relectura=relectura)
        reconstruir_plan()
        guardar_estado(estado="ejecutando", inicio=inicio.isoformat(), etapa="materializacion_trayectorias", relectura=relectura)
        trayectorias = materializar_trayectorias(aplicar=True)
        guardar_estado(estado="ejecutando", inicio=inicio.isoformat(), etapa="personas_academicas", relectura=relectura, trayectorias=trayectorias)
        personas = materializar_personas(aplicar=True)
        guardar_estado(estado="ejecutando", inicio=inicio.isoformat(), etapa="clasificacion_operativa", relectura=relectura, trayectorias=trayectorias, personas=personas)
        clasificacion = clasificar(aplicar=True)
        guardar_estado(
            estado="completado", inicio=inicio.isoformat(), fin=datetime.now(timezone.utc).isoformat(),
            relectura=relectura, trayectorias=trayectorias, personas=personas, clasificacion=clasificacion,
        )
        print(json.dumps({"estado": "completado", "relectura": relectura, "trayectorias": trayectorias, "personas": personas, "clasificacion": clasificacion}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        guardar_estado(estado="error", inicio=inicio.isoformat(), fin=datetime.now(timezone.utc).isoformat(), error=str(exc))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
