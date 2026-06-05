from odoo import models, fields, api, _
from datetime import timedelta

class MercadoPublicoLimpiarWizard(models.TransientModel):
    _name = 'mercadopublico.limpiar.wizard'
    _description = 'Asistente de Limpieza de Licitaciones'

    dias = fields.Integer('Días hacia atrás', default=30, required=True)
    solo_no_aptas = fields.Boolean('Solo Licitaciones No Aptas', default=True)
    borrar_sin_oportunidad = fields.Boolean('Solo sin Oportunidad CRM', default=True)

    def action_limpiar(self):
        self.ensure_one()
        fecha_limite = fields.Datetime.now() - timedelta(days=self.dias)
        
        domain = [('create_date', '<', fecha_limite)]
        if self.solo_no_aptas:
            domain.append(('decision_filtro', '=', 'no_apta'))
        if self.borrar_sin_oportunidad:
            domain.append(('opportunity_id', '=', False))
            
        licitaciones = self.env['mercadopublico.licitacion'].search(domain)
        count = len(licitaciones)
        licitaciones.unlink()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Limpieza Completada',
                'message': f"Se han eliminado {count} registros (Licitaciones y Compras Ágiles).",
                'type': 'success',
                'sticky': False,
            }
        }
