# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models


class PublicJsonAPIKey(models.AbstractModel):
    """Base Json:API Public Method's base class."""
    _name = 'easy.jsonapi.key.public.methods'

    @classmethod
    def allowed_public(cls):
        """Override this method and return supper's result by adding your methods
        defined in it which are allowed for public calls.

        See an example bellow.
        """
        return []

# class YourPublicJsonAPI(models.AbstractModel):
#     _inherit = 'easy.jsonapi.public'

#     @classmethod
#     def allowed_public(cls):
#         res = super().allowed_public()
#         res.extend(['demo'])  # define your public methods
#         return res

#     @classmethod
#     def demo(self, query, response)
#         response.jsonapi_data = {
#             'result': 'Demo Successful',
#         }
#         return response
