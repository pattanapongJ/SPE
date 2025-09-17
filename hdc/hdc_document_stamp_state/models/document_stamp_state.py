from odoo import api, fields, models, _
from datetime import datetime


class DocumentStampState(models.Model):
    _name = 'document.stamp.state'
    _description = 'Document Stamp State'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    description = fields.Char(string='Description')