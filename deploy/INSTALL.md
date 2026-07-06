# 🚀 Guía de Instalación y Despliegue — EPG-UAC TesisTrack

> **Servidor objetivo:** Debian 11/12 (Bullseye/Bookworm) — VPS Linux  
> **Ruta base del sistema:** `/opt/sistema_posgrado/`

---

## 1. Estructura de Directorios en el VPS

```
/opt/sistema_posgrado/
├── backend/          ← Código Python (FastAPI, scraper, extractor)
│   ├── .env          ← Variables de entorno (NO en Git)
│   └── auth.json     ← Sesión osTicket (generado en runtime)
├── frontend/
│   └── dist/         ← Build compilado de Vue (generado por npm run build)
├── uploads/
│   └── expedientes/  ← Adjuntos descargados de osTicket
└── venv/             ← Entorno virtual Python
```

---

## 2. Instalación Inicial (una sola vez)

### 2.1 Dependencias del Sistema

```bash
sudo apt update && sudo apt install -y \
    python3.11 python3.11-venv python3-pip \
    nodejs npm \
    nginx \
    mariadb-server \
    chromium-driver  # Para Playwright headless
```

### 2.2 Entorno Virtual Python

```bash
# Crear directorio base
sudo mkdir -p /opt/sistema_posgrado
sudo chown -R www-data:www-data /opt/sistema_posgrado

# Subir/clonar el código
cd /opt/sistema_posgrado
git clone https://github.com/TU_USUARIO/Bot_Epg.git .
# O subir los archivos manualmente via SCP/SFTP

# Crear venv
python3.11 -m venv /opt/sistema_posgrado/venv

# Instalar dependencias Python
/opt/sistema_posgrado/venv/bin/pip install -r backend/requirements.txt

# Instalar Playwright y navegador Chromium
/opt/sistema_posgrado/venv/bin/playwright install chromium
/opt/sistema_posgrado/venv/bin/playwright install-deps chromium
```

### 2.3 Crear el archivo `.env`

```bash
sudo nano /opt/sistema_posgrado/backend/.env
```

Contenido del `.env`:
```env
# Base de datos MariaDB
DB_URL=mysql+pymysql://epg_user:TU_PASSWORD_AQUI@localhost/epg_posgrado

# osTicket (scraper)
OSTICKET_URL_LOGIN=https://mesadepartes.uandina.edu.pe/scp/login.php
OSTICKET_USER=tu_usuario_osticket
OSTICKET_PASSWORD=tu_password_osticket
OSTICKET_AUTH_FILE=/opt/sistema_posgrado/backend/auth.json
OSTICKET_QUEUE_URL=https://mesadepartes.uandina.edu.pe/scp/tickets.php?queue=1

# Almacenamiento de adjuntos
EPG_UPLOADS_DIR=/opt/sistema_posgrado/uploads/expedientes
EPG_UPLOADS_PUBLIC_URL=https://dataepis.uandina.edu.pe/expedientes

# JWT Auth (genera una clave segura: python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=CAMBIA_ESTO_POR_CLAVE_ALEATORIA_SEGURA
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# SMTP para notificaciones
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@uandina.edu.pe
SMTP_PASSWORD=tu_app_password_gmail
```

### 2.4 Base de Datos

```bash
# Crear BD y usuario
sudo mysql -u root -p <<EOF
CREATE DATABASE IF NOT EXISTS epg_posgrado CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'epg_user'@'localhost' IDENTIFIED BY 'TU_PASSWORD_AQUI';
GRANT ALL PRIVILEGES ON epg_posgrado.* TO 'epg_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Importar esquema inicial
mysql -u epg_user -p epg_posgrado < /opt/sistema_posgrado/bd_actualizada.sql
# Aplicar migraciones
mysql -u epg_user -p epg_posgrado < /opt/sistema_posgrado/migracion_fase3.sql
mysql -u epg_user -p epg_posgrado < /opt/sistema_posgrado/backend/migracion_auth.sql
```

---

## 3. Demonización del Backend (Systemd)

```bash
# Copiar el archivo de servicio
sudo cp /opt/sistema_posgrado/deploy/systemd/fastapi_posgrado.service \
        /etc/systemd/system/fastapi_posgrado.service

# Copiar el servicio del bot scraper (ya existente)
sudo cp /opt/sistema_posgrado/deploy/systemd/epg-bot.service \
        /etc/systemd/system/epg-bot.service
sudo cp /opt/sistema_posgrado/deploy/systemd/epg-bot.timer \
        /etc/systemd/system/epg-bot.timer

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar y arrancar el backend FastAPI
sudo systemctl enable fastapi_posgrado.service
sudo systemctl start fastapi_posgrado.service

# Habilitar el timer del bot (se ejecuta cada 15 min)
sudo systemctl enable epg-bot.timer
sudo systemctl start epg-bot.timer

# Verificar estado
sudo systemctl status fastapi_posgrado.service
sudo systemctl status epg-bot.timer
```

---

## 4. Compilar y Desplegar el Frontend (Vue)

```bash
# Instalar dependencias Node
cd /opt/sistema_posgrado/frontend
npm install

# Configurar la URL del backend en producción
# Editar frontend/src/api.js y poner la URL correcta del servidor
# O crear frontend/.env.production:
echo "VITE_API_BASE_URL=https://dataepis.uandina.edu.pe/bot-posgrado/api" \
    > /opt/sistema_posgrado/frontend/.env.production

# Compilar para producción
npm run build
# Esto genera /opt/sistema_posgrado/frontend/dist/
```

---

## 5. Configurar Nginx

```bash
# Copiar configuración
sudo cp /opt/sistema_posgrado/deploy/nginx/epg-posgrado.conf \
        /etc/nginx/sites-available/epg-posgrado

# Activar el sitio
sudo ln -sf /etc/nginx/sites-available/epg-posgrado \
            /etc/nginx/sites-enabled/epg-posgrado

# Eliminar el sitio por defecto (si existe)
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar sintaxis
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

---

## 6. Comandos de Mantenimiento Diario

```bash
# Ver logs del backend en tiempo real
sudo journalctl -fu fastapi_posgrado.service

# Ver logs del bot scraper
sudo journalctl -fu epg-bot.service

# Ver logs de Nginx
sudo tail -f /var/log/nginx/epg-error.log

# Reiniciar backend tras actualizar código
sudo systemctl restart fastapi_posgrado.service

# Forzar ejecución inmediata del bot
sudo systemctl start epg-bot.service

# Ver el estado del timer
sudo systemctl list-timers epg-bot.timer
```

---

## 7. Actualización del Sistema

```bash
# Subir nuevos archivos al servidor (desde tu PC)
scp -r backend/ usuario@servidor:/opt/sistema_posgrado/

# En el servidor: reiniciar servicios
sudo systemctl restart fastapi_posgrado.service

# Si hay cambios en el frontend
cd /opt/sistema_posgrado/frontend
npm run build
sudo systemctl reload nginx
```

---

## 8. Estructura de Permisos de Archivos

```bash
# El usuario www-data debe tener acceso de escritura a uploads y auth.json
sudo chown -R www-data:www-data /opt/sistema_posgrado/uploads/
sudo chown -R www-data:www-data /opt/sistema_posgrado/backend/auth.json
sudo chmod 600 /opt/sistema_posgrado/backend/.env
```
