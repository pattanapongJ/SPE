# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

AUTH_TYPE_HELP= """
This field specifies the method used to authenticate API requests. Choose the most suitable \
authentication method based on your security requirements and the capabilities \
of your client applications.

- User's API Key: Use a unique API key by users/client for secure access.
- Using OAuth 2.0: Use OAuth2 for secure authorisation and token-based authentication using \
compatible authorisation provider.
- User Credentials: Authenticate with a combination of a username and password \
of the invoking user.
- Basic Authentication: A simple and widely-used authentication method.

Select the appropriate method that aligns with your security policies and \
the needs of your API consumers.
"""

RESOURCE_CONTROL_HELP = """
This field determines the access control settings for the API, specifying how users \
interact with the system and what actions they are permitted to perform. Choose the most suitable \
access control method based on your security policies and the specific requirements of your API.

- User Based Access: Restricts access based on user roles and permissions as per \
odoo's behaviour, ensuring a granular and user-specific approach.
- Full Access Using Sudo: Grants full and unrestricted access, utilising Odoo's sudo \
mechanism for elevated privileges.
- Personalized Access: Allows fine-tuned customisation of access settings, \
catering to unique and specific access requirements.

Select the access control method that aligns with your security policies and the \
intended use of your API.
"""


class EasyApi(models.Model):
    _name = 'easy.api'
    _description = 'API'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', tracking=True, required=True)
    description = fields.Text(string='Description')

    # Different Stages
    # draft: This stage is layer-1, all basic requirenments of api_framework_base
    #        module should be fill here
    # open: This stage is layer-2, all child module related information fill here
    # active: This stage is layer-3, Where API should be usable
    state = fields.Selection(selection=[('draft', "Draft"), ('open', 'Open'),
                                        ('active', 'Published')],
                            default='draft', string='Stage', tracking=True)

    user_id = fields.Many2one('res.users', string='Manager', tracking=True)

    base_url = fields.Char('Base URL', compute='_compute_base_url')
    base_endpoint = fields.Char('Endpoint', tracking=True, required=True)
    api_type = fields.Selection(selection=[], string='Protocol', tracking=True)
    authentication_type = fields.Selection(selection=[], string='Authentication',
                                           help=AUTH_TYPE_HELP, tracking=True)
    resource_control_type = fields.Selection(selection=[('user_based', 'User Based Access'),
                                                        ('full_access', 'Full Access Using Sudo')],
                                            string='Access Control', help=RESOURCE_CONTROL_HELP,
                                            tracking=True)

    page_size = fields.Integer('Page Length', default=40, tracking=True)

    # For Advance Option
    error_debug = fields.Boolean('Debug', default=False, tracking=True)
    error_detail = fields.Boolean('Verbose Errors', tracking=True)

    # For Help Section
    api_type_help = fields.Html('Api Type Help', compute='_compute_api_type_help')
    authentication_type_help = fields.Html(string='Authentication Type Help',
                                           compute='_compute_authentication_type_help')
    page_size_help = fields.Html('Page Length Help', compute='_compute_page_size_help')
    error_debug_help = fields.Html('Error Debug Help', compute='_compute_error_debug_help')

    @api.constrains('name')
    def _check_name_field(self):
        for record in self:
            duplicate_records = self.search([('name', '=', record.name)])
            if len(duplicate_records) > 1:
                raise models.ValidationError('Name field must be unique!')

    @api.constrains('base_endpoint')
    def _check_base_endpoint_field(self):
        for record in self:
            duplicate_records = self.search([('base_endpoint', '=', record.base_endpoint)])
            if len(duplicate_records) > 1:
                raise models.ValidationError('URL-endpoint  must be unique!')

    @api.model_create_multi
    def create(self, vals_list):
        results = super(EasyApi, self).create(vals_list)
        _logger.warning('New Api Settings created')
        return results

    @api.model
    def get_base_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f'{base_url}/'

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        defaults.setdefault('base_url', self.get_base_url())
        return defaults

    @api.model
    def _compute_base_url(self):
        self.base_url = self.get_base_url()

    def action_debug_enable(self):
        self.ensure_one()
        self.error_debug = True

    def action_debug_disable(self):
        self.ensure_one()
        self.error_debug = False

    def do_confirm(self):
        """
        Allowed to inherit by sub-modules to confirm their respected settings
        """
        return True

    def action_cancel(self):
        self.state = 'draft'

    def action_publish(self):
        self.state = 'active'

    def action_confirm(self):
        # ToDo: ANAND: Exception lists to be handled
        if self.do_confirm():
            self.state = 'confirm'

    def action_open(self):
        # It is used to reload routing table
        ir_http = self.env['ir.http']
        ir_http._clear_routing_map()
        ir_http.clear_caches()
        self.state = 'open'

    @api.depends('page_size')
    def _compute_page_size_help(self):
        for rec in self:
            help_msg = ('<b>Page Length</b>: This field describe how much records '
                        f'you want to display by default, currently it is {rec.page_size}')
            rec.page_size_help = help_msg

    @api.depends('authentication_type')
    def _compute_authentication_type_help(self):
        for rec in self:
            basic_info = ('This field specifies the method used to authenticate API requests. '
                          'Choose the most suitable authentication method based on your security '
                          'requirements and the capabilities of your client applications.')
            rec.authentication_type_help = basic_info

    @api.depends('api_type')
    def _compute_api_type_help(self):
        for rec in self:
            if rec.api_type == False:
                rec.api_type_help = False

    def _compute_error_debug_help(self):
        for rec in self:
            help_msg = ('<b>Error Debug</b>: This is advance api mode option. '
                        'When this field is checked, any exception that occurs '
                        'during API requests will have a response with its traceback.')
            rec.error_debug_help = help_msg
