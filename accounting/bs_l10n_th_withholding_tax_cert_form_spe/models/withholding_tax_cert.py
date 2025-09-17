from odoo import models, fields


class WithholdingTaxCert(models.Model):
    _inherit = 'withholding.tax.cert'
    _rec_name = 'tax_cert_name'

    reference = fields.Char(string='Ref No.', copy=False)
    show_signature_and_date = fields.Boolean(string='Signature & Date', default=True)
    tax_cert_name = fields.Char(string='WHT Number', copy=False, default='New', readonly=True)

    def action_done(self):
        res = super(WithholdingTaxCert, self).action_done()
        self.action_generate_sequence()
        return res

    def action_generate_sequence(self):
        for wth in self.filtered(lambda x: x.tax_cert_name in ['New']):
            wth.tax_cert_name = wth.get_withholding_tax_cert_sequence_number()


    def get_withholding_tax_cert_sequence_number(self):
        self.ensure_one()
        Sequence = self.env['ir.sequence'].with_company(self.company_id)
        sequence = Sequence.search([('code', '=', 'withholding.tax.cert'),('company_id','=',self.company_id.id)], limit=1)
        if not sequence.exists():
            Sequence.create({
                'code': 'withholding.tax.cert',
                'name': 'Withholding Tax Certificate Sequence',
                'prefix': 'WHT%(year)s%(month)s',
                'padding': 4,
                'use_date_range': True,
                'company_id': self.company_id.id
            })
        return Sequence.with_context(ir_sequence_date=self.date).next_by_code('withholding.tax.cert',sequence_date=self.date) or 'New'
