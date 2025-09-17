# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        change_invoice_tag_ids = 'invoice_tag_ids' in vals
        res = super(AccountMove, self).write(vals)
        if change_invoice_tag_ids:
            self._action_assign_invoice_tag_ids()
        return res



    def action_post(self):
        res = super(AccountMove,self).action_post()
        self._action_assign_invoice_tag_ids()
        return res


    def _action_assign_invoice_tag_ids(self):
        for move in self:
            move.with_context(skip_account_move_synchronization=True).line_ids.write({'invoice_tag_ids':[(6,0,move.invoice_tag_ids.ids)]})


    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(
            view_id=view_id, 
            view_type=view_type, 
            toolbar=toolbar, 
            submenu=submenu
        )

        # Only process search views
        if view_type != 'search':
            return res

        # Parse the XML architecture of the view
        doc = etree.XML(res['arch'])

        # Find and remove filters with the specific domain
        for filter_node in doc.xpath("//filter[@domain]"):
            domain_value = filter_node.attrib.get('domain', '')
            if "[('invoice_tag_ids', '='" in domain_value:  # Check if the specific domain pattern exists
                parent = filter_node.getparent()
                if parent is not None:
                    parent.remove(filter_node)  # Remove the node from its parent

        # Update the modified architecture
        res['arch'] = etree.tostring(doc, encoding='unicode', pretty_print=True)

        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMoveLine, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu
        )

        # Only process search views
        if view_type != 'search':
            return res

        # Parse the XML architecture of the view
        doc = etree.XML(res['arch'])

        # Find and remove filters with the specific domain
        for filter_node in doc.xpath("//filter[@domain]"):
            domain_value = filter_node.attrib.get('domain', '')
            if "[('invoice_tag_ids', '='" in domain_value:  # Check if the specific domain pattern exists
                parent = filter_node.getparent()
                if parent is not None:
                    parent.remove(filter_node)  # Remove the node from its parent

        # Update the modified architecture
        res['arch'] = etree.tostring(doc, encoding='unicode', pretty_print=True)

        return res