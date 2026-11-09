# Validación BOE nativa — 18.0 y 19.0

Fecha: 9 de noviembre de 2026. Estado: **INNECESARIO con las revisiones
actualizadas comprobadas**, para la descarga del asistente BOE compartido.

## Qué se ha probado

Dos bases vacías independientes, sin instalar `web_binary_boe_download_fix`.
En cada versión se instala el modelo 130 real de OCA, se crea una declaración
sintética y su asistente, se abre el formulario real en Chromium, se pulsa
Exportar y se pulsa el enlace real del campo binario de solo lectura.

En ambas versiones: una prueba de extremo a extremo superada, cero fallos,
cero errores y ninguna omisión. Se comprueban POST `/web/content`, HTTP 200,
modelo/ID/campo/nombre enviados, contenido exacto base64 y nombre del archivo
en Content-Disposition. No se falsean las respuestas ni el generador BOE.
El onboarding se desactiva solo en la prueba para que no abra otra pantalla.

El módulo no modifica cálculos de impuestos ni el formato de la declaración;
su única función es sustituir ese POST por una URL GET para el mismo binario.
Los demás modelos que utilizan el mismo asistente comparten el mecanismo de
descarga. No se han validado los cálculos ni las configuraciones de todos los
modelos AEAT ni todas las instalaciones personalizadas.

## Revisiones exactas

| Repositorio | 18.0 | 19.0 |
| --- | --- | --- |
| Odoo CE | `d2ca2c1ca08b4ba6ec2840b2d7446da2f882f628` | `a27a1090b519a01bf308f0c43c5dd4254458a5ae` |
| OCA/l10n-spain | `f2f43cbbed5543a31f2e5090ae7943324d69435a` | `e72a553de7fe680f8fd68eb8dd97efec6aa782db` |
| OCA/account-financial-reporting | `dbfd1f44cb0c69826cb4e5143f76d45f1e3f5098` | `f48b4ea777c444256aa1c215ec3117d604b5feff` |
| OCA/server-ux | `7f9bbfaa1b1e6b758a993bf5e0819eb90e042b89` | `af19073dc86443bad8590811649a54172a81a1ef` |

Entorno: Python 3.12, PostgreSQL 16, navegador Chromium/Brave aislado.
La clasificación no se extiende automáticamente a builds antiguos o con
modificaciones locales. No se ha cambiado tu base de producción.

## Qué se ha encontrado en el historial

Odoo 18 y 19 ya envían modelo, ID, campo y nombre mediante `download` por POST.
La extracción del método `getDownloadData` en el [commit de Odoo 56ffcb0](https://github.com/odoo/odoo/commit/56ffcb01fe8766d5b1d037cb6eff8563dc8f4b06)
no introdujo este transporte: el diff muestra el mismo POST antes del cambio.
Esa corrección trataba los binarios en Ajustes, no una incidencia AEAT.

OCA sí corrigió un problema del asistente: faltaba cargar el campo invisible
`name`, por lo que se mostraba el tamaño en lugar del nombre de archivo.

- [Incidencia OCA #4302](https://github.com/OCA/l10n-spain/issues/4302).
- [Corrección 18.0 del 25 de julio de 2025](https://github.com/OCA/l10n-spain/commit/d72e938094a028d9a1d15b2b2dddffbb51cc7dc9).
- [Corrección equivalente incluida en 19.0](https://github.com/OCA/l10n-spain/commit/53abaa6f4b87cc1e43af964633b08db3b7da5c31).

Esta incidencia del nombre NO demuestra la causa del GET vacío/404 descrito
en el README antiguo del parche. No se dispone del código desplegado y los
registros de aquella instalación para atribuirle una causa exacta. La marca
innecesario se basa en la prueba actual independiente para cada versión,
no en afirmar que ese 404 histórico fuese exactamente la incidencia #4302.
`downloadFile(url)` y `downloadFile._download(url)` son mecanismos GET válidos;
no se califican como errores del parche.

## Reproducción sin activar el parche

El addon de comprobación está en `validation/boe_native_check`. Añadir a los
addons-path las rutas de Odoo, OCA/l10n-spain, OCA/account-financial-reporting,
OCA/server-ux y `web_binary_boe_download_fix/validation` de la versión revisada.
Instalar **solo** el addon de prueba, no el parche. En una base temporal:

```sh
odoo-bin -d boe_native_check -i boe_native_check --test-tags=/boe_native_check --stop-after-init
```

Añadir las opciones de conexión y addons-path de ese entorno. Se necesita un
navegador Chromium/Chrome y `websocket-client`; puede indicarse su ejecutable
con `ODOO_BROWSER_BIN`. Instalar las dependencias Python de Odoo, `unidecode`
y, en OCA 18, la dependencia de pruebas `odoo-test-helper` de `date_range`.
La prueba falla si el parche está instalado o si la descarga no es el POST
nativo con contenido y nombre esperados. No es una prueba de presentación
fiscal ni una validación jurídica de los datos sintéticos.
