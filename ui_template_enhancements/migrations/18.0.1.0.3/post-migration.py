from odoo import SUPERUSER_ID, api

PAPERFORMAT_XMLIDS = (
    "ui_template_enhancements.paperformat_ute_sale_external",
    "ui_template_enhancements.paperformat_ute_purchase_external",
    "ui_template_enhancements.paperformat_ute_account_external",
)

VIEW_XMLIDS = ("ui_template_enhancements.ui_external_layout_standard_align_address",)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Localizar los formatos de papel creados por el XML eliminado.
    paperformats = env["report.paperformat"]

    for xmlid in PAPERFORMAT_XMLIDS:
        record = env.ref(xmlid, raise_if_not_found=False)
        if record:
            paperformats |= record

    paperformats = paperformats.exists()

    if paperformats:
        # Desvincular todos los informes antes de eliminar los formatos.
        reports = env["ir.actions.report"].search(
            [("paperformat_id", "in", paperformats.ids)]
        )
        reports.write({"paperformat_id": False})

        paperformats.unlink()

    # Eliminar la vista heredada creada por report_layout_fix.xml.
    for xmlid in VIEW_XMLIDS:
        view = env.ref(xmlid, raise_if_not_found=False)
        if view:
            view.unlink()
