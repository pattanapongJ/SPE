# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, models, fields
from lxml import etree


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_tag_ids = fields.Many2many('sh.invoice.tags',
                                       string="Invoice Tags")

    def insert_after(self, element, new_element):
        if isinstance(element, etree._Element):
            parent = element.getparent()
            parent.insert(parent.index(element) + 1, new_element)

    @api.model
    def fields_view_get(
        self,
        view_id=None,
        view_type='form',
        toolbar=False,
        submenu=False,
    ):
        res = super(AccountMove, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )

        # useful when we need to deal with multiple views for same model filters
        view_record = False
        node=False
        if view_id:
            view_record = self.env['ir.ui.view'].sudo().search(
                [('id', '=', view_id)], limit=1)

        if view_type != 'search':
            return res

        doc = etree.XML(res['arch'])

        invoice_tags = self.env['sh.invoice.tags'].search([]).sorted(
            'name',
            reverse=True,
        )

        #### if there are multiple views than we will check for which view
        if view_record:
            if view_record.xml_id == 'account.view_account_invoice_filter':
                node = doc.find(".//filter[@name='late']")
            else:
                node = doc.find(".//filter[@name='to_check']")

        if not invoice_tags:
            return res

        self.insert_after(node, etree.fromstring("<separator/>"))

        for invoice_tag in invoice_tags:
            invoice_tag_filter = """
            <filter string="{name}" domain="[('invoice_tag_ids', '=', {invoice_tag_id})]"/>
            """.format(**{
                'name': invoice_tag.name,
                'invoice_tag_id': invoice_tag.id,
            })
            self.insert_after(node, etree.fromstring(invoice_tag_filter))
        self.insert_after(node, etree.fromstring("<separator/>"))
        res['arch'] = etree.tostring(doc)

        return res

    def action_mass_tag_update(self):
        return {
            'name':
            'Mass Tag Update',
            'res_model':
            'sh.update.mass.tag.wizard',
            'view_mode':
            'form',
            'context': {
                'default_account_move_ids':
                [(6, 0, self.env.context.get('active_ids'))]
            },
            'view_id':
            self.env.ref(
                'sh_invoice_tags.sh_update_mass_tag_wizard_form_view').id,
            'target':
            'new',
            'type':
            'ir.actions.act_window'
        }

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMove, self).default_get(fields_list)
        if self.env.company.invoice_tags_id:
            res.update(
                {'invoice_tag_ids': [(6, 0, self.env.company.invoice_tags_id.ids)]})
        return res
