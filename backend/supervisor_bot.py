import logging
import os
import re
import signal
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from estado_bot import guardar_estado_bot, leer_estado_bot


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupervisorBot")


def _resumen_salida(resultado: subprocess.CompletedProcess) -> str:
    # El renovador de sesion escribe el motivo funcional en stdout y Python deja
    # el traceback en stderr. Conservar ambos evita ocultar la causa real.
    texto = "\n".join(parte for parte in (resultado.stdout, resultado.stderr) if parte).strip()
    return texto[-2000:]


def _ejecutar(comando: list[str], backend_dir: Path, env: dict, timeout: int):
    inicio = datetime.utcnow()
    proceso = subprocess.Popen(
        comando,
        cwd=str(backend_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        salida, errores = proceso.communicate(timeout=timeout)
        resultado = subprocess.CompletedProcess(
            comando,
            proceso.returncode,
            stdout=salida,
            stderr=errores,
        )
        return resultado, (datetime.utcnow() - inicio).total_seconds(), False
    except subprocess.TimeoutExpired as exc:
        # Playwright abre Node y Chromium; matar sólo Python deja procesos
        # huérfanos consumiendo memoria después del timeout.
        try:
            os.killpg(proceso.pid, signal.SIGTERM)
            proceso.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(proceso.pid, signal.SIGKILL)
            proceso.wait()
        except ProcessLookupError:
            pass
        resultado = subprocess.CompletedProcess(
            comando,
            124,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=f"Tiempo limite excedido ({timeout}s). {exc.stderr or ''}",
        )
        return resultado, (datetime.utcnow() - inicio).total_seconds(), True


def _metricas_backfill(salida: str) -> dict:
    patrones = {
        "revisados": r"Progreso:\s*(\d+)/(\d+)",
        "procesados": r"Procesados:\s*(\d+)",
        "vinculados": r"Vinculados a expediente existente:\s*(\d+)",
        "extracciones": r"Extracciones ejecutadas:\s*(\d+)",
        "pendientes_humanos": r"Pendientes de revision humana:\s*(\d+)",
        "errores": r"Errores:\s*(\d+)",
    }
    metricas = {}
    for clave, patron in patrones.items():
        coincidencias = re.findall(patron, salida or "")
        if not coincidencias:
            continue
        valor = coincidencias[-1]
        metricas[clave] = int(valor[-1] if isinstance(valor, tuple) else valor)
    return metricas


def _finalizar_estado(estado: dict, inicio: datetime, resultado: str, error: str | None = None):
    fin = datetime.utcnow()
    intervalo = int(os.getenv("EPG_BOT_INTERVAL_MINUTES", "15"))
    estado.update(
        {
            "estado": resultado,
            "ultima_corrida": fin.isoformat(),
            "duracion_segundos": round((fin - inicio).total_seconds(), 2),
            "proxima_corrida_estimada": (fin + timedelta(minutes=intervalo)).isoformat(),
        }
    )
    if error:
        errores = list(estado.get("errores_recientes") or [])
        errores.append({"fecha": fin.isoformat(), "mensaje": error[-1200:]})
        estado["errores_recientes"] = errores[-5:]
    guardar_estado_bot(estado)


def ejecutar_ciclo():
    logger.info("Iniciando ciclo de scraping/backfill liviano...")
    try:
        os.nice(int(os.getenv("EPG_BOT_NICE", "10")))
    except Exception:
        pass
    backend_dir = Path(__file__).resolve().parent
    import sys
    env = os.environ.copy()
    env.setdefault("OSTICKET_MAX_DEEP_CRAWL", "30")
    env.setdefault("EPG_EXTRACT_MAX_PAGES", "6")
    inicio = datetime.utcnow()
    estado_anterior = leer_estado_bot()
    estado = {
        "estado": "ejecutando",
        "inicio_corrida": inicio.isoformat(),
        "ultima_corrida": estado_anterior.get("ultima_corrida"),
        "proxima_corrida_estimada": None,
        "duracion_segundos": None,
        "errores_recientes": estado_anterior.get("errores_recientes", []),
        "limites": {
            "deep_crawl": int(env["OSTICKET_MAX_DEEP_CRAWL"]),
            "workers_backfill": int(os.getenv("EPG_BACKFILL_WORKERS", "2")),
            "max_tickets_backfill": int(os.getenv("EPG_BACKFILL_MAX_TICKETS", "120")),
            "paginas_por_adjunto": int(env["EPG_EXTRACT_MAX_PAGES"]),
            "cpu_quota": os.getenv("EPG_BOT_CPU_QUOTA", "35%"),
        },
        "fases": {
            "sincronizacion": {"estado": "ejecutando"},
            "backfill": {"estado": "pendiente"},
        },
    }
    guardar_estado_bot(estado)

    sync, duracion_sync, timeout_sync = _ejecutar(
        [sys.executable, "sincronizador.py"],
        backend_dir,
        env,
        timeout=int(os.getenv("EPG_SYNC_TIMEOUT_SECONDS", "300")),
    )
    estado["fases"]["sincronizacion"] = {
        "estado": "ok" if sync.returncode == 0 else "error",
        "duracion_segundos": round(duracion_sync, 2),
        "timeout": timeout_sync,
        "codigo_salida": sync.returncode,
    }

    if sync.returncode == 0:
        logger.info("Sincronizacion exitosa.")
    else:
        error = _resumen_salida(sync)
        logger.error("Error en sincronizacion: %s", error)
        estado["fases"]["sincronizacion"]["error"] = error
        estado["fases"]["backfill"] = {"estado": "omitido"}
        _finalizar_estado(estado, inicio, "error", error)
        return sync.returncode

    estado["fases"]["backfill"] = {"estado": "ejecutando"}
    guardar_estado_bot(estado)
    backfill, duracion_backfill, timeout_backfill = _ejecutar(
        [
            sys.executable,
            "backfill_tickets.py",
            "--workers",
            os.getenv("EPG_BACKFILL_WORKERS", "2"),
            "--solo-pendientes",
            "--con-adjuntos",
            "--max-tickets",
            os.getenv("EPG_BACKFILL_MAX_TICKETS", "40"),
            "--aplicar",
        ],
        backend_dir,
        env,
        timeout=int(os.getenv("EPG_BACKFILL_TIMEOUT_SECONDS", "450")),
    )
    estado["fases"]["backfill"] = {
        "estado": "ok" if backfill.returncode == 0 else "error",
        "duracion_segundos": round(duracion_backfill, 2),
        "timeout": timeout_backfill,
        "codigo_salida": backfill.returncode,
        "metricas": _metricas_backfill(backfill.stdout or ""),
    }
    if backfill.returncode == 0:
        logger.info("Backfill liviano exitoso.")
        _finalizar_estado(estado, inicio, "ok")
    else:
        error = _resumen_salida(backfill)
        logger.error("Error en backfill liviano: %s", error)
        estado["fases"]["backfill"]["error"] = error
        _finalizar_estado(estado, inicio, "error", error)
    return backfill.returncode


if __name__ == "__main__":
    raise SystemExit(ejecutar_ciclo())
