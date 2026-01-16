# UI and Template Enhancements

Este módulo proporciona un conjunto de mejoras visuales, estéticas y de comportamiento en diversas plantillas de Odoo Community Edition, orientadas a una mejor presentación de documentos, interfaces y notificaciones, sin modificar funcionalidades centrales.

## Características principales

- Mejoras en el diseño de informes PDF como presupuestos y facturas.
- Personalización de bloques de dirección y contacto en documentos impresos.
- Visualización opcional de productos complementarios en presupuestos enviados al cliente.
- Ajustes en la disposición de cabeceras, pies de página y mensajes visuales.
- Reducción de elementos redundantes o innecesarios para una presentación más clara y profesional.
- Simplificación del diseño de correos de restablecimiento de contraseña, notificaciones, y portales.

## Objetivo

El propósito de este módulo es **optimizar la experiencia visual** de plantillas predeterminadas sin alterar la lógica empresarial de Odoo. Esto facilita:

- Informes más comprensibles para el cliente final.
- Interfaces de portal y backend más limpias y enfocadas.
- Mayor coherencia visual en procesos de venta, comunicación y acceso.

## Ámbitos de mejora

El módulo incluye ajustes en:

- Reportes PDF (`sale.order`, `account.move`, `hr.expense`)
- Correos y plantillas QWeb (`mail.notification`, `reset_password_email`, etc.)
- Interfaces públicas (login, portal, sidebar)
- Mensajes genéricos de marca, correos y branding visual

## Compatibilidad

- Compatible con Odoo 19.0 Community Edition.
- No requiere dependencias externas.
- Puede coexistir con otros módulos que personalicen informes o correos, siempre que no sobrescriban exactamente las mismas vistas.

## Instalación

1. Copia el módulo dentro de tu carpeta de addons personalizados.
2. Activa el modo desarrollador.
3. Instala el módulo desde la interfaz de Odoo o con:

   ```bash
   odoo-bin -u ui_template_enhancements -d [tu_base_de_datos]
   ```

## Advertencia

Algunas modificaciones incluidas en este módulo podrían sobrescribir vistas QWeb de módulos nativos. Se recomienda revisar conflictos si otros módulos también personalizan plantillas similares.
Licencia

## Licencia

Este módulo se distribuye bajo los términos de la licencia [AGPL-3](https://www.gnu.org/licenses/agpl-3.0.html).
