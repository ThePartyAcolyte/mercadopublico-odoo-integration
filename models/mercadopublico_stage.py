"""
Tender pipeline stage model for Mercado Público integration.

Defines Kanban stages (e.g. En Espera, Convertida, Descartada) used to track
the workflow status of tender records in the Odoo Kanban view.
"""
from odoo import fields, models


class MercadoPublicoStage(models.Model):
    """Workflow stage definition for tender and quick buy records."""

    _name = "mercadopublico.stage"
    _description = "Etapas del flujo de trabajo de licitaciones"
    _order = "sequence, id"

    name = fields.Char(string="Nombre de la Etapa", required=True)
    sequence = fields.Integer(string="Secuencia", default=10)
    fold = fields.Boolean(
        string="Plegada en Kanban",
        help="Si está marcado, la etapa se mostrará plegada en la vista Kanban.",
    )
