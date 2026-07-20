from __future__ import annotations
import json, subprocess, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path('/opt/sistema_posgrado'); BASE=ROOT/'data'/'identidades_academicas'; ESTADO=BASE/'estado_reconstruccion_nocturna.json'; ERROR=BASE/'estado_reconstruccion_nocturna_error.json'
def main():
 if not (BASE/'estado_post_drive.json').exists() or ESTADO.exists(): return 0
 try:
  subprocess.run([sys.executable,str(ROOT/'backend'/'reconstruir_trayectorias_identidad.py'),'--aplicar'],cwd=ROOT/'backend',check=True)
  ERROR.unlink(missing_ok=True)
  return 0
 except Exception as exc:
  ERROR.write_text(json.dumps({'fecha':datetime.now(timezone.utc).isoformat(),'error':str(exc),'traceback':traceback.format_exc()},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  raise
if __name__=='__main__': raise SystemExit(main())
