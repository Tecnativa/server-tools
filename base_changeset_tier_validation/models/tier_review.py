# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class TierReview(models.Model):
    _inherit = "tier.review"

    summary_field_id = fields.Many2one(
        comodel_name="ir.model.fields", compute="_compute_summary_field_id", store=True
    )
    summary = fields.Char(string="Summary", compute="_compute_summary", store=True)
    changeset_id = fields.Many2one(comodel_name="record.changeset")
    changeset_ref = fields.Reference(
        selection=lambda self: [
            (model.model, model.name) for model in self.env["ir.model"].search([])
        ],
        compute="_compute_changeset_ref",
    )
    changeset_ref_display_name = fields.Char(
        compute="_compute_changeset_ref_display_name",
    )

    @api.depends("definition_id", "changeset_id")
    def _compute_summary_field_id(self):
        for item in self:
            changes = item.changeset_id.change_ids
            if changes and any(x.rule_id.summary_field_id for x in changes):
                final_changes = changes.filtered(lambda x: x.rule_id.summary_field_id)
                change = fields.first(final_changes)
                item.summary_field_id = change.rule_id.summary_field_id
            else:
                item.summary_field_id = item.definition_id.summary_field_id

    @api.depends("summary_field_id", "model", "res_id", "changeset_id")
    def _compute_summary(self):
        for item in self.filtered(lambda x: x.summary_field_id):
            changes = item.changeset_id.change_ids.filtered(
                lambda x: x.field_id == item.summary_field_id
            )
            if changes:
                change = fields.first(changes)
                value = "%s > %s" % (
                    change.origin_value_display,
                    change.new_value_display,
                )
            else:
                field_name = item.summary_field_id.name
                model = self.env[item.model]
                model_field_def = model._fields[field_name]
                record = model.browse(item.res_id)
                value = model_field_def.convert_to_write(record[field_name], record)
            item.summary = "%s: %s" % (item.summary_field_id.field_description, value)

    @api.depends("changeset_id", "changeset_id.model", "changeset_id.res_id")
    def _compute_changeset_ref(self):
        for item in self:
            if item.changeset_id and item.model != item.changeset_id.model:
                item.changeset_ref = "%s,%s" % (
                    item.changeset_id.model,
                    item.changeset_id.res_id,
                )

            else:
                item.changeset_ref = item.changeset_ref

    @api.depends("changeset_id", "changeset_id.model", "changeset_id.res_id")
    def _compute_changeset_ref_display_name(self):
        for item in self:
            if item.changeset_id and item.model != item.changeset_id.model:
                record = self.env[item.changeset_id.model].browse(
                    item.changeset_id.res_id
                )
                item.changeset_ref_display_name = record.display_name
            else:
                item.changeset_ref_display_name = item.changeset_ref_display_name

    def validate_tier(self):
        self.ensure_one()
        self._tier_process("approved")

    def reject_tier(self):
        self.ensure_one()
        self._tier_process("rejected")

    def _tier_process(self, status):
        """Custom process to accept/reject, similar to _validate_tier()
        and _rejected_tier().
        If you have a changeset_id defined, we want to cancel only first pending
        revision  and the linked changeset."""
        self.ensure_one()
        if self.changeset_id and status == "approved":
            self.changeset_id.apply()
        elif self.changeset_id and status == "rejected":
            self.changeset_id.cancel()
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