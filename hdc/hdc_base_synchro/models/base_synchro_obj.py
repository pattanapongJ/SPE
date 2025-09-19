# See LICENSE file for full copyright and licensing details.

from odoo import _,api, fields, models
import xmlrpc.client
import uuid
from odoo.tools import format_datetime

class BaseSynchroServer(models.Model):
    """Class to store the information regarding server."""

    _name = "base.synchro.server"
    _description = "Synchronized server"

    name = fields.Char("Server name", required=True)
    server_url = fields.Char(required=True)
    server_port = fields.Integer(required=True, default=8069)
    server_db = fields.Char("Server Database", required=True)
    login = fields.Char("Database UserName", required=True)
    password = fields.Char(required=True)
    obj_ids = fields.One2many(
        "base.synchro.obj", "server_id", "Models", ondelete="cascade"
    )

class BaseSynchroObj(models.Model):
    """Class to store the operations done by wizard."""

    _name = "base.synchro.obj"
    _description = "Register Class"
    _order = "sequence"

    name = fields.Char(required=True)
    domain = fields.Char(required=True, default="[]")
    server_id = fields.Many2one(
        "base.synchro.server", "Server", ondelete="cascade", required=True
    )
    model_id = fields.Many2one("ir.model", "Object to synchronize")
    action = fields.Selection(
        [("d", "Download"), ("u", "Upload"), ("b", "Both")],
        "Synchronization direction",
        required=True,
        default="d",
    )
    sequence = fields.Integer("Sequence")
    active = fields.Boolean(default=True)
    synchronize_date = fields.Datetime("Latest Synchronization", readonly=True)
    line_id = fields.One2many(
        "base.synchro.obj.line", "obj_id", "IDs Affected", ondelete="cascade"
    )
    avoid_ids = fields.One2many(
        "base.synchro.obj.avoid", "obj_id", "Fields Not Sync."
    )

    @api.model
    def get_ids(self, obj, dt, domain=None, action=None):
        if action is None:
            action = {}
        model_obj = self.env[obj]
        if dt:
            w_date = domain + [("write_date", ">=", dt)]
            c_date = domain + [("create_date", ">=", dt)]
        else:
            w_date = c_date = domain
        obj_rec = model_obj.search(w_date)
        obj_rec += model_obj.search(c_date)
        result = [
            (
                r.get("write_date") or r.get("create_date"),
                r.get("id"),
                action.get("action", "d"),
            )
            for r in obj_rec.read(["create_date", "write_date"])
        ]
        return result

    model_id_name = fields.Char(related='model_id.model')
    domain = fields.Char(required=True, default="[]")

    def action_view_synchronized_instances(self):   
        line_ids = self.env['base.synchro.obj.line'].search([('obj_id', '=',self.id)])         
        return {
            "name": _("Synchronized instances"),
            "view_mode": "tree,form",
            "res_model": "base.synchro.obj.line",
            "type": "ir.actions.act_window",
            "domain": [("id", "in", line_ids.ids)],                
            }
    
    def action_update_data(self):
        start_date = fields.Datetime.now()
        timezone = self._context.get("tz", "UTC")
        start_date = format_datetime(
            self.env, start_date, timezone, dt_format=False
        )
        line_ids = self.env['base.synchro.obj.line'].search([('obj_id', '=',self.id)]) 
        local_url = "http://%s:%d/xmlrpc/common" % (
            self.server_id.server_url,
            self.server_id.server_port,
        )
        db = self.server_id.server_db
        username = self.server_id.login
        password = self.server_id.password
        common = xmlrpc.client.ServerProxy(local_url)

        #authenticate
        uid = common.authenticate(db,username,password,{})

        local_url_obj = "http://%s:%d/xmlrpc/object" % (
            self.server_id.server_url,
            self.server_id.server_port,
        )
        ext_id_total = 0
        ext_id_create_new = 0
        ext_id_write = 0
        ext_id_create = 0
        models = xmlrpc.client.ServerProxy(local_url_obj)
        model_name = self.model_id_name
        for line in line_ids:
            if line.deleted == False:
                #search
                item_id = models.execute_kw(db, uid, password, model_name, 'search', [[['id', '=', line.remote_id]]],{'limit':1})
                #search External Identifiers
                model_ext_id = 'ir.model.data'
                ext_id = models.execute_kw(db, uid, password, model_ext_id, 'search', [[['model', '=', model_name],['res_id', '=', line.remote_id]]],{'limit':1})

                if ext_id:
                    ext_id = ext_id
                else:
                    model_name_replace = model_name.replace(".", "_")
                    name = '%s_sync_%d_%s' % (model_name_replace,line.remote_id,uuid.uuid4().hex[:8])
                    ext_id = models.execute_kw(db, uid, password, model_ext_id,'create', [{
                            "module": '__export__',
                            "name": name,
                            "model": model_name,
                            "res_id":line.remote_id,
                        }])
                    ext_id_create_new += 1
                
                ext_id_read = models.execute_kw(db, uid, password, model_ext_id, 'read', [ext_id], {'fields': ['module', 'name', 'display_name','model','res_id','complete_name']})
                ext_id_local = self.env['ir.model.data'].search([('model', '=',model_name),('res_id', '=',line.local_id)]) 
                if ext_id_local:
                    if ext_id_local.complete_name != ext_id_read[0].get('complete_name'):
                        ext_id_local = ext_id_local.write(
                            {
                                "module": ext_id_read[0].get('module'),
                                "name": ext_id_read[0].get('name'),
                                "display_name": ext_id_read[0].get('display_name'),
                                "model": model_name,
                                "res_id":line.local_id,
                            }
                        )
                        ext_id_write += 1
                        ext_id_total += 1
                else:
                    ext_id_local = self.env["ir.model.data"].create(
                        {
                            "module": ext_id_read[0].get('module'),
                            "name": ext_id_read[0].get('name'),
                            "display_name": ext_id_read[0].get('display_name'),
                            "model": model_name,
                            "res_id":line.local_id,
                        }
                    )
                    ext_id_create += 1
                    ext_id_total += 1
        end_date = fields.Datetime.now()
        end_date = format_datetime(
            self.env, end_date, timezone, dt_format=False
        )

        summary = """Here is the synchronization update external id report:

     Synchronization started: %s
     Synchronization finished: %s

     Synchronized records: %d
     Records create new external id: %d
     Records updated sync external id: %d
     Records new sync external id: %d
        """ % (
                start_date,
                end_date,
                ext_id_total,
                ext_id_create_new,
                ext_id_write,
                ext_id_create,
            )
        request = self.env["res.ext.id.update"]
        request.create(
                {
                    "name": "Update External ID report",
                    "user_id": self.env.user.id,
                    "date": fields.Datetime.now(),
                    "obj_id": self.id,
                    "body": summary,
                }
            )
        
        id2 = self.env.ref("hdc_base_synchro.base_synchro_obj_form_update_ext_id_finish").id
        return {
            "binding_view_types": "form",
            "view_mode": "form",
            "res_model": "base.synchro.obj",
            "views": [(id2, "form")],
            "view_id": False,
            "type": "ir.actions.act_window",
            "target": "new",
        }
    
    def action_view_external_id_report(self):   
        ext_id_report = self.env['res.ext.id.update'].search([('obj_id', '=',self.id)])         
        return {
            "name": _("External ID Report"),
            "view_mode": "tree,form",
            "res_model": "res.ext.id.update",
            "type": "ir.actions.act_window",
            "domain": [("id", "in", ext_id_report.ids)],                
            }

    def check_selected_field_not_sync(self,field_id):
        for line in self.avoid_ids:
            if field_id.name == line.name:
                return True
        return False
    
    def sort_selected(self,e):
        return e['selected']
    
    def button_edit_fields_not_sync(self):
        fields_ids = self.env['ir.model.fields'].search([('model_id', '=',self.model_id.id)]) 
        fields_list = []
        wizard_edit_fields_not_sync_line = []
        for field_id in fields_ids:
            selected = self.check_selected_field_not_sync(field_id)
            fields_list.append({
                'selected':selected,
                'name': field_id.name,
                'field_description': field_id.field_description,
            })
        fields_list.sort(key=self.sort_selected,reverse=True)
        for item in fields_list:
            wizard_edit_fields_not_sync_line.append((0, 0, 
            {   'selected':item['selected'],
                'name': item['name'],
                'field_description': item['field_description'],
            }))
        context = {
            'default_obj_id': self.id,
            'default_wizard_edit_fields_not_sync_line': wizard_edit_fields_not_sync_line,
        }

        return {
                'type': 'ir.actions.act_window',
                'name': 'Edit Fields Not Sync',
                'res_model': 'wizard.edit.fields.not.sync',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }

