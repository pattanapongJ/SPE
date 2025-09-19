from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    partners = env['res.partner'].search([('check_credit', '=', False)])  # ค้นหา partner ที่ check_credit เป็น False
    partners.write({'check_credit': True})  # อัปเดตฟิลด์ check_credit ให้เป็น True
