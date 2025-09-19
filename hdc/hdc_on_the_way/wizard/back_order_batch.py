from odoo import models, fields, api

class CreateBackorderWizard(models.TransientModel):
    _name = 'create.backorder.wizard'
    _description = 'Create Backorder Wizard'

    batch_id = fields.Many2one('stock.picking.batch', string='Batch Transfer')
    
    def process(self):
        for batch in self :
            batch.batch_id.create_backorder(1)
        return False
    
    def process_cancel_backorder(self):
        for batch in self :
            batch.batch_id.create_backorder(0)
        return False
    