class BaseSynchroObjLine(models.Model):

    """Class to store object line in base synchro."""

    _name = "base.synchro.obj.line"
    _description = "Synchronized instances"

    name = fields.Datetime(
        "Date", required=True, default=lambda self: fields.Datetime.now()
    )
    obj_id = fields.Many2one("base.synchro.obj", "Object", ondelete="cascade")
    local_id = fields.Integer("Local ID", readonly=True)
    remote_id = fields.Integer("Remote ID", readonly=True)

    deleted = fields.Boolean(
        compute="_compute_deleted", string="Deleted"
    )
    xml_id = fields.Char(compute='_compute_xml_id', string='XML ID')

    def _compute_deleted(self):
        for rec in self:
            item_id = self.env[rec.obj_id.model_id_name].search([('id', '=',rec.local_id)]) 
            if item_id:
                rec.deleted = False
            else:
                rec.deleted = True    

    def _compute_xml_id(self):  
        for rec in self:
            rec.xml_id = ""
            if rec.deleted == False:
                model_name = rec.obj_id.model_id_name
                ext_id_local = self.env['ir.model.data'].search([('model', '=',model_name),('res_id', '=',rec.local_id)]) 
                if ext_id_local:
                    rec.xml_id = ext_id_local.complete_name

class BaseSynchroObjAvoid(models.Model):
    """Class to avoid the base synchro object."""

    _name = "base.synchro.obj.avoid"
    _description = "Fields to not synchronize"

    name = fields.Char("Field Name", required=True)
    obj_id = fields.Many2one(
        "base.synchro.obj", "Object", required=True, ondelete="cascade"
    )

    field_description = fields.Char(string='Field Label')
                    

