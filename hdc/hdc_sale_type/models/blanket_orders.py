
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"


    sale_type_id = fields.Many2one(comodel_name="sale.order.type", string="Sale Type")

    is_below_cost = fields.Boolean(string="Is below cost", default=False)

    is_confirm_below_cost = fields.Boolean(
        string="Is confirm below cost", default=False, copy=False
    )

    def action_confirm(self):
        # if not (self.sale_type_id.inter_company_transactions or self.sale_type_id.is_retail):
        #     if self.delivery_trl:
        #         if not self.delivery_trl_description:
        #             raise ValidationError(_("กรุณาระบุรายละเอียดของ สายส่ง TRL"))
        #     elif self.delivery_company:
        #         if not self.delivery_company_description:
        #             raise ValidationError(_("กรุณาระบุรายละเอียดของ Mode of Delivery"))
        #     else:
        #         raise ValidationError(_("กรุณาระบุสายส่ง TRL หรือ Mode of Delivery"))


        list_warning_below_cost = []

        for line in self.line_ids:

            in_pricelist = self.env["product.pricelist.item"].search(
                            [
                                ("pricelist_id", "=", self.pricelist_id.id),
                                ("product_tmpl_id", "=", line.product_id.product_tmpl_id.id),
                            ], limit=1
                        )
            
            if not self.pricelist_id.approve_below_cost:
                if not self.sale_type_id.below_cost:
                    if not line.product_id.product_tmpl_id.below_cost:
                        if line.product_id.product_tmpl_id.type != "service":

                            fixed_price = line.price_unit
                            cost_price = in_pricelist.pricelist_cost_price or line.product_id.product_tmpl_id.standard_price

                            if cost_price > fixed_price:
                                list_warning_below_cost.append({'product':line.product_id.name, 'price': fixed_price, 'cost': cost_price})

        if list_warning_below_cost:
            if not self.is_confirm_below_cost:    
                return self.show_below_cost_warning_wizard(list_warning_below_cost)
            else:
                return super(BlanketOrder, self).action_confirm()
        else:
            return super(BlanketOrder, self).action_confirm()

    def set_to_draft(self):
        self.is_confirm_below_cost = False
        return super(BlanketOrder, self).set_to_draft()

    def show_below_cost_warning_wizard(self, list_warning_below_cost=[]):

        messages = []

        for list in list_warning_below_cost:

            line_message = f"{list['product']}, price: {list['price']}, cost: {list['cost']}"
            messages.append(line_message)

        message = "Your order has found selling price below cost. \n" + "\n".join(
            messages
        )

        return {
            "name": _("Below Cost Warning"),
            "type": "ir.actions.act_window",
            "res_model": "agreement.below.cost.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_agreement_id": self.id,
                "default_message": message,
            },
        }
        

    @api.depends('team_id')
    def _get_sale_type_domain(self):
        domain = []
        print(self.team_id)
        if self.team_id:
            domain = [('team_ids', 'in', self.team_id.id)]
        return domain

    @api.onchange('team_id')
    def _onchange_team_id(self):
        pass
        # 15/11/2024 มีสร้าง _domain_sale_type_id มาใช้แทน
        # if self.team_id:
        #     if self.team_id.sale_type_ids:
        #         self.sale_type_id = self.team_id.sale_type_ids[0].id
        #     else:
        #         self.sale_type_id = False
        # else:
        #     self.sale_type_id = False

        # for rec in self:
        #     return {'domain': {'sale_type_id': [('team_ids', 'in', rec.team_id.id)]}}
        
    # @api.onchange("team_id")
    # def _domain_sale_type_id(self):
    #     if self.team_id:
    #         return {
    #             "domain": {"sale_type_id": [("id", "in", self.team_id.sale_type_ids.ids), ("company_id", "=", self.company_id.id)]}
    #         }
    #     else:
    #         return {"domain": {"sale_type_id": []}}
        