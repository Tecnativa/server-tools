# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartnerBankCustom(models.Model):
    _name = "res.partner.bank.custom"

    acc_number = fields.Char(required=True)
    category_ids = fields.Many2many(comodel_name="res.partner.category")
    bank_id = fields.Many2one("res.bank")
    partner_id = fields.Many2one(
        "res.partner", ondelete="cascade", index=True, required=True
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    custom_bank_ids = fields.One2many("res.partner.bank.custom", "partner_id")
