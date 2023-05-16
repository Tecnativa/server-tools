# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class TierReview(models.Model):
    _inherit = "tier.review"

    summary = fields.Char(string="Summary")
    changeset_id = fields.Many2one(comodel_name="record.changeset")

    def _tier_process(self, status):
        """Custom process to accept/reject, similar to _validate_tier()
        and _rejected_tier()."""
        self.ensure_one()
        self.write(
            {
                "status": status,
                "done_by": self.env.user.id,
                "reviewed_date": fields.Datetime.now(),
            }
        )
        rec = self.env[self.model].browse(self.res_id)
        if status == "approved":
            rec._notify_accepted_reviews()
        else:
            rec._notify_rejected_review()

    @api.model_create_multi
    def create(self, vals_list):
        """Set summary in reviews."""
        result = super().create(vals_list)
        for item in result:
            item.summary = item._get_summary()
        return result

    def _get_field_value_display_from_record(self, field, field_value, record):
        if not field_value:
            return ""
        if field.ttype == "monetary":
            pre = post = ""
            currency = record.currency_id
            if currency.position == "before":
                pre = "{symbol}\N{NO-BREAK SPACE}".format(symbol=currency.symbol or "")
            else:
                post = "\N{NO-BREAK SPACE}{symbol}".format(symbol=currency.symbol or "")
            value = " {pre}{0}{post}".format(field_value, pre=pre, post=post)
        elif field.ttype == "many2one":
            value = field_value.display_name
        elif field.ttype == "selection":
            selection_labels = dict(
                record.fields_get(field.name, "selection")[field.name]["selection"]
            )
            value = selection_labels[field_value]
        else:
            value = field_value
        return value

    def _get_summary(self):
        """Set summary in reviews: field name: value or old_value > new_value.
        Example: Vendor: Azure Interior."""
        if self.definition_id.summary_field_id:
            field = self.definition_id.summary_field_id
            record = self.env[self.model].browse(self.res_id)
            change = self.changeset_id.change_ids.filtered(
                lambda x: x.field_id == field
            )
            if change:
                old_value = self._get_field_value_display_from_record(
                    field, change.origin_value_display, record
                )
                new_value = self._get_field_value_display_from_record(
                    field, change.new_value_display, record
                )
                value = "%s > %s" % (old_value, new_value)
            else:
                field_value = record[field.name]
                value = self._get_field_value_display_from_record(
                    field, field_value, record
                )
            return "%s: %s" % (field.field_description, value)
        return False
