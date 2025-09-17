# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import base64
import xlrd

class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_import_serial(self):

        # Column 0 : ID Product Template
        # Column 1 : ID UoM
        # Column 2 : Factor Base (Float)
        # Column 3 : Uom Type (base, both)
        # Column 4 : Is Default Sale (True, False)
        # Column 5 : Is Default Purchase (True, False)

        if not self.import_pricelist:
            raise ValidationError(_("กรุณาอัพโหลดไฟล์ก่อน Import"))

        record_data = base64.b64decode(self.import_pricelist)
        wb = xlrd.open_workbook(file_contents=record_data)

        # Clear previous lines
        self.uom_map_ids = [(5, 0, 0)]

        # Excel column positions
        cols_product_id = 0
        cols_uom_id = 1
        cols_factor_base = 2
        cols_uom_type = 3
        cols_is_default_sale = 4
        cols_is_default_purchase = 5

        uom_map_ids_vals = []
        error_lines = []
        base_count = 0

        for sheet in wb.sheets():
            for row in range(1, sheet.nrows):  # skip header
                vals = {}
                try:
                    product_id_val = int(sheet.cell(row, cols_product_id).value or 0)
                    uom_id_val = int(sheet.cell(row, cols_uom_id).value or 0)
                    factor_base_val = float(sheet.cell(row, cols_factor_base).value or 0.0)
                    uom_type_val = str(
                        sheet.cell(row, cols_uom_type).value or ""
                    ).strip()  # base, both
                    is_default_sale_val = bool(
                        sheet.cell(row, cols_is_default_sale).value
                    )
                    is_default_purchase_val = bool(
                        sheet.cell(row, cols_is_default_purchase).value
                    )

                    # Constraints
                    if uom_type_val == "base":
                        base_count += 1
                        if base_count > 1:  # base ได้ value เดียว
                            error_lines.append(
                                f"Row {row+1}: Only one 'Base' is allowed."
                            )
                        if self.uom_id.id != uom_id_val:  # base ใช้ UoM เดียวกัน
                            error_lines.append(
                                f"Row {row+1}: 'Base' UoM ({uom_id_val}) must match product template's UoM ({self.uom_id.id})."
                            )

                    if product_id_val:
                        prod = self.env["product.template"].browse(product_id_val)
                        if prod.id != self.id:  # product ต้องชนิดเดียวกัน
                            error_lines.append(
                                f"Row {row+1}: Product ID ({product_id_val}) does not match template."
                            )

                    if uom_type_val not in ["base", "both"]:
                        error_lines.append(
                            f"UoM Type please Add only 'base' or 'both' row: {row+1}"
                        )

                    prod = self.env["product.template"].browse(product_id_val)
                    product_id_val = prod.product_variant_ids.ids

                    vals = {
                        "product_tmpl_id": self.id,
                        "product_id": product_id_val[0] if product_id_val else False,
                        "uom_id": uom_id_val,
                        "factor_base": factor_base_val,
                        "uom_type": uom_type_val,
                        "is_default_sale": is_default_sale_val,
                        "is_default_purchase": is_default_purchase_val,
                    }
                    uom_map_ids_vals.append((0, 0, vals))

                except Exception as e:
                    error_lines.append(f"Row {row+1}: {e}")

        if error_lines:
            text_error = "\n".join(error_lines)
            raise UserError(f"Import errors:\n{text_error}")

        self.write({"uom_map_ids": uom_map_ids_vals})

