from odoo import api, models,fields
from datetime import date

class ProductCategory(models.Model):
    _inherit = "product.category"

    child_id = fields.One2many('product.category', 'parent_id', 'Child Categories',index=True)
    parent_path = fields.Char(index=True)
    # group_level_1 = fields.Char(string="level 1",index=True, compute="_compute_level", store=True)
    # group_level_2 = fields.Char(string="level 2",index=True, compute="_compute_level", store=True)
    # group_level_3 = fields.Char(string="level 3",index=True, compute="_compute_level",store=True)
    # level_show = fields.Char(string="level" ,index=True, compute="_compute_level")

    category_level_id = fields.Many2one('product.category.level', string = 'Category Level')
    
    # def _compute_level(self):
    #     for category in self:
    #         if category.parent_path:
    #             parent_ids = [int(id) for id in category.parent_path.split('/') if id]
    #             level_category = self.env['product.category'].browse(parent_ids)
    #             if len(level_category) >= 3:
    #                 category.level_show = level_category[0].name
    #                 category.group_level_1 = level_category[0].name
    #                 category.group_level_2 = level_category[1].name
    #                 category.group_level_3 = level_category[2].name

    #             elif len(level_category) == 2:
    #                 category.group_level_1 = level_category[0].name
    #                 category.group_level_2 = level_category[1].name
    #                 category.group_level_3 = category.name
    #                 category.level_show = level_category[0].name
                    
    #             elif len(level_category) == 1:
    #                 category.group_level_1 = level_category[0].name
    #                 category.group_level_2 = category.name
    #                 category.group_level_3 = category.name
    #                 category.level_show = level_category[0].name
    #         else:
    #             category.level_show = ''
    #             category.group_level_1 = ''
    #             category.group_level_2 = ''
    #             category.group_level_3 = ''

class ProductCategoryLevel(models.Model):
    _name = "product.category.level"

    name = fields.Char(string="Level Description")
    level = fields.Integer(string="Level")

    def name_get(self):
        result = []
        for record in self:
            rec_name = str(record.level)
            result.append((record.id, rec_name))
        return result

 





    