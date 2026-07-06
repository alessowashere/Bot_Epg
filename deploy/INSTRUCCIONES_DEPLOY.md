# Instrucciones de Despliegue (Demonios)

Sigue estos pasos en la consola de tu servidor Linux para que nunca más tengas que dejar terminales abiertas.

## 1. Backend (FastAPI) con Systemd

Hemos creado el archivo `fastapi_posgrado.service`. Para instalarlo:

```bash
# 1. Copia el archivo al directorio de servicios de Linux
sudo cp /opt/sistema_posgrado/deploy/fastapi_posgrado.service /etc/systemd/system/

# 2. Recarga los demonios para que Linux reconozca el nuevo archivo
sudo systemctl daemon-reload

# 3. Inicia el backend
sudo systemctl start fastapi_posgrado.service

# 4. Habilita el backend para que arranque solo si el servidor se reinicia
sudo systemctl enable fastapi_posgrado.service
```

## 2. Frontend (Vue) con PM2 (Modo Desarrollo Persistente)

Como estamos en etapa de desarrollo/MVP, la forma más rápida de mantener Vue vivo es usando PM2 de Node.js.

```bash
# 1. Instala PM2 globalmente (si no lo tienes)
sudo npm install -g pm2

# 2. Entra a la carpeta del frontend
cd /opt/sistema_posgrado/frontend

# 3. Inicia el servidor de Vue en segundo plano
pm2 start npm --name "tesistrack-frontend" -- run dev -- --host

# 4. Guarda la lista de procesos para que revivan al reiniciar
pm2 save
pm2 startup
```

¡Con eso listo, ya puedes cerrar la terminal de tu servidor y la web seguirá funcionando 24/7!
