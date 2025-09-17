# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

import json
from werkzeug.exceptions import HTTPException


class UnsupportedMediaType(HTTPException):
    code = 415
    def get_headers(self, environ=None, scope=None):
        return [('Content-Type', 'application/json')]

    def get_body(self, environ=None, scope=None):
        return json.dumps({'Error': 'Unsupported Media Type.'})
