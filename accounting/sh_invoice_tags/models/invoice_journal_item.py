# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import api, models, fields
from lxml import etree


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    invoice_tag_ids = fields.Many2many(
        'sh.invoice.tags',
        string="Invoice Tags"
    )

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
        res = super(AccountMoveLine, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )

        if view_type != 'search':
            return res

        doc = etree.XML(res['arch'])

        invoice_tags = self.env['sh.invoice.tags'].search([]).sorted(
            'name', reverse=True,
        )

        if not invoice_tags:
            return res

        node = doc.find(".//filter[@name='receivable']")
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
    
    @api.model
    def default_get(self, fields_list):
        res = super(AccountMoveLine, self).default_get(fields_list)
        if self.env.company.invoice_tags_id:
            res.update(
                {'invoice_tag_ids': [(6, 0, self.env.company.invoice_tags_id.ids)]})
        return res
