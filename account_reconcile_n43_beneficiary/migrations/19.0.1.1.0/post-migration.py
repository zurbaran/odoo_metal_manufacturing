# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api

from odoo.addons.account_reconcile_n43_beneficiary.hooks import (
    migrate_18_mappings,
    preserve_19_mappings,
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    migrate_18_mappings(env)
    # Do not apply this compatibility mode on a fresh installation.
    preserve_19_mappings(env)
