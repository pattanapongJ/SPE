from odoo import fields, models, api

class RequestTypeMR(models.Model):
    _name = "request.type.mr"
    _description = "Request Type"

    name = fields.Char("Request Name",required=True, tracking=True)
    request_type = fields.Selection([
        ('example_product', 'สินค้าตัวอย่าง'),
        ('modify_product', 'สินค้าที่ต้องดำเนินการแก้ไข'),
        ('new_product', 'สินค้าใหม่'),
        ('old_product', 'สินค้าเคยมีการสั่งผลิต'),
        ], string='Request Type',tracking=True,required=True,)
    is_design = fields.Boolean(string="Design",default=False, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    is_modify = fields.Boolean(string='Is Modify')
    is_claim = fields.Boolean(string='Is Claim')
    is_repack = fields.Boolean(string='Is Repack')
    receipt_picking_type_id = fields.Many2one('stock.picking.type', 'Receipt Operation',domain="[('code', '=', 'incoming')]")

class ProductTypeMR(models.Model):
    _name = "product.type.mr"
    _description = "Product Type"

    name = fields.Char("Product Type",required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Factory', domain="[('code', '=', 'mrp_operation')]",)
    department_id = fields.Many2one('hr.department', string='Department',)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # Location 
    modify_location = fields.Many2one("stock.location", string="Modify Location", domain="[('usage', '=', 'internal')]")
    repack_location = fields.Many2one("stock.location", string="Repack Location", domain="[('usage', '=', 'internal')]")
    repair_location = fields.Many2one("stock.location", string="Repair Location", domain="[('usage', '=', 'internal')]")
    claim_location = fields.Many2one("stock.location", string="Claim Location", domain="[('usage', '=', 'internal')]")
    scrap_location = fields.Many2one("stock.location", string="Scrap Location", domain="[('scrap_location', '=', 'True')]")

    # Operation type 
    into_factory_picking_type_id = fields.Many2one('stock.picking.type', 'Transfer into Factory',domain="[('addition_operation_types.code', '=', 'AO-06')]")
    out_factory_picking_type_id = fields.Many2one('stock.picking.type', 'Transfer out of Factory',domain="[('addition_operation_types.code', '=', 'AO-06')]")
    modify_factory_picking_type_id = fields.Many2one('stock.picking.type', 'Modify Operation',domain="[('addition_operation_types.code', '=', 'AO-06')]")
    repack_factory_picking_type_id = fields.Many2one('stock.picking.type', 'Repack Operation',domain="[('addition_operation_types.code', '=', 'AO-06')]")
    repair_factory_picking_type_id = fields.Many2one('stock.picking.type', 'Repair Operation',domain="[('addition_operation_types.code', '=', 'AO-06')]")
    claim_factory_picking_type_id = fields.Many2one('stock.picking.type', 'Claim Operation',domain="[('addition_operation_types.code', '=', 'AO-06')]")
