from odoo import models, fields

class MercadopublicoEtapa(models.Model):
    _name = 'mercadopublico.etapa'
    _description = 'Etapas del flujo de trabajo de licitaciones'
    _order = 'sequence, id'

    name = fields.Char(string="Nombre de la Etapa", required=True)
    sequence = fields.Integer(string="Secuencia", default=10)
    fold = fields.Boolean(string="Plegada en Kanban", help="Si está marcado, la etapa se mostrará plegada en la vista Kanban.")
