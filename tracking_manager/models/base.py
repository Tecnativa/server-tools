# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    # TODO: Remove if merged https://github.com/odoo/odoo/pull/156236
    def _mail_track(self, tracked_fields, initial_values):
        _tracked_fields = tracked_fields
        tracked_fields_properties = {}
        for tf_key in list(_tracked_fields.keys()):
            tracked_field = tracked_fields[tf_key]
            if tracked_field["type"] == "properties":
                tracked_fields_properties[tf_key] = tracked_field
        updated, tracking_value_ids = super()._mail_track(
            tracked_fields, initial_values
        )
        # Remove unnecessary tracking_value_ids
        tracking_value_ids_keys_to_delete = []
        for tf_key in list(tracked_fields_properties.keys()):
            field = self.env["ir.model.fields"]._get(self._name, tf_key)
            for key, vals in enumerate(tracking_value_ids):
                if vals[2]["field_id"] == field.id:
                    tracking_value_ids_keys_to_delete.append(key)
        for key in tracking_value_ids_keys_to_delete:
            tracking_value_ids.pop(key)
        # Extra things for properties
        for col_name, _sequence in self._mail_track_order_fields(
            tracked_fields_properties
        ):
            if col_name not in initial_values:
                continue
            initial_value, new_value = initial_values[col_name], self[col_name]
            if new_value == initial_value or (not new_value and not initial_value):
                continue
            p_keys = list(initial_value.keys()) if initial_value else []
            properties_data = {}
            for definition in self.read([col_name])[0][col_name]:
                properties_data[definition["name"]] = definition
            for p_key in p_keys:
                if initial_value[p_key] != new_value[p_key]:
                    col_info_item = properties_data[p_key]
                    tracking_vals = self.env[
                        "mail.tracking.value"
                    ]._create_tracking_values(
                        initial_value[p_key],
                        new_value[p_key],
                        col_name,
                        properties_data[p_key],
                        self,
                    )
                    tracking_vals["property_name"] = col_info_item["string"]
                    tracking_value_ids.append([0, 0, tracking_vals])
        return updated, tracking_value_ids
