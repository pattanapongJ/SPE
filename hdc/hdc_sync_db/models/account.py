# -*- coding: utf-8 -*-
import requests
import http.client
import json
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import xmlrpc.client
from odoo.api import call_kw
from datetime import datetime
import ast

class AccountMove(models.Model):
    _inherit = "account.move"

    sync_db = fields.Boolean('Sync DB', copy=False, default=False)
    sync_id = fields.Integer(string="sync order id", copy=False)

    def value_get_json(self,lines_value, one_many_value, endpoint_url, headers):
        model_fields = self.env['ir.model.fields'].search([('model', '=', one_many_value)])

        vaule = []
        for lines in lines_value:
            field_obj = {}
            for f_var in model_fields:
                if f_var.ttype == "binary":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "boolean":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "char":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "date":
                    val_date = getattr(lines, f_var.name, None)
                    if val_date:
                        formatted_date = val_date.strftime("%Y-%m-%d %H:%M:%S")
                        f_data = {"%s"%f_var.name: formatted_date}
                elif f_var.ttype == "datetime":
                    val_date = getattr(lines, f_var.name, None)
                    if val_date:
                        formatted_date = val_date.strftime("%Y-%m-%d %H:%M:%S")
                        f_data = {"%s"%f_var.name: formatted_date}
                elif f_var.ttype == "float":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "html":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "integer":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "many2many":
                    many2many_vals = []
                    model_val = getattr(lines, f_var.name, None)
                    if model_val:
                        for model_line in model_val:
                            xml_id = model_val.get_xml_id().get(model_line.id)
                            if xml_id:
                                url = "%s/ir.model.data?fields[ir.model.data]=complete_name,res_id&filter=[('model', '=', '%s')]"%(
                                    str(endpoint_url), f_var.relation)
                                response = requests.request("GET", url, headers = headers, data = {})
                                data = response.json()
                                res_id = next((item["attributes"]["res_id"] for item in data.get("data") if
                                               item["attributes"]["complete_name"] == xml_id), None)
                                if res_id:
                                    many2many_vals.append((4, res_id))

                        f_data = {"%s"%f_var.name: many2many_vals}

                elif f_var.ttype == "many2one":
                    model_val = getattr(lines, f_var.name, None)
                    if model_val:
                        xml_id = model_val.get_xml_id().get(model_val.id)
                        if xml_id:
                            url = "%s/ir.model.data?fields[ir.model.data]=complete_name,res_id&filter=[('model', '=', '%s')]"%(
                                str(endpoint_url), f_var.relation)
                            response = requests.request("GET", url, headers = headers, data = {})
                            data = response.json()
                            res_id = next((item["attributes"]["res_id"] for item in data.get("data") if
                                           item["attributes"]["complete_name"] == xml_id), None)
                            if res_id:
                                f_data = {"%s"%f_var.name: res_id}
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue

                elif f_var.ttype == "boolean":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}

                elif f_var.ttype == "many2one_reference":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}

                elif f_var.ttype == "monetary":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "one2many":
                    if getattr(lines, f_var.name, None):
                        one2many_vals = self.value_get_json(getattr(lines, f_var.name, None), f_var.relation, endpoint_url, headers)
                        f_data = {"%s"%f_var.name: one2many_vals}
                elif f_var.ttype == "reference":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "selection":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                else:
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}  # field_type == text
                field_obj.update(f_data)
            vaule.append((0, 0, field_obj))
        return vaule

    def action_post(self):
        result = super(AccountMove, self).action_post()
        if self.state == "posted" and self.sync_db == False:
            # เพิ่ม state ที่เป็น connect ด้วย
            app_list = self.env['sync.app.list'].search([('invoice', '=', True)])
            json_data = {}
            for list in app_list:
                invoice_domain = list.invoice_domain
                if not invoice_domain:
                    invoice_domain = "[]"
                tuple_obj = ast.literal_eval(invoice_domain)
                invoice_domain_ids = self.search(tuple_obj).ids
                if self.id in invoice_domain_ids:
                    headers = {
                        'Content-Type': 'application/vnd.api+json', 'x-api-key': list.apikey, 'DB': list.instance_db
                        }
                    f_data = {}
                    for f_var in list.invoice_ids.filtered(lambda m: m.sync == True):
                        if f_var.field_type == "binary":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}
                        elif f_var.field_type == "boolean":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}
                        elif f_var.field_type == "char":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}
                        elif f_var.field_type == "date":
                            val_date = getattr(self, f_var.field_name, None)
                            if val_date:
                                formatted_date = val_date.strftime("%Y-%m-%d %H:%M:%S")
                                f_data = {"%s"%f_var.field_name : formatted_date}
                        elif f_var.field_type == "datetime":
                            val_date = getattr(self, f_var.field_name, None)
                            if val_date:
                                formatted_date = val_date.strftime("%Y-%m-%d %H:%M:%S")
                                f_data = {"%s"%f_var.field_name : formatted_date}
                        elif f_var.field_type == "float":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}
                        elif f_var.field_type == "html":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}
                        elif f_var.field_type == "integer":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}
                        elif f_var.field_type == "many2many":
                            many2many_vals = []
                            model_val = getattr(self, f_var.field_name, None)
                            if model_val:
                                for model_line in model_val:
                                    xml_id = model_val.get_xml_id().get(model_line.id)
                                    if xml_id:
                                        url = "%s/ir.model.data?fields[ir.model.data]=complete_name,res_id&filter=[('model', '=', '%s')]"%(
                                            str(list.endpoint_url), f_var.field_id.relation)
                                        response = requests.request("GET", url, headers = headers, data = {})
                                        data = response.json()
                                        res_id = next((item["attributes"]["res_id"] for item in data.get("data") if
                                                       item["attributes"]["complete_name"] == xml_id), None)
                                        if res_id:
                                            many2many_vals.append((4, res_id))

                                f_data = {"%s"%f_var.field_name : many2many_vals}

                        elif f_var.field_type == "many2one":
                            model_val = getattr(self, f_var.field_name, None)
                            if model_val:
                                xml_id = model_val.get_xml_id().get(model_val.id)
                                if xml_id:
                                    url = "%s/ir.model.data?fields[ir.model.data]=complete_name,res_id&filter=[('model', '=', '%s')]"%(
                                    str(list.endpoint_url), f_var.field_id.relation)
                                    response = requests.request("GET", url, headers = headers, data = {})
                                    data = response.json()
                                    res_id = next((item["attributes"]["res_id"] for item in data.get("data") if
                                                   item["attributes"]["complete_name"] == xml_id), None)
                                    if res_id:
                                        f_data = {"%s"%f_var.field_name : res_id}
                                    else:
                                        continue
                                else:
                                    continue
                            else:
                                continue
                        elif f_var.field_type == "boolean":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}

                        elif f_var.field_type == "many2one_reference":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}

                        elif f_var.field_type == "monetary":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}
                        elif f_var.field_type == "one2many":
                            if getattr(self, f_var.field_name, None):
                                one2many_vals = self.value_get_json(getattr(self, f_var.field_name, None),f_var.field_id.relation, list.endpoint_url, headers)
                                f_data = {"%s"%f_var.field_name: one2many_vals}
                        elif f_var.field_type == "reference":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}
                        elif f_var.field_type == "selection":
                            f_data = {"%s"%f_var.field_name : getattr(self, f_var.field_name, None)}
                        else:
                            f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                        print("========================",f_var.field_name, f_data)
                        json_data.update(f_data)

                    url = "%s/sync.db.order" %str(list.endpoint_url)
                    payload = json.dumps({
                        "data": {
                            "type": "sync.db.order",
                            "attributes": {
                                "name": self.name,
                                "type": "invoice",
                                "json_data": json.dumps(json_data)
                                }
                            }
                        })

                    response = requests.request("POST", url, headers = headers, data = payload)
                    sync_value = response.json()
                    self.sync_id = sync_value.get("data").get('id')
                    print('-------------response.json', response.json())
                # self.sync_db == True
        return result

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    sync_account_id = fields.Many2one('account.move', string = 'Sync Invoices')

    def value_get_json(self, lines_value, one_many_value, endpoint_url, headers):
        model_fields = self.env['ir.model.fields'].search([('model', '=', one_many_value)])

        vaule = []
        for lines in lines_value:
            field_obj = {}
            for f_var in model_fields:
                if f_var.ttype == "binary":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "boolean":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "char":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "date":
                    val_date = getattr(lines, f_var.name, None)
                    if val_date:
                        formatted_date = val_date.strftime("%Y-%m-%d %H:%M:%S")
                        f_data = {"%s"%f_var.name: formatted_date}
                elif f_var.ttype == "datetime":
                    val_date = getattr(lines, f_var.name, None)
                    if val_date:
                        formatted_date = val_date.strftime("%Y-%m-%d %H:%M:%S")
                        f_data = {"%s"%f_var.name: formatted_date}
                elif f_var.ttype == "float":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "html":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "integer":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "many2many":
                    many2many_vals = []
                    model_val = getattr(lines, f_var.name, None)
                    if model_val:
                        for model_line in model_val:
                            xml_id = model_val.get_xml_id().get(model_line.id)
                            if xml_id:
                                url = "%s/ir.model.data?fields[ir.model.data]=complete_name,res_id&filter=[('model', '=', '%s')]"%(
                                    str(endpoint_url), f_var.relation)
                                response = requests.request("GET", url, headers = headers, data = {})
                                data = response.json()
                                res_id = next((item["attributes"]["res_id"] for item in data.get("data") if
                                               item["attributes"]["complete_name"] == xml_id), None)
                                if res_id:
                                    many2many_vals.append((4, res_id))

                        f_data = {"%s"%f_var.name: many2many_vals}

                elif f_var.ttype == "many2one":
                    model_val = getattr(lines, f_var.name, None)
                    if model_val:
                        xml_id = model_val.get_xml_id().get(model_val.id)
                        if xml_id:
                            url = "%s/ir.model.data?fields[ir.model.data]=complete_name,res_id&filter=[('model', '=', '%s')]"%(
                                str(endpoint_url), f_var.relation)
                            response = requests.request("GET", url, headers = headers, data = {})
                            data = response.json()
                            res_id = next((item["attributes"]["res_id"] for item in data.get("data") if
                                           item["attributes"]["complete_name"] == xml_id), None)
                            if res_id:
                                f_data = {"%s"%f_var.name: res_id}
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue

                elif f_var.ttype == "boolean":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}

                elif f_var.ttype == "many2one_reference":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}

                elif f_var.ttype == "monetary":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "one2many":
                    if getattr(lines, f_var.name, None):
                        one2many_vals = self.value_get_json(getattr(lines, f_var.name, None), f_var.relation,
                                                            endpoint_url, headers)
                        f_data = {"%s"%f_var.name: one2many_vals}
                elif f_var.ttype == "reference":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                elif f_var.ttype == "selection":
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}
                else:
                    f_data = {"%s"%f_var.name: getattr(lines, f_var.name, None)}  # field_type == text
                field_obj.update(f_data)
            vaule.append((0, 0, field_obj))
        return vaule

    def action_create_payments(self):
        self.sync_account_id = self._context.get('active_ids', [])[0]
        payments = self._create_payments()

        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action


    def _create_payments(self):
        result = super(AccountPaymentRegister, self)._create_payments()
        # เพิ่ม state ที่เป็น connect ด้วย
        app_list = self.env['sync.app.list'].search([('payment', '=', True)])
        json_data = {}
        for list in app_list:
            payment_domain = list.payment_domain
            if not payment_domain:
                payment_domain = "[]"
            tuple_obj = ast.literal_eval(payment_domain)
            payment_domain_ids = self.search(tuple_obj).ids
            if self.id in payment_domain_ids:
                headers = {
                    'Content-Type': 'application/vnd.api+json', 'x-api-key': list.apikey, 'DB': list.instance_db
                    }

                for f_var in list.payment_ids.filtered(lambda m: m.sync == True):
                    if f_var.field_name == "line_ids":
                        continue
                    if f_var.field_type == "binary":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                    elif f_var.field_type == "boolean":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                    elif f_var.field_type == "char":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                    elif f_var.field_type == "date":
                        val_date = getattr(self, f_var.field_name, None)
                        if val_date:
                            formatted_date = val_date.strftime("%Y-%m-%d %H:%M:%S")
                            f_data = {"%s"%f_var.field_name: formatted_date}
                    elif f_var.field_type == "datetime":
                        val_date = getattr(self, f_var.field_name, None)
                        if val_date:
                            formatted_date = val_date.strftime("%Y-%m-%d %H:%M:%S")
                            f_data = {"%s"%f_var.field_name: formatted_date}
                    elif f_var.field_type == "float":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                    elif f_var.field_type == "html":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                    elif f_var.field_type == "integer":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                    elif f_var.field_type == "many2many":
                        many2many_vals = []
                        model_val = getattr(self, f_var.field_name, None)
                        if model_val:
                            for model_line in model_val:
                                xml_id = model_val.get_xml_id().get(model_line.id)
                                if xml_id:
                                    url = "%s/ir.model.data?fields[ir.model.data]=complete_name,res_id&filter=[('model', '=', '%s')]"%(
                                        str(list.endpoint_url), f_var.field_id.relation)
                                    response = requests.request("GET", url, headers = headers, data = {})
                                    data = response.json()
                                    res_id = next((item["attributes"]["res_id"] for item in data.get("data") if
                                                   item["attributes"]["complete_name"] == xml_id), None)
                                    if res_id:
                                        many2many_vals.append((4, res_id))

                            f_data = {"%s"%f_var.field_name: many2many_vals}

                    elif f_var.field_type == "many2one":
                        model_val = getattr(self, f_var.field_name, None)
                        if model_val:
                            xml_id = model_val.get_xml_id().get(model_val.id)
                            if xml_id:
                                url = "%s/ir.model.data?fields[ir.model.data]=complete_name,res_id&filter=[('model', '=', '%s')]"%(
                                    str(list.endpoint_url), f_var.field_id.relation)
                                response = requests.request("GET", url, headers = headers, data = {})
                                data = response.json()
                                res_id = next((item["attributes"]["res_id"] for item in data.get("data") if
                                               item["attributes"]["complete_name"] == xml_id), None)
                                if res_id:
                                    f_data = {"%s"%f_var.field_name: res_id}
                                else:
                                    continue
                            else:
                                continue
                        else:
                            continue

                    elif f_var.field_type == "boolean":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}

                    elif f_var.field_type == "many2one_reference":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}

                    elif f_var.field_type == "monetary":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                    elif f_var.field_type == "one2many":
                        if getattr(self, f_var.field_name, None):
                            one2many_vals = self.value_get_json(getattr(self, f_var.field_name, None),
                                                                f_var.field_id.relation, list.endpoint_url, headers)
                            f_data = {"%s"%f_var.field_name: one2many_vals}
                    elif f_var.field_type == "reference":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                    elif f_var.field_type == "selection":
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}
                    else:
                        f_data = {"%s"%f_var.field_name: getattr(self, f_var.field_name, None)}

                    json_data.update(f_data)
                url = "%s/sync.db.order"%str(list.endpoint_url)
                lines = self.env['account.move'].browse(self.sync_account_id.id)
                payload = json.dumps({
                    "data": {
                        "type": "sync.db.order", "attributes": {
                            "name": "Register Payment %s" %self.communication,
                            "type": "payment",
                            "json_data": json.dumps(json_data),
                            "after_account_id": lines.sync_id
                            }
                        }
                    })

                response = requests.request("POST", url, headers = headers, data = payload)  # self.sync_db == True
        return result


