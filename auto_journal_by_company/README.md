# README.md
# Auto Journal by Company

Este módulo asigna automáticamente el diario contable (`account.journal`) en facturas de cliente y proveedor (`account.move`) en función de:

- La empresa (`company_id`)
- El tipo de movimiento (`move_type`): venta o compra

## Funcionalidad

- Soporta facturas creadas manualmente desde la interfaz.
- Soporta facturas creadas desde presupuestos (`sale.order`) y órdenes de compra (`purchase.order`).
- Añade `logging` informativo para trazabilidad.

## Instalación

Coloca este módulo en tu carpeta de addons y ejecuta:

```bash
./odoo-bin -d <base_de_datos> -i auto_journal_by_company
```

## Pruebas

Este módulo incluye pruebas automáticas:

```bash
./odoo-bin -d <base_de_datos_test> -i auto_journal_by_company --test-enable --stop-after-init
```

## Requisitos

- Odoo 17 Community Edition
- Módulo base `account`

## Autor

Antonio Caballero 