class ProductTemplate(models.Model):
    _inherit = "product.template"

    uom_map_ids = fields.One2many(
        "product.uom.map", "product_tmpl_id", string="UOM Map"
    )


    sale_uom_map_ids = fields.Many2many(
        "uom.uom",
        "product_template_sale_uom_map_rel",
        "product_tmpl_id",
        "uom_id",
        compute="_compute_sale_uom_map_ids",
        string="Sale UOMs",
        store=True,
    )

    purchase_uom_map_ids = fields.Many2many(
        "uom.uom",
        "product_template_purchase_uom_map_rel",
        "product_tmpl_id",
        "uom_id",
        compute="_compute_purchase_uom_map_ids",
        string="Purchase UOMs",
        store=True,
    )

    def action_import_serial(self):

        # Column 0 : ID Product Template
        # Column 1 : ID UoM
        # Column 2 : Factor Base (Float)
        # Column 3 : Uom Type (base, both)
        # Column 4 : Is Default Sale (True, False)
        # Column 5 : Is Default Purchase (True, False)

        if not self.import_pricelist:
            raise ValidationError(_("กรุณาอัพโหลดไฟล์ก่อน Import"))

        record_data = base64.b64decode(self.import_pricelist)
        wb = xlrd.open_workbook(file_contents=record_data)

        # Clear previous lines
        self.uom_map_ids = [(5, 0, 0)]

        # Excel column positions
        cols_product_id = 0
        cols_uom_id = 1
        cols_factor_base = 2
        cols_uom_type = 3
        cols_is_default_sale = 4
        cols_is_default_purchase = 5

        uom_map_ids_vals = []
        error_lines = []
        base_count = 0

        for sheet in wb.sheets():
            for row in range(1, sheet.nrows):  # skip header
                vals = {}
                try:
                    product_id_val = int(sheet.cell(row, cols_product_id).value or 0)
                    uom_id_val = int(sheet.cell(row, cols_uom_id).value or 0)
                    factor_base_val = float(sheet.cell(row, cols_factor_base).value or 0.0)
                    uom_type_val = str(
                        sheet.cell(row, cols_uom_type).value or ""
                    ).strip()  # base, both
                    is_default_sale_val = bool(
                        sheet.cell(row, cols_is_default_sale).value
                    )
                    is_default_purchase_val = bool(
                        sheet.cell(row, cols_is_default_purchase).value
                    )

                    # Constraints
                    if uom_type_val == "base":
                        base_count += 1
                        if base_count > 1:  # base ได้ value เดียว
                            error_lines.append(
                                f"Row {row+1}: Only one 'Base' is allowed."
                            )
                        if self.uom_id.id != uom_id_val:  # base ใช้ UoM เดียวกัน
                            error_lines.append(
                                f"Row {row+1}: 'Base' UoM ({uom_id_val}) must match product template's UoM ({self.uom_id.id})."
                            )

                    if product_id_val:
                        prod = self.env["product.template"].browse(product_id_val)
                        if prod.id != self.id:  # product ต้องชนิดเดียวกัน
                            error_lines.append(
                                f"Row {row+1}: Product ID ({product_id_val}) does not match template."
                            )

                    if uom_type_val not in ["base", "both"]:
                        error_lines.append(
                            f"UoM Type please Add only 'base' or 'both' row: {row+1}"
                        )

                    prod = self.env["product.template"].browse(product_id_val)
                    product_id_val = prod.product_variant_ids.ids

                    vals = {
                        "product_tmpl_id": self.id,
                        "product_id": product_id_val[0] if product_id_val else False,
                        "uom_id": uom_id_val,
                        "factor_base": factor_base_val,
                        "uom_type": uom_type_val,
                        "is_default_sale": is_default_sale_val,
                        "is_default_purchase": is_default_purchase_val,
                    }
                    uom_map_ids_vals.append((0, 0, vals))

                except Exception as e:
                    error_lines.append(f"Row {row+1}: {e}")

        if error_lines:
            text_error = "\n".join(error_lines)
            raise UserError(f"Import errors:\n{text_error}")

        self.write({"uom_map_ids": uom_map_ids_vals})
        
        # ตรวจสอบและสร้าง base UOM อัตโนมัติหลังจาก import
        self.action_update_uom_base()

    @api.onchange("file_name_import")
    def _onchange_file_name_import(self):
        if self.file_name_import:
            file_name = self.file_name_import.lower()
            if not (file_name.endswith(".xls") or file_name.endswith(".xlsx")):
                raise UserError("Please upload only .xls or .xlsx")


    @api.depends("uom_map_ids.is_default_sale")
    def _compute_sale_uom_map_ids(self):
        for template in self:
            # เรียงลำดับตาม is_default_sale และ sequence
            sorted_uoms = template.uom_map_ids.sorted(
                key=lambda l: (not l.is_default_sale, l.sequence)
            )
            template.sale_uom_map_ids = sorted_uoms.mapped("uom_id")

    @api.depends("uom_map_ids.is_default_purchase")
    def _compute_purchase_uom_map_ids(self):
        for template in self:
            # เรียงลำดับตาม is_default_purchase และ sequence
            sorted_uoms = template.uom_map_ids.sorted(
                key=lambda l: (not l.is_default_purchase, l.sequence)
            )
            template.purchase_uom_map_ids = sorted_uoms.mapped("uom_id")

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        """เมื่อเปลี่ยน uom_id ให้ตรวจสอบและสร้าง base UOM อัตโนมัติ"""
        if self.uom_id and not self.uom_map_ids.filtered(lambda l: l.uom_type == 'base'):
            # ถ้าไม่มี base UOM ให้สร้างใหม่
            self.action_update_uom_base()

    def action_update_uom_base(self):
        """สร้างหรืออัปเดต base UOM สำหรับสินค้า"""
        _logger = self.env['ir.logging']
        
        for rec in self:
            if not rec.uom_id:
                continue
                
            # ตรวจสอบว่ามี base UOM อยู่แล้วหรือไม่
            existing_base = rec.uom_map_ids.filtered(lambda l: l.uom_type == 'base')
            
            # ถ้าไม่มี base UOM ให้สร้างใหม่
            if not existing_base:
                rec.env['product.uom.map'].create({
                    'product_tmpl_id': rec.id,
                    'uom_id': rec.uom_id.id, 
                    'uom_type': 'base',
                    'factor_base': 1.0,
                    'is_default_sale': True,
                    'is_default_purchase': True,
                    'sequence': 0,
                })
                
                _logger.create({
                    'name': 'Update UOM Base',
                    'level': 'INFO',
                    'message': f'สร้าง base UOM ใหม่สำหรับสินค้า: {rec.name} (ID: {rec.id}) - UOM: {rec.uom_id.name}',
                    'func': 'action_update_uom_base',
                    'line': 0,
                    'type': 'server',
                    'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
                })
            # ถ้ามี base UOM อยู่แล้วแต่ uom_id เปลี่ยน ให้อัปเดต
            elif existing_base[0].uom_id != rec.uom_id:
                old_uom_name = existing_base[0].uom_id.name
                existing_base[0].write({
                    'uom_id': rec.uom_id.id,
                    'factor_base': 1.0,
                    'is_default_sale': True,
                    'is_default_purchase': True,
                    'sequence': 0,
                })
                
                _logger.create({
                    'name': 'Update UOM Base',
                    'level': 'INFO',
                    'message': f'อัปเดต base UOM สำหรับสินค้า: {rec.name} (ID: {rec.id}) - เปลี่ยนจาก {old_uom_name} เป็น {rec.uom_id.name}',
                    'func': 'action_update_uom_base',
                    'line': 0,
                    'type': 'server',
                    'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
                })
            # ถ้ามี base UOM อยู่แล้วและ uom_id ตรงกัน ให้อัปเดต default และ sequence
            else:
                existing_base[0].write({
                    'is_default_sale': True,
                    'is_default_purchase': True,
                    'sequence': 0,
                })
                
                _logger.create({
                    'name': 'Update UOM Base',
                    'level': 'INFO',
                    'message': f'อัปเดต default UOM สำหรับสินค้า: {rec.name} (ID: {rec.id}) - UOM: {rec.uom_id.name}',
                    'func': 'action_update_uom_base',
                    'line': 0,
                    'type': 'server',
                    'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
                })

    def create_update_uom_base(self):
        product_all = self.env['product.template'].search([])   
        for product in product_all:
            product.action_update_uom_base()

    def fix_existing_default_uom_data(self):
        """แก้ไขข้อมูลเดิมที่มี default UOM ซ้ำ โดยย้าย default ไปที่ base UOM"""
        # ตรวจสอบสินค้าที่เลือก (checkbox) หรือสินค้าทั้งหมดหากไม่ได้เลือก
        if self.ids:
            products = self.filtered(lambda p: p.uom_id)
        else:
            products = self.env['product.template'].search([('uom_id', '!=', False)])
        
        processed_count = 0
        created_count = 0
        
        _logger = self.env['ir.logging']
        # ตรวจสอบว่ามีสินค้าที่เลือกหรือไม่
        if not products:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'ไม่พบสินค้า',
                    'message': 'ไม่พบสินค้าที่มี UOM สำหรับแก้ไข',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        _logger.create({
            'name': 'Fix Default UOM Data',
            'level': 'INFO',
            'message': f'เริ่มต้นการแก้ไขข้อมูล Default UOM สำหรับสินค้า {len(products)} รายการ',
            'func': 'fix_existing_default_uom_data',
            'line': 0,
            'type': 'server',
            'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
        })
        
        for product in products:
            # ตรวจสอบว่ามี UOM Map หรือไม่
            if not product.uom_map_ids:
                # ถ้าไม่มี UOM Map ให้สร้าง base UOM อัตโนมัติ
                # ใช้ create โดยตรงแทน action_update_uom_base เพื่อหลีกเลี่ยง constraint
                product.env['product.uom.map'].create({
                    'product_tmpl_id': product.id,
                    'uom_id': product.uom_id.id, 
                    'uom_type': 'base',
                    'factor_base': 1.0,
                    'is_default_sale': True,
                    'is_default_purchase': True,
                    'sequence': 0,
                })
                
                _logger.create({
                    'name': 'Fix Default UOM Data',
                    'level': 'INFO',
                    'message': f'สร้าง UOM Map ใหม่สำหรับสินค้า: {product.name} (ID: {product.id}) - UOM: {product.uom_id.name}',
                    'func': 'fix_existing_default_uom_data',
                    'line': 0,
                    'type': 'server',
                    'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
                })
                
                created_count += 1
                processed_count += 1
                continue
            
            # หา base UOM ที่ตรงกับ uom_id ของสินค้า
            correct_base_uom = product.uom_map_ids.filtered(
                lambda l: l.uom_type == 'base' and l.uom_id.id == product.uom_id.id
            )
            
            # หา base UOM ทั้งหมด
            all_base_uoms = product.uom_map_ids.filtered(lambda l: l.uom_type == 'base')
            
            # ถ้ามี base UOM มากกว่า 1 รายการ ให้ลบออกทั้งหมดก่อน
            if len(all_base_uoms) > 1:
                _logger.create({
                    'name': 'Fix Default UOM Data',
                    'level': 'WARNING',
                    'message': f'พบ base UOM ซ้ำ {len(all_base_uoms)} รายการสำหรับสินค้า: {product.name} (ID: {product.id}) - กำลังลบออกทั้งหมด',
                    'func': 'fix_existing_default_uom_data',
                    'line': 0,
                    'type': 'server',
                    'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
                })
                
                all_base_uoms.unlink()
                all_base_uoms = product.uom_map_ids.filtered(lambda l: l.uom_type == 'base')
                # หลังจากลบ base UOM ซ้ำแล้ว ให้หา correct_base_uom ใหม่
                correct_base_uom = product.uom_map_ids.filtered(
                    lambda l: l.uom_type == 'base' and l.uom_id.id == product.uom_id.id
                )
            
            if not correct_base_uom:
                if all_base_uoms:
                    # ถ้ามี base UOM แต่ไม่ตรงกับ uom_id ให้อัปเดต
                    old_uom_name = all_base_uoms[0].uom_id.name
                    all_base_uoms[0].write({
                        'uom_id': product.uom_id.id,
                        'factor_base': 1.0,
                    })
                    
                    _logger.create({
                        'name': 'Fix Default UOM Data',
                        'level': 'INFO',
                        'message': f'อัปเดต base UOM สำหรับสินค้า: {product.name} (ID: {product.id}) - เปลี่ยนจาก {old_uom_name} เป็น {product.uom_id.name}',
                        'func': 'fix_existing_default_uom_data',
                        'line': 0,
                        'type': 'server',
                        'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
                    })
                    
                    correct_base_uom = all_base_uoms[0]
                else:
                    # ถ้าไม่มี base UOM เลย ให้สร้างใหม่
                    # ใช้ create โดยตรงแทน action_update_uom_base เพื่อหลีกเลี่ยง constraint
                    product.env['product.uom.map'].create({
                        'product_tmpl_id': product.id,
                        'uom_id': product.uom_id.id, 
                        'uom_type': 'base',
                        'factor_base': 1.0,
                        'is_default_sale': True,
                        'is_default_purchase': True,
                        'sequence': 0,
                    })
                    
                    _logger.create({
                        'name': 'Fix Default UOM Data',
                        'level': 'INFO',
                        'message': f'สร้าง base UOM ใหม่สำหรับสินค้า: {product.name} (ID: {product.id}) - UOM: {product.uom_id.name}',
                        'func': 'fix_existing_default_uom_data',
                        'line': 0,
                        'type': 'server',
                        'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
                    })
                    
                    correct_base_uom = product.uom_map_ids.filtered(
                        lambda l: l.uom_type == 'base' and l.uom_id.id == product.uom_id.id
                    )
                    created_count += 1
            
            if correct_base_uom:
                # ยกเลิก default sale ทั้งหมดก่อน
                product.uom_map_ids.write({'is_default_sale': False})
                # ตั้ง default sale ให้ base UOM ที่ถูกต้อง
                correct_base_uom[0].write({'is_default_sale': True})
                
                # ยกเลิก default purchase ทั้งหมดก่อน
                product.uom_map_ids.write({'is_default_purchase': False})
                # ตั้ง default purchase ให้ base UOM ที่ถูกต้อง
                correct_base_uom[0].write({'is_default_purchase': True})
                
                # ตั้ง sequence ให้ base UOM เป็น 0 (ลำดับแรก)
                correct_base_uom[0].write({'sequence': 0})
                
                _logger.create({
                    'name': 'Fix Default UOM Data',
                    'level': 'INFO',
                    'message': f'ตั้ง default UOM สำหรับสินค้า: {product.name} (ID: {product.id}) - UOM: {correct_base_uom[0].uom_id.name} (Base UOM)',
                    'func': 'fix_existing_default_uom_data',
                    'line': 0,
                    'type': 'server',
                    'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
                })
                
                processed_count += 1
        
        message = f"แก้ไขข้อมูล default UOM เรียบร้อยแล้ว\n"
        message += f"- สินค้าที่แก้ไข: {processed_count} รายการ\n"
        message += f"- สินค้าที่สร้าง UOM Map ใหม่: {created_count} รายการ"
        
        _logger.create({
            'name': 'Fix Default UOM Data',
            'level': 'INFO',
            'message': f'เสร็จสิ้นการแก้ไขข้อมูล Default UOM - สินค้าที่แก้ไข: {processed_count} รายการ, สินค้าที่สร้าง UOM Map ใหม่: {created_count} รายการ',
            'func': 'fix_existing_default_uom_data',
            'line': 0,
            'type': 'server',
            'path': 'modules/hdc/hdc_convert_prod_uom/model/product.py',
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'สำเร็จ',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_fix_default_uom_batch(self):
        """Batch action สำหรับแก้ไข default UOM หลายสินค้าพร้อมกัน"""
        return self.fix_existing_default_uom_data()

    def check_default_uom_issues(self):
        """ตรวจสอบข้อมูล default UOM ที่มีปัญหา"""
        issues = []
        products = self.env['product.template'].search([('uom_id', '!=', False)])
        total_products = len(products)
        products_with_uom_map = 0
        products_without_uom_map = 0
        
        for product in products:
            product_issues = []
            
            # ตรวจสอบว่ามี UOM Map หรือไม่
            if not product.uom_map_ids:
                product_issues.append("ไม่มี UOM Map")
                products_without_uom_map += 1
            else:
                products_with_uom_map += 1
                
                # ตรวจสอบ default sale ซ้ำ
                default_sale_maps = product.uom_map_ids.filtered(lambda l: l.is_default_sale)
                if len(default_sale_maps) > 1:
                    product_issues.append(f"มี Default Sale ซ้ำ {len(default_sale_maps)} รายการ")
                
                # ตรวจสอบ default purchase ซ้ำ
                default_purchase_maps = product.uom_map_ids.filtered(lambda l: l.is_default_purchase)
                if len(default_purchase_maps) > 1:
                    product_issues.append(f"มี Default Purchase ซ้ำ {len(default_purchase_maps)} รายการ")
                
                # ตรวจสอบ base UOM
                base_uom_maps = product.uom_map_ids.filtered(lambda l: l.uom_type == 'base')
                if not base_uom_maps:
                    product_issues.append("ไม่มี Base UOM")
                else:
                    # ตรวจสอบ base UOM ตรงกับ uom_id หรือไม่
                    correct_base_uom = base_uom_maps.filtered(
                        lambda l: l.uom_id.id == product.uom_id.id
                    )
                    if not correct_base_uom:
                        product_issues.append("Base UOM ไม่ตรงกับ Unit of Measure")
            
            if product_issues:
                issues.append(f"สินค้า: {product.name} - {', '.join(product_issues)}")
        
        # สร้างรายงานสรุป
        message = f"ผลการตรวจสอบ Default UOM:\n"
        message += f"- สินค้าทั้งหมด: {total_products} รายการ\n"
        message += f"- มี UOM Map: {products_with_uom_map} รายการ\n"
        message += f"- ไม่มี UOM Map: {products_without_uom_map} รายการ\n"
        message += f"- มีปัญหา: {len(issues)} รายการ\n"
        
        if issues:
            message += "\nรายละเอียดปัญหา:\n" + "\n".join(issues[:10])  # แสดงแค่ 10 รายการแรก
            if len(issues) > 10:
                message += f"\n... และอีก {len(issues) - 10} รายการ"
        else:
            message += "\nไม่พบปัญหาข้อมูล Default UOM"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'ผลการตรวจสอบ',
                'message': message,
                'type': 'info' if issues else 'success',
                'sticky': True,
            }
        }

    @api.model
    def create(self, vals):
        """Override create method to automatically create base UOM when creating new product"""
        # สร้างสินค้าใหม่ก่อน
        product = super(ProductTemplate, self).create(vals)
        
        # ตรวจสอบว่ามี base UOM อยู่แล้วหรือไม่
        has_base_uom = product.uom_map_ids.filtered(lambda l: l.uom_type == 'base')
        
        # ถ้าไม่มี base UOM และมี uom_id ให้สร้าง base UOM อัตโนมัติ
        if not has_base_uom and product.uom_id:
            product.action_update_uom_base()
            
        return product
            
