# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # parent_company = fields.Many2one("res.partner",string="Parent Company")

    delivery_trl = fields.Many2one("delivery.round", string = "สายส่ง TRL")
    delivery_trl_description = fields.Char(related = "delivery_trl.name", string = "สายส่ง TRL Description")
    # delivery_company = fields.Many2one("company.delivery.round", string = "Mode of delivery")
    delivery_company_description = fields.Char(related = "delivery_company.name",
                                               string = "Mode of delivery Description")
    payment_term_description_sale = fields.Text(related="property_payment_term_id.note",string="Payment Terms Description")
    payment_term_description_purchase = fields.Text(related="property_supplier_payment_term_id.note",string="Payment Terms Description")
    internal_remark = fields.Text(string="Remark")

    register_no = fields.Char(string="Register No.")
    register_date = fields.Date(string="Register Date")
    register_capital = fields.Float(string="Register Capital")
    director_lists = fields.Text(string="Director Lists")
    bank_guarantee = fields.Boolean(string="Bank Guarantee")
    bank_guarantee_amount = fields.Float(string="Bank Guarantee Amount")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    