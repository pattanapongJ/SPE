from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import base64
import xlrd
from pytz import timezone

class PricelistUpdate(models.Model):
    _name = "pricelist.update"
    _description = "Pricelist Update"

    name = fields.Char(string="Name")

    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist Name ID")

    item_ids_line = fields.One2many(
        "pricelist.update.line",
        "product_update_id",
        string="Pricelist Items Line",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        readonly=True,
        related="pricelist_id.company_id",
        store=True,
    )

    import_pricelist = fields.Binary(string="Import")
    file_name_import = fields.Char(string="File Name")

    issue_date = fields.Datetime(string="Issue Date", default=fields.Datetime.now)

    responsible = fields.Many2one(
        "res.users", string="Responsible", default=lambda self: self.env.user
    )

    state = fields.Selection(
        [("draft", "Draft"), ("confirm", "Confirm")],
        string="Status",
        default="draft",
    )

    def copy(self, default=None):

        today = datetime.today()

        self.issue_date = today

        return super(PricelistUpdate, self).copy(default)

    def action_update_today(self):
        bangkok_tz = timezone("Asia/Bangkok")
        today = datetime.now(bangkok_tz).date()
        item_today = self.item_ids_line.filtered(lambda m: m.schedule_action == False
                                                and m.date_start.astimezone(bangkok_tz).date() == today)

        for record in item_today:
            pricelist_items = self.env["product.pricelist.item"].search(
                [("product_tmpl_id", "=", record.product_tmpl_id.id),
                    ("pricelist_id", "=", self.pricelist_id.id)])
            if pricelist_items:
                for item_pricelist in pricelist_items:
                    item_pricelist.write({
                        "min_quantity": record.min_quantity, "fixed_price": record.update_price,
                        "date_start": record.date_start, "date_end": record.date_end,
                        "triple_discount": record.triple_discount,
                        "remark": record.remark,
                        })

            record.write({"schedule_action": True})


    def action_pricelist_update(self):
        date_today = datetime.today().date()

        pricelist_update_all = self.env["pricelist.update.line"].search([("product_update_id.state", "=", "confirm"),
                                                                         ("schedule_action", "=", False),
                                                                         ("date_start", "<=", datetime.now())])

        for record in pricelist_update_all:
            pricelist_items = self.env["product.pricelist.item"].search(
                [("product_tmpl_id","=",record.product_tmpl_id.id),
                 ("pricelist_id","=",record.product_update_id.pricelist_id.id)])

            if pricelist_items:
                for item_pricelist in pricelist_items:
                    item_pricelist.write(
                        {
                            "min_quantity": record.min_quantity,
                            "fixed_price": record.update_price,
                            "date_start": record.date_start,
                            "date_end": record.date_end,
                        }
                    )

            record.write({"schedule_action": True})

    def action_confirm(self):

        product_templ = self.env["product.pricelist.item"].search(
            [(("pricelist_id", "=", self.pricelist_id.id))]
        )

        product_templ_ids = product_templ.product_tmpl_id.ids
        product_templ_line_ids = self.item_ids_line.product_tmpl_id.ids

        is_inside = set(product_templ_line_ids).issubset(set(product_templ_ids))

        if not is_inside:

            missing_product_templ_ids = set(product_templ_line_ids) - set(
                product_templ_ids
            )

            missing_list = []

            for tmpl_id in missing_product_templ_ids:
                missing_record = self.env["product.template"].browse(tmpl_id)
                missing_list.append(missing_record.name)

            missing_message_lines = [
                f"{idx + 1}) {error}" for idx, error in enumerate(missing_list)
            ]

            missing_message = "Product that not in pricelist is:\n" + "\n".join(
                missing_message_lines
            )

            raise UserError(missing_message)

        else:
            self.state = "confirm"

    @api.onchange("file_name_import")
    def _onchange_file_name_import(self):

        if self.file_name_import:
            file_name = self.file_name_import.lower()
            if not (file_name.endswith(".xls") or file_name.endswith(".xlsx")):
                raise UserError("Please upload only .xls or .xlsx")

    @api.constrains("item_ids_line")
    def _constrains_item_ids(self):

        bangkok_tz = timezone("Asia/Bangkok")
        today = datetime.now(bangkok_tz).date()

        keep_date_error = []
        for item in self.item_ids_line:
            item_date_start = item.date_start.astimezone(bangkok_tz).date()
            if item_date_start < today:

                product_date_error = item.product_tmpl_id.name

                keep_date_error.append(product_date_error)

        if keep_date_error:
            date_error_line = [
                f"{idx+1}) {error}" for idx, error in enumerate(keep_date_error)
            ]

            date_error_message = (
                "Please check the start date cannot less than the current date:\n"
                + "\n".join(date_error_line)
            )
            raise UserError(date_error_message)

    #################### Import File Excel ###########################

    def action_clear_all(self):
        self.import_pricelist = False
        self.item_ids_line = [(5, 0, 0)]

    def action_import_serial(self):

        if self.import_pricelist:
            self.item_ids_line = [(5, 0, 0)]

            record_data = base64.b64decode(self.import_pricelist)
            cols_internal_ref = 0  # field column
            cols_product = 1  # field column
            cols_min_quantity = 2  # field column
            cols_price = 3  # field column
            cols_start_date = 4  # field column
            cols_end_date = 5  # field column
            cols_uom = 6 # field column

            wb = xlrd.open_workbook(file_contents=record_data)

            keep_list_error = []

            keep_list_start_date_error = []

            today = datetime.today() + timedelta(hours=7)

            for sheet in wb.sheets():
                for row in range(sheet.nrows):
                    if row > 0:
                        cols_internal_ref_value = sheet.cell(
                            row, cols_internal_ref
                        ).value
                        cols_internal_ref_value = cols_internal_ref_value.strip()

                        cols_uom_value = sheet.cell(
                            row, cols_uom
                        ).value
                        cols_uom_value = cols_uom_value.strip()

                        cols_product_value = sheet.cell(row, cols_product).value
                        cols_min_quantity_value = sheet.cell(
                            row, cols_min_quantity
                        ).value
                        cols_price_value = sheet.cell(row, cols_price).value
                        cols_start_date_value = sheet.cell(row, cols_start_date).value
                        cols_end_date_value = sheet.cell(row, cols_end_date).value

                        try:

                            # Check Type Date ใหม่ ####################
                            # !!!!! print date-time is correct but in odoo will -7 hr

                            start_time_obj = datetime.strptime(
                                cols_start_date_value, "%d/%m/%Y %H:%M:%S"
                            ) - timedelta(hours=7)

                            start_time_obj_calc = datetime.strptime(
                                cols_start_date_value, "%d/%m/%Y %H:%M:%S"
                            )

                            if cols_end_date_value:
                                end_time_obj = datetime.strptime(
                                    cols_end_date_value, "%d/%m/%Y %H:%M:%S"
                                ) - timedelta(hours=7)
                                end_time_obj_calc = datetime.strptime(
                                    cols_end_date_value, "%d/%m/%Y %H:%M:%S"
                                )
                            else:
                                end_time_obj = False
                                end_time_obj_calc = False

                            start_time_value = fields.Datetime.to_string(start_time_obj)
                            end_time_value = fields.Datetime.to_string(end_time_obj)

                            if start_time_obj_calc < today:
                                keep_list_start_date_error.append(cols_product_value)
                                continue

                            check_default_code = self.env["product.template"].search(
                                [(("default_code", "=", cols_internal_ref_value))]
                            )
                            uom_id = self.env["uom.uom"].search([("name", "=", cols_uom_value)], limit=1)
                            if not cols_uom_value:
                                keep_list_start_date_error.append("not uom product %s"%str(cols_product_value))
                                continue

                            item_ids_line_vals = []

                            for product in check_default_code:

                                find_current_price = self.env[
                                    "product.pricelist.item"
                                ].search(
                                    [
                                        ("pricelist_id", "=", self.pricelist_id.id),
                                        ("product_tmpl_id", "=", product.id),
                                        ("product_uom_id", "=", uom_id.id),
                                    ]
                                )

                                if find_current_price:
                                    current_price = find_current_price.fixed_price
                                else:
                                    current_price = 0

                                item_ids_line_vals.append(
                                    (
                                        0,
                                        0,
                                        {
                                            "default_code": cols_internal_ref_value,
                                            "product_tmpl_id": product.id,
                                            "min_quantity": cols_min_quantity_value,
                                            "price": current_price,
                                            "update_price": cols_price_value,
                                            "date_start": start_time_value,
                                            "date_end": end_time_value,
                                            "triple_discount": find_current_price.triple_discount if find_current_price else "",
                                            "remark": find_current_price.remark if find_current_price else "",
                                        },
                                    )
                                )

                            self.write({"item_ids_line": item_ids_line_vals})

                        except Exception as e:
                            keep_list_error.append(e)

                        ################ ########### ########################

            if keep_list_start_date_error:
                text_error_lines = [
                    f"{idx + 1}) {error}"
                    for idx, error in enumerate(keep_list_start_date_error)
                ]
                text_error = (
                    f"Please check the start date cannot less than the current date:\n"
                    + "\n".join(text_error_lines)
                )
                raise UserError(text_error)

            if keep_list_error:
                text_error_lines = [
                    f"{idx + 1}) {error}" for idx, error in enumerate(keep_list_error)
                ]
                text_error = f"Found Date Error From Product:\n" + "\n".join(
                    text_error_lines
                )
                raise UserError(text_error)

        else:
            raise ValidationError(_("กรุณาอัพโหลดไฟล์ก่อน Import"))

    #################### ################ ###########################


