# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools import html2plaintext


class MailTracking(models.Model):
    _inherit = "mail.tracking.value"

    # TODO: Remove if merged https://github.com/odoo/odoo/pull/156236
    property_name = fields.Char(readonly=True)

    # TODO: Remove if merged https://github.com/odoo/odoo/pull/156236
    def _tracking_value_format_model(self, model):
        """Change the value of changedField to show in the chatter
        the name of the property instead of the name of the field.
        """
        res = super()._tracking_value_format_model(model)
        if any(item.property_name for item in self):
            for item in res:
                item["changedField"] = (
                    self.browse(item["id"]).property_name or item["changedField"]
                )
        return res

    @api.model
    def _create_tracking_values(
        self, initial_value, new_value, col_name, col_info, record
    ):
        try:
            return super()._create_tracking_values(
                initial_value, new_value, col_name, col_info, record
            )
        except NotImplementedError:
            if col_info["type"] == "html":
                field = self.env["ir.model.fields"]._get(record._name, col_name)
                values = {"field_id": field.id}
                values.update(
                    {
                        "old_value_char": html2plaintext(initial_value) or "",
                        "new_value_char": html2plaintext(new_value) or "",
                    }
                )
                return values
            elif col_info["type"] == "properties":
                # TODO: Remove if merged https://github.com/odoo/odoo/pull/156236
                # A return is necessary to avoid the NotImplementedError error
                field = self.env["ir.model.fields"]._get(record._name, col_name)
                return {"field_id": field.id}
            raise