class ProductUomMap(models.Model):
    _name = "product.uom.map"
    _description = "Product UOM Map"

    product_tmpl_id = fields.Many2one(
        "product.template", string="Product Template", ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", string="Product", compute="_compute_product_id", store=True)
    uom_id = fields.Many2one("uom.uom", string="UoM")
    factor_base = fields.Float(string="Factor Base", digits=(12, 2))
    uom_type = fields.Selection(
        [
            ("none", ""),
            ("base", "Base"),
            ("both", "Both"),
        ],
        string="UoM Type",
        default="none",
    )
    is_default_sale = fields.Boolean(string="Is Default Sale")
    is_default_purchase = fields.Boolean(string="Is Default Purchase")
    sequence = fields.Integer(string="Sequence", default=10)

    @api.depends('product_tmpl_id')
    def _compute_product_id(self):
        for record in self:
            if record.product_tmpl_id and record.product_tmpl_id.product_variant_ids:
                record.product_id = record.product_tmpl_id.product_variant_ids[0].id
            else:
                record.product_id = False

    @api.onchange('is_default_sale')
    def _onchange_is_default_sale(self):
        """เมื่อเลือก is_default_sale ให้ตั้ง sequence เป็น 0 เพื่อแสดงเป็นลำดับแรก"""
        if self.is_default_sale:
            self.sequence = 0

    @api.onchange('is_default_purchase')
    def _onchange_is_default_purchase(self):
        """เมื่อเลือก is_default_purchase ให้ตั้ง sequence เป็น 0 เพื่อแสดงเป็นลำดับแรก"""
        if self.is_default_purchase:
            self.sequence = 0

    @api.constrains("product_tmpl_id", "uom_type", "uom_id", "is_default_sale", "is_default_purchase")
    def _check_uom_map_constraints(self):
        for rec in self:

            # product_id จะถูกกำหนดโดยอัตโนมัติจาก product_tmpl_id
            # ไม่ต้องตรวจสอบ product_id อีกต่อไป

            if rec.uom_type == "base":
                base_lines = self.search(
                    [
                        ("product_tmpl_id", "=", rec.product_tmpl_id.id),
                        ("uom_type", "=", "base"),
                    ]
                )
                if len(base_lines) > 1:  # เจอ base > 1
                    raise ValidationError(_("Can use 'Base' only 1 value."))

                if (
                    rec.product_tmpl_id.uom_id
                    and rec.uom_id != rec.product_tmpl_id.uom_id
                ):
                    raise ValidationError(
                        _("Set UoM value same main product when set value 'Base'.")
                    )

            # ตรวจสอบและแก้ไข is_default_sale ซ้ำอัตโนมัติ
            if rec.is_default_sale:
                default_sale_lines = self.search(
                    [
                        ("product_tmpl_id", "=", rec.product_tmpl_id.id),
                        ("is_default_sale", "=", True),
                        ("id", "!=", rec.id),
                    ]
                )
                if default_sale_lines:
                    # ยกเลิก default sale ที่ซ้ำ
                    default_sale_lines.write({'is_default_sale': False})

            # ตรวจสอบและแก้ไข is_default_purchase ซ้ำอัตโนมัติ
            if rec.is_default_purchase:
                default_purchase_lines = self.search(
                    [
                        ("product_tmpl_id", "=", rec.product_tmpl_id.id),
                        ("is_default_purchase", "=", True),
                        ("id", "!=", rec.id),
                    ]
                )
                if default_purchase_lines:
                    # ยกเลิก default purchase ที่ซ้ำ
                    default_purchase_lines.write({'is_default_purchase': False})
