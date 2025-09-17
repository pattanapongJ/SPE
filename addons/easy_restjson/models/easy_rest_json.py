# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

import json
from odoo.api import call_kw
from odoo import models
from odoo.http import request
from odoo.models import check_method_name


class EasyRestJson(models.AbstractModel):
    _name = 'easy.rest.json'
    _description = 'Easy Rest Json'

    @classmethod
    def handle_request(cls):
        model = request.easyapi.get('model')
        method = request.easyapi.get('method')
        check_method_name(method)
        data = json.loads(request.httprequest.get_data(as_text=True))
        args = data.get('args', [])
        kwargs = data.get('kwargs', [])
        return call_kw(request.env[model], method, args, kwargs)
