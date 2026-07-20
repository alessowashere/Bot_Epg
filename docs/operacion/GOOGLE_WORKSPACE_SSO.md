# Acceso con Google Workspace

Fecha: 2026-07-14

Posgrado mantiene sus usuarios y roles locales. Google solo confirma la identidad de una
cuenta institucional; nunca crea personas, asigna roles ni habilita correos que no estén
activos en `usuarios_sistema`.

## URL pública y certificado

Google registra callbacks públicos con esquema `https://`; no se registra una URL
`http://`. El acceso histórico por `http://dataepis.uandina.pe:49267` funciona porque
Nginx responde un `302` inmediato hacia `https://dataepis.uandina.pe:49267`.

El certificado actual corresponde a otro dominio, según `TLS_DATAEPIS.md`. Eso no
impide registrar el callback ni explicar por qué el OAuth histórico funcionaba si el
navegador aceptaba la advertencia, pero sí muestra una advertencia al usuario. Debe
corregirse antes de desplegar el acceso a todo el personal.

## Configuración

1. Entrar con la cuenta institucional administradora a Google Cloud Console, en el mismo
   proyecto que administra las aplicaciones UAndina o en un proyecto nuevo de Posgrado.
2. En **APIs y servicios > Credenciales**, crear un cliente OAuth de tipo **Aplicación web**
   para Posgrado. No reutilizar el secreto de Gestión.
3. Registrar exactamente esta URI de redirección autorizada:

   ```text
   https://dataepis.uandina.pe:49267/bot-posgrado/api/auth/google/callback
   ```

   Si Infraestructura publica Posgrado en otra URL definitiva, usar esa URL exacta tanto
   aquí como en `EPG_PUBLIC_BASE_URL` (sin `/bot-posgrado`).
4. En `/opt/sistema_posgrado/backend/.env`, agregar sin comillas ni espacios:

   ```dotenv
   EPG_GOOGLE_OAUTH_ENABLED=true
   EPG_GOOGLE_CLIENT_ID=<id-del-cliente-de-posgrado>
   EPG_GOOGLE_CLIENT_SECRET=<secreto-del-cliente-de-posgrado>
   EPG_GOOGLE_ALLOWED_DOMAIN=uandina.edu.pe
   EPG_OAUTH_SESSION_SECRET=<salida-de-openssl-rand-hex-48>
   EPG_PUBLIC_BASE_URL=https://dataepis.uandina.pe:49267
   EPG_PUBLIC_API_PREFIX=/bot-posgrado
   ```

   Generar el secreto de sesión con:

   ```bash
   openssl rand -hex 48
   ```

5. Reiniciar y comprobar sin exponer valores:

   ```bash
   sudo systemctl restart fastapi_posgrado.service
   curl -s http://127.0.0.1:8000/api/auth/google/config
   ```

   La respuesta esperada es `{"enabled":true}`.
6. Abrir el sistema en la URL HTTPS pública y seleccionar **Continuar con cuenta UAndina**.
   Probar primero con una cuenta que exista y esté activa en Usuarios. El sistema conserva
   el rol local, una sola sesión por persona y el enlace a dispositivo.

## Límites deliberados

- Solo se admiten correos verificados con dominio alojado `uandina.edu.pe`.
- No se crean cuentas ni roles desde Google.
- El JWT de Posgrado vuelve al navegador en el fragmento `#`, que no se envía a Nginx.
- El estado OAuth y el identificador del navegador viven en una cookie firmada de 10
  minutos, protegida contra CSRF.
- Una cuenta marcada para cambio de contraseña puede usar Google, pues Google sustituye la
  comprobación de esa clave local; el acceso con contraseña continúa sujeto a su política.
