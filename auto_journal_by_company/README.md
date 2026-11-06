# Auto Journal by Company — Odoo 19

Módulo de compatibilidad sin sobrescrituras. Odoo 19 selecciona el diario por
compañía y tipo mediante `account.move._compute_journal_id()` y
`_search_default_journal()`, respetando la selección manual válida.

No es necesario instalarlo en bases nuevas. En bases existentes, actualizarlo
retira la lógica anterior sin eliminar el registro del módulo. Las pruebas
comprueban la selección nativa, incluso con otra compañía y diario explícito.
