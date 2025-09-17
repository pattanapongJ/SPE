from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from datetime import datetime

    
class ProductTemplate(models.Model):
    _inherit = "product.template"

    # source = fields.Selection([('domestic', 'Domestic'), ('inter', 'International')], default = "domestic")
    # country_source = fields.Many2one('res.country')
    source_history_ids = fields.One2many(
        comodel_name="product.source.history",
        inverse_name="product_tmpl_id",
        copy=False
    )

    # def write(self, vals):
    #     if "country_source" in vals:
    #         for record in self:
    #             source_from_ids = record.country_source.ids if record.country_source else []
    #             source_to_ids = [vals["country_source"]] if vals["country_source"] else []
                
    #             record.source_history_ids.create({
    #                 'product_tmpl_id': record.id,
    #                 'source_from_ids': [(6, 0, [source_from_ids] if isinstance(source_from_ids, int) else source_from_ids)],
    #                 'source_to_ids': [(6, 0, source_to_ids)],
    #                 'last_updated': datetime.now(),
    #                 'user_id': self.env.user.id
    #             })
    #     return super().write(vals)


class ProductSourceHistory(models.Model):
    _name = "product.source.history"
    _description = 'Product Source History'
    _order = "id desc"

    product_tmpl_id = fields.Many2one(comodel_name="product.template")
    source_from_ids = fields.Many2many(
        "res.country",
        "product_source_history_country_from_rel",
        "history_id",
        "country_id",
        string="Source From"
    )
    source_to_ids = fields.Many2many(
        "res.country",
        "product_source_history_country_to_rel",
        "history_id",
        "country_id",
        string="Source To"
    )
    last_updated = fields.Datetime(string = 'Last Updated')
    user_id = fields.Many2one(string="Update By", comodel_name="res.users")