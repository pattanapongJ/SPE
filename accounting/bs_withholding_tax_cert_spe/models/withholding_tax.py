from odoo import models, api, _
from odoo.exceptions import UserError

class CreateWithholdingTaxCert(models.TransientModel):
    _inherit = 'create.withholding.tax.cert'


    def check_validation(self):
        self = self.with_context(skip_move_type_validation=True)
        super(CreateWithholdingTaxCert,self).check_validation()


