Flujo resultante tras instalar el módulo
=========================================

::

    SO259 (sale_line_id=855)
      └─ MO padre 00056 (sale_line_id=855, pg.sale_id=257)
           │
           │  _prepare_procurement_values() → values["sale_line_id"] = 855
           │  _prepare_mo_vals()            → vals["sale_line_id"] = 855
           │  create()                      → pg(239).sale_id = 257
           │
           └─ MO hija 00057 (sale_line_id=855, pg.sale_id=257) ✓
                └─ Fórmulas encuentran SOL 855 en primera condición
                   production.sale_line_id → correcto
                   cantidades calculadas ✓
