from lxml import etree

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                         submenu=submenu)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='property_purchase_currency_id']"):
            if view_type == 'form':
                node.set('domain', "[('show_in_purchase', '=', True)]")

        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
