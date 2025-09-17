# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PdcWizard(models.Model):
    _inherit = 'pdc.wizard'

    company_id = fields.Many2one('res.company',string='Company', default=lambda self: self.env.company, tracking=True, required=True, readonly=False)
    
    @api.model
    def default_get(self, default_fields):
        res = super(PdcWizard, self).default_get(default_fields)
        if self._context.get('active_model') == 'account.payment':
            res['pdc_effective_date'] = False
        return res



    @api.model
    def _get_check_formate(self):
        company_id = self.env.user.company_id.id
        formate_id = self.env['cheque.setting'].search([('set_default', '=', True), ('company_id', '=', company_id)],
                                                       limit=1)
        return formate_id.id

    cheque_formate_id = fields.Many2one('cheque.setting', 'Cheque Formate', default=_get_check_formate)
    cheque_no = fields.Char('Cheque No')
    text_free = fields.Char('Free Text')
    partner_text = fields.Char('Partner Title')
    crossed_text = fields.Char(string='Crossed Text')
    is_acc_pay = fields.Boolean(related='cheque_formate_id.is_acc_pay')
    state = fields.Selection(selection_add=[
            ("rc", "Replace Cheque")
        ],
        ondelete={"rc": "cascade"},)
    pdc_effective_date = fields.Date(
        string='Effective Date',
        store=True,
        index=True,
        help="วันที่เช็คเคลียร์ริ่ง (จะใช้วันที่นี้ในการบันทึกบัญชีเมื่อเช็คเคลียร์ริ่ง",
        default=False)
    pdc_bounce_reason = fields.Many2one(
        'cheque.bounce.reason',
        string='Bounce Reason',
        help="สาเหตุของการเกิดเช็คส่งคืน",
        index=True )

    @api.onchange('cheque_formate_id')
    def onchange_cheque_formate_id(self):
        self.crossed_text = self.cheque_formate_id.crossed_text

    def action_rc_button(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'bs_pdc.action_pdc_rc_wizard')
        context = dict(self._context)
        context.update({
            'default_pdc_id': self.id
        })
        action['context'] = context
        return action


    def check_pdc_account(self):
        account_id = super(PdcWizard,self).check_pdc_account()
        if self.payment_type == 'receive_money' and self.journal_id.pdc_receipt_account_id:
            return self.journal_id.pdc_receipt_account_id.id
        elif self.payment_type == 'send_money' and self.journal_id.pdc_payment_account_id:
            return self.journal_id.pdc_payment_account_id.id

        else:
            return account_id


    def action_done(self):
        self._check_validation_before_done()
        super().action_done()



    def _check_validation_before_done(self):
        invalid_pdc_ids = self.filtered(lambda x:not x.pdc_effective_date)
        if len(invalid_pdc_ids)>0:
            raise ValidationError(_('Please Fill Effective Date'))


    # override reset to draft
    def action_state_draft(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        active_models = self.env[active_model].browse(active_ids)

        for model in active_models:
            if model.state not in ('done','cancel','rc'):                
                raise UserError('Only done and cancel, replace check state pdc can reset to draft')

        for model in active_models:
            move_ids = self.env['account.move'].search([('pdc_id', '=', model.id)])
            for move in move_ids:
                move.button_draft()
                move.button_cancel()
                # lines = self.env['account.move.line'].search([('move_id', '=', move.id)])
                # lines.unlink()
            model.sudo().write({
                'state':'draft',
                'done_date' : False
                })

            # for move in move_ids:
            #     self.env.cr.execute(""" delete from account_move where id =%s""" %(move.id,))