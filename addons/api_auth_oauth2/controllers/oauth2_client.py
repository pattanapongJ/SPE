# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

import json
from werkzeug.datastructures import Headers
from requests_oauthlib import OAuth2Session
from odoo import http, SUPERUSER_ID
from odoo.http import request, Response

class ApiOAuth2ClientController(http.Controller):

    def get_client_params(self):
        """
        return client_id, client_user_identity from http-request
        """
        request_data = json.loads(request.httprequest.get_data(as_text=True))
        client_id = request_data['client_id']
        client_user_identity = request_data['client_user_identity']
        api_endpoint = request_data['api_endpoint']
        return client_id, client_user_identity, api_endpoint

    @http.route(route='/auth/oauth2/provider/authorize', methods=['GET'],
                type='http', auth='none', save_session=False)
    def api_oauth2_provider_authorize(self, **kwargs):
        """
        This Controller used by client to fetch authorization code,
        here we have to provide client_id, client_user_identity in request-body(json)
        """
        client_id, client_user_identity, api_endpoint = self.get_client_params()

        api_rec = request.env['easy.api'].with_user(SUPERUSER_ID)\
                  .search([('base_endpoint','=',api_endpoint), ('state', '=', 'active')])
        if not api_rec:
            raise Exception("API Not Found")
        provider_rec = api_rec['oauth2_provider_ids']\
                       .filtered_domain([('client_id','=',client_id)])

        if not provider_rec:
            # when provider not found
            raise Exception("Provider Not Found")

        api_user = api_rec.api_user_ids.filtered_domain(
                                        [('client_user_id','=',client_user_identity)])
        if not api_user:
            # create api_user record on particular api_record
            api_rec.write({
                'api_user_ids': [(0, 0 ,{
                    'client_user_id': client_user_identity,
                    'provider_id': provider_rec.id,
                })]
            })

        redirect_uri = api_rec['oauth2_redirect_link']
        scope = provider_rec['scope']
        auth_endpoint = provider_rec['auth_endpoint']
        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)

        # access_type='offline', prompt='consent' parameters is for google to get refresh token in response
        state = {'d' : request.db,
                 'p' : provider_rec.id,
                 'r' : redirect_uri,
                 'ae' : api_endpoint,
                 'cui': client_user_identity}
        authorization_url, state = oauth.authorization_url(
        auth_endpoint, state=json.dumps(state),access_type='offline', prompt='consent')
        data = {
            'authorization_url': authorization_url
        }
        headers = Headers()
        headers['Content-Type'] = 'application/json'
        return Response(json.dumps(data), headers=headers, status=200)

    @http.route(route='/auth/oauth2/callback', methods=['GET'], type='http',
                auth='none', save_session=False, csrf=False)
    def oauth2_client_callback(self, **kwargs):
        """
        This is callback method, which generates access-token information
        """
        if 'error' in kwargs:
            error = {
                'error': kwargs['error']
            }
            return Response(json.dumps(error), status=400)

        state = json.loads(kwargs['state'])
        api_rec = request.env['easy.api'].sudo().search([('base_endpoint','=',state['ae']),
                                                         ('oauth2_redirect_link', '=', state['r'])])
        api_user = request.env['api.user'].with_user(SUPERUSER_ID)\
                   .search([('client_user_id','=',state['cui']), ('provider_id', '=', state['p']),
                            ('easy_api_id', '=', api_rec.id)])
        provider_rec = api_user and api_user.provider_id
        if not all([api_rec, api_user, provider_rec]):
            raise Exception('Invalid Request')

        client_id = provider_rec['client_id']
        client_secret = provider_rec['client_secret']
        token_endpoint = provider_rec['token_endpoint']
        redirect_uri = state['r']
        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)

        token = oauth.fetch_token(token_endpoint, authorization_response=request.httprequest.url,
                                  include_client_id=True, client_secret=client_secret)
        # Note: token['scope'] responded as list ["read", "write", "create", "delete"]
        # but client has to store string of space saperated like "read write create delete"
        token.update({'state': kwargs['state']})
        values = request.env['res.users'].with_user(SUPERUSER_ID)\
                 .api_auth_oauth2(provider_rec.id, token, api_user)
        headers = Headers()
        headers['Content-Type'] = 'application/json'
        return Response(json.dumps(values), headers=headers, status=200)

    @http.route(route='/auth/oauth2/token', methods=['POST'], type='http',
                auth='none', save_session=False, csrf=False)
    def oauth2_client_oauth2_token(self, **kwargs):
        """
        This is used to get access_token information by using client_user_identity, client_id/secret
        here we have to provide client_id, client_user_identity in request-body(json)
        """
        client_id, client_user_identity, api_endpoint = self.get_client_params()

        api_rec = request.env['easy.api'].sudo().search([('base_endpoint','=', api_endpoint), ('state', '=', 'active')])
        api_user = request.env['api.user'].with_user(SUPERUSER_ID)\
                   .search([('client_user_id','=',client_user_identity),
                            ('provider_id.client_id', '=', client_id),
                            ('easy_api_id', '=', api_rec.id)])
        if not api_user:
            raise Exception('Invalid Request')

        refresh_token = api_user['refresh_token']
        token_endpoint = api_user.provider_id.token_endpoint
        client_secret = api_user.provider_id.client_secret
        token = {'refresh_token': refresh_token}
        client = OAuth2Session(client_id, token=token, scope=None)
        extra = {
            'client_id': client_id,
            'client_secret': client_secret,
        }
        try:
            token = client.refresh_token(token_endpoint, **extra)
        except Exception:
            data = {'error': 'invalid_request'}
            headers = Headers()
            headers['Content-Type'] = 'application/json'
            return Response(json.dumps(data), headers=headers, status=400)
        api_user.write({'access_token': token['access_token']})
        api_user.write({'refresh_token': token['refresh_token']})
        headers = Headers()
        headers['Content-Type'] = 'application/json'
        token.pop('refresh_token')
        return Response(json.dumps(token), headers=headers,status=200)

    @http.route(route='/auth/oauth2/revoke', methods=['GET'], type='http',
                auth='none', save_session=False, csrf=False)
    def oauth2_client_revoke_token(self, **kwargs):
        """
        This Controller used by client to revoke token,
        here we have to provide client_id, client_user_identity in request-body(json)
        Note: we are using refresh token for revocation process.
        """
        client_id, client_user_identity, api_endpoint = self.get_client_params()

        api_rec = request.env['easy.api'].sudo().search([('base_endpoint','=', api_endpoint), ('state', '=', 'active')])
        api_user = request.env['api.user'].with_user(SUPERUSER_ID)\
                   .search([('client_user_id','=',client_user_identity),
                            ('provider_id.client_id', '=', client_id),
                            ('easy_api_id', '=', api_rec.id)])

        if not api_user:
            raise Exception('Invalid Request')

        refresh_token = api_user['refresh_token']
        revoke_endpoint = api_user.provider_id.revoke_endpoint
        client_secret = api_user.provider_id.client_secret
        token = {'refresh_token': refresh_token}
        client = OAuth2Session(client_id)

        # Make the token revocation request
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'token': token['refresh_token'],
                'client_id': client_id,
                'client_secret': client_secret}
        response = client.post(revoke_endpoint, headers=headers, data=data)
        if response.status_code == 200:
            api_user.unlink()
            headers = Headers()
            headers['Content-Type'] = 'application/json'
            return Response(headers=headers,status=200)
