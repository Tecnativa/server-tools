# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(env.cr, "record_changeset_change", "res_id"):
        openupgrade.logged_query(
            env.cr,
            """
            ALTER TABLE record_changeset_change
            ADD COLUMN res_id int;
            """,
        )
        openupgrade.logged_query(
            env.cr,
            """UPDATE record_changeset_change
            SET res_id = record_changeset.res_id
            FROM record_changeset
            WHERE record_changeset.id = record_changeset_change.changeset_id
            AND record_changeset_change.res_id = 0""",
        )
