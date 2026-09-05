"""
Wizard for editing UNSPSC category assignments on related records.

Opens from a button on product.template or product.category to allow the user
to select UNSPSC categories (mercadopublico.category) without navigating away
from the record form.
"""
from odoo import api, fields, models


class MercadoPublicoCategoryWizard(models.TransientModel):
    """Transient wizard that edits the UNSPSC category mapping of a related record."""

    _name = "mercadopublico.category.wizard"
    _description = "Asistente para editar Categorías UNSPSC"

    res_model = fields.Char("Modelo Relacionado", required=True)
    res_id = fields.Integer("ID Relacionado", required=True)
    mercadopublico_category_ids = fields.Many2many(
        "mercadopublico.category",
        "mercadopublico_category_wizard_new_rel",
        string="Categorías UNSPSC",
    )

    @api.model
    def default_get(self, fields_list):
        """Pre-fills the category list from the source record's current selection."""
        res = super().default_get(fields_list)
        res_model = self._context.get("active_model")
        res_id = self._context.get("active_id")
        if res_model and res_id:
            res["res_model"] = res_model
            res["res_id"] = res_id
            record = self.env[res_model].browse(res_id)
            if record.exists() and hasattr(record, "mercadopublico_category_ids"):
                res["mercadopublico_category_ids"] = [
                    (6, 0, record.mercadopublico_category_ids.ids)
                ]
        return res

    def action_save(self):
        """
        Writes the selected categories back to the source record.

        Returns:
            dict: An act_window_close action to dismiss the wizard.
        """
        if self.res_model and self.res_id:
            record = self.env[self.res_model].browse(self.res_id)
            if record.exists() and hasattr(record, "mercadopublico_category_ids"):
                record.mercadopublico_category_ids = [
                    (6, 0, self.mercadopublico_category_ids.ids)
                ]
        return {"type": "ir.actions.act_window_close"}
