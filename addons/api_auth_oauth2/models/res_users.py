# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, api
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def api_auth_oauth2(self, provider, params, api_user):
        access_token = params.get('access_token')
        refresh_token = params.get('refresh_token')
        validation = self._auth_oauth_validate(provider, access_token)
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        oauth_uid = validation['user_id']
        oauth_user = self.search([("oauth_uid", "=", oauth_uid),
                                  ('oauth_provider_id', '=', provider)])
        api_user.write({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': oauth_user.id
        })
        params.pop('state')
        params.update({
            'db': self.env.cr.dbname,
        })
        params.pop('refresh_token')
        validation.pop('user_id')
        params.update(validation)
        return params

