# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields


class EasyApi(models.Model):
    _inherit = 'easy.api'

    # For CORS
    allowed_origins = fields.Text('CORS Allowed Origins', help='provide comma saperated origin')
