from odoo import models, fields, api

class MercadoPublicoCategoriaWizard(models.TransientModel):
    _name = 'mercadopublico.categoria.wizard'
    _description = 'Asistente para editar Categorías UNSPSC'

    res_model = fields.Char('Modelo Relacionado', required=True)
    res_id = fields.Integer('ID Relacionado', required=True)

    categoria_ids = fields.Many2many(
        'mercadopublico.categoria',
        'mercadopublico_categoria_wizard_rel',
        string='Categorías UNSPSC'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res_model = self._context.get('active_model')
        res_id = self._context.get('active_id')
        
        if res_model and res_id:
            res['res_model'] = res_model
            res['res_id'] = res_id
            record = self.env[res_model].browse(res_id)
            if record.exists() and hasattr(record, 'mercadopublico_categoria_ids'):
                res['categoria_ids'] = [(6, 0, record.mercadopublico_categoria_ids.ids)]
                
        return res

    def action_save(self):
        if self.res_model and self.res_id:
            record = self.env[self.res_model].browse(self.res_id)
            if record.exists() and hasattr(record, 'mercadopublico_categoria_ids'):
                record.mercadopublico_categoria_ids = [(6, 0, self.categoria_ids.ids)]
        return {'type': 'ir.actions.act_window_close'}
