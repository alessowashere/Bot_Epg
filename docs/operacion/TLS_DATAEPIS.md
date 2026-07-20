# TLS de dataepis.uandina.pe

Fecha de diagnostico: 2026-07-13.

## Estado comprobado

- La aplicacion responde en `https://dataepis.uandina.pe:49267/`.
- El certificado presentado tiene `CN=akdigital.site` y solo declara
  `DNS:akdigital.site`; por eso el navegador advierte que no corresponde al
  dominio de Posgrado.
- El DNS A publico de `dataepis.uandina.pe` apunta a `38.43.133.79`.
- La comprobacion HTTP en el puerto 80 de ese dominio responde desde Apache,
  no desde el Nginx de este servidor. Por ello un desafio ACME HTTP-01 lanzado
  aqui no puede validarse.
- El certificado actual se encuentra en `/home/bot-whatsapp/certs/` y no es
  administrado por Certbot en este equipo.

## Decision

No sustituir el certificado actual ni ejecutar Certbot en produccion hasta que
la administracion de DNS o del servidor que atiende el puerto 80 autorice un
metodo de validacion. Cambiarlo sin un certificado valido dejaría inaccesible
la URL publica.

## Solucion recomendada

1. Solicitar a Infraestructura UAC una de estas dos habilitaciones:
   - DNS-01 automatizable para `dataepis.uandina.pe` mediante la API del
     proveedor DNS, preferida porque no depende del mapeo de puertos actual.
   - Enrutamiento/proxy del desafio `/.well-known/acme-challenge/` desde el
     Apache publico hacia este servidor, si conservan HTTP-01.
2. Emitir un certificado exclusivo para `dataepis.uandina.pe` con renovacion
   automatica. No reutilizar el certificado de `akdigital.site`.
3. Instalar el certificado y la llave con permisos de lectura solo para root y
   el proceso Nginx, actualizar el virtual host que sirve Posgrado y ejecutar
   `nginx -t` antes de recargar.
4. Confirmar desde una red externa:

```bash
openssl s_client -connect dataepis.uandina.pe:49267 \
  -servername dataepis.uandina.pe </dev/null 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

El resultado debe incluir `DNS:dataepis.uandina.pe`, una cadena valida y una
fecha de renovacion conocida.

## No hacer

- No desactivar la verificacion TLS en el navegador o en el frontend como
  solucion permanente.
- No solicitar un certificado manual sin plan de renovacion.
- No publicar llaves privadas ni rutas de secretos en repositorios, logs o
  capturas.