class PricelistUpdateLine(models.Model):
    _name = "pricelist.update.line"
    _description = "Pricelist Update Line"

    product_update_id = fields.Many2one("pricelist.update", string="Pricelist Update")
    issue_date = fields.Datetime(related="product_update_id.issue_date",string="Issue Date")
    pricelist_id = fields.Many2one(related="product_update_id.pricelist_id", string="Pricelist", store=True)
    product_tmpl_id = fields.Many2one("product.template", string="Product")

    # name = fields.Char(string="Product")
    min_quantity = fields.Float(string="Min. Quantity")
    price = fields.Float(string="Current Price")
    date_start = fields.Datetime(string="Date Start")
    date_end = fields.Datetime(string="Date End")
    update_price = fields.Float(string="Update Price")
    default_code = fields.Char(string="Internal Reference")
    schedule_action = fields.Boolean(string="Schedule Action", default=False)
    triple_discount = fields.Char(string="Triple Discount")
    remark = fields.Char(string="Remark")

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        if self.product_tmpl_id:
            find_current_price = self.env["product.pricelist.item"].search(
                [
                    ("product_tmpl_id", "=", self.product_tmpl_id.id),
                    ("pricelist_id", "=", self.product_update_id.pricelist_id.id),
                ]
            )

            if find_current_price:
                for product in find_current_price:
                    self.price = product.fixed_price
                    self.min_quantity = product.min_quantity
                    self.remark = product.remark
                    self.triple_discount = product.triple_discount
            else:
                raise UserError("Product that not in pricelist")
