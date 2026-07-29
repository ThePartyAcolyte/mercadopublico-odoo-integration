"""
Feedback wizard for manual tender classification decisions.

Allows users to manually override the automated scoring result, marking a
tender as 'apta' or 'no_apta'. When marking as 'apta', the wizard suggests
UNSPSC categories found in the tender's items so the user can add them to
the company filter configuration as positive training signal.
"""
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MercadoPublicoTenderDiscardCategory(models.TransientModel):
    """Line model holding a suggested category within the feedback wizard."""

    _name = "mercadopublico.tender.discard.category"
    _description = "Categoría Sugerida en Feedback"

    wizard_id = fields.Many2one(
        "mercadopublico.tender.discard.wizard", required=True, ondelete="cascade"
    )
    category_id = fields.Many2one(
        "mercadopublico.category", string="Categoría", required=True
    )
    selected = fields.Boolean("Añadir", default=True)


class MercadoPublicoTenderDiscardWizard(models.TransientModel):
    """
    Wizard for providing manual feedback on a tender's relevance classification.

    When marking as 'apta', suggested categories from the tender's item list
    are presented so the user can add them to the company filter configuration.
    """

    _name = "mercadopublico.tender.discard.wizard"
    _description = "Wizard de Feedback para Licitaciones"

    tender_id = fields.Many2one(
        "mercadopublico.tender", string="Licitación", required=True
    )
    action_type = fields.Selection(
        [("apta", "Marcar como Apta"), ("no_apta", "Descartar / No Apta")],
        string="Acción",
        required=True,
    )

    # Discard-specific fields
    discard_reason_type = fields.Selection(
        [
            ("filtro", "No corresponde al rubro (Ajustar Filtro)"),
            ("catalogo", "Productos solicitados no están en el catálogo"),
            ("tecnico", "Falta de capacidad técnica"),
            ("economico", "Falta de solvencia económica / Boletas"),
            ("plazo", "Plazos imposibles"),
            ("dirigida", "Marca o especificaciones exclusivas (Dirigida)"),
            ("presupuesto", "Presupuesto estimado demasiado bajo"),
            ("ubicacion", "Ubicación geográfica inviable"),
            ("conflicto", "Conflicto de interés"),
            ("otro", "Otro motivo"),
        ],
        string="Motivo de descarte",
        default="filtro",
    )
    additional_comment = fields.Text("Comentario / Motivo")
    category_line_ids = fields.One2many(
        "mercadopublico.tender.discard.category",
        "wizard_id",
        string="Categorías Sugeridas",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        tender_id = res.get("tender_id") or self.env.context.get("default_tender_id")
        if tender_id and "category_line_ids" in fields_list:
            tender = self.env["mercadopublico.tender"].browse(tender_id)
            suggested = self.env["mercadopublico.category"]
            if tender.process_type == "licitacion":
                suggested = tender.category_ids
            else:
                for item in tender.item_ids:
                    if item.product_code and len(item.product_code) == 8:
                        family_code = item.product_code[:4] + "0000"
                        class_code = item.product_code[:6] + "00"
                        cat = self.env["mercadopublico.category"].search(
                            [("codigo", "in", [class_code, family_code])],
                            order="codigo desc",
                            limit=1,
                        )
                        if cat:
                            suggested |= cat
            lines = []
            for cat in suggested:
                lines.append((0, 0, {"category_id": cat.id, "selected": True}))
            res["category_line_ids"] = lines
        return res

    @api.onchange("tender_id")
    def _onchange_tender_for_suggestions(self):
        """
        Populates the suggested category list from the linked tender's items.

        For v1 tenders, uses the already-resolved category_ids. For v2 quick
        buys, resolves the UNSPSC class and family codes from 8-digit product codes.
        """
        if not self.tender_id:
            self.category_line_ids = [(5, 0, 0)]
            return

        tender = self.tender_id
        suggested = self.env["mercadopublico.category"]

        if tender.process_type == "licitacion":
            suggested = tender.category_ids
        else:
            for item in tender.item_ids:
                if item.product_code and len(item.product_code) == 8:
                    # Derive UNSPSC class (6-digit) and family (4-digit) from product code.
                    family_code = item.product_code[:4] + "0000"
                    class_code = item.product_code[:6] + "00"
                    cat = self.env["mercadopublico.category"].search(
                        [("codigo", "in", [class_code, family_code])],
                        order="codigo desc",
                        limit=1,
                    )
                    if cat:
                        suggested |= cat

        lines = [(5, 0, 0)]
        for cat in suggested:
            lines.append((0, 0, {"category_id": cat.id, "selected": True}))
        self.category_line_ids = lines

    def action_confirm(self):
        """
        Applies the user's feedback decision to the linked tender record.

        - For 'no_apta': sets discard_reason, resets rating to 0, and moves
          the record to the 'descartada' stage.
        - For 'apta': sets rating to 3, moves to 'en_espera' stage, and
          optionally adds selected categories to the company filter config.

        Returns:
            dict: An act_window_close action to dismiss the wizard.
        """
        self.ensure_one()
        tender = self.tender_id

        discard_label = dict(self._fields["discard_reason_type"].selection).get(
            self.discard_reason_type, ""
        )
        if self.additional_comment:
            discard_label = f"{discard_label}: {self.additional_comment}"

        vals = {"filter_decision": self.action_type, "state": "analizado"}

        if self.action_type == "no_apta":
            vals["discard_reason"] = discard_label
            vals["rating"] = "0"
            stage_discarded = self.env.ref(
                "mercadopublico_odoo_integration.etapa_descartada",
                raise_if_not_found=False,
            )
            if stage_discarded:
                vals["stage_id"] = stage_discarded.id
        else:
            vals["rating"] = "3"
            stage_waiting = self.env.ref(
                "mercadopublico_odoo_integration.etapa_en_espera",
                raise_if_not_found=False,
            )
            if stage_waiting:
                vals["stage_id"] = stage_waiting.id

        tender.write(vals)

        log_msg = _("Decisión manual del usuario: <b>%s</b>.") % (
            self.action_type.upper()
        )

        if self.action_type == "apta":
            categories_to_add = (
                self.category_line_ids.filtered(lambda l: l.selected)
                .mapped("category_id")
            )
            if categories_to_add:
                self.env.company.mercadopublico_category_ids = [
                    (4, cat.id) for cat in categories_to_add
                ]
                cat_names = ", ".join(categories_to_add.mapped("name"))
                log_msg += _(
                    "<br/>Se añadieron las siguientes categorías a los filtros: <i>%s</i>"
                ) % cat_names

        tender.message_post(body=log_msg)
        return {"type": "ir.actions.act_window_close"}
