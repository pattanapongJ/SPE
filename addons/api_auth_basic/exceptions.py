# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from werkzeug.exceptions import Unauthorized


class BasicUnauthorized(Unauthorized):

    def get_headers(self, environ= None, scope= None):
        return [('WWW-Authenticate', 'Basic realm="api"')]

