# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from base64 import b64encode
import json
from dateutil.relativedelta import relativedelta
from odoo import models
from odoo.fields import Datetime
from odoo.http import request


class AuthSignUpJsonAPIKey(models.AbstractModel):
    _inherit = 'easy.jsonapi.key.public.methods'

    @classmethod
    def allowed_public(cls):
        res = super().allowed_public()
        res.extend(['signup', 'signin', 'changepasswd', 'signout'])
        return res

    @classmethod
    def signup(cls, query, response):
        data = json.loads(request.httprequest.get_data(as_text=True))

        # Signup Must Require login, name and password as data in body.
        if not all([x in data and data[x] for x in ['login', 'name', 'password']]):
            raise Exception("Invalid Use of Method.")

        db_name, login, passwd = request.env['res.users'].sudo().signup({
            'login': data['login'],
            'name': data['name'],
            'password': data['password'],
        })
        request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        pre_uid = request.session.authenticate(request.db, login, passwd)
        if not pre_uid:
            raise Exception('Authentication Failed.')

        api_key = cls.get_new_api_key(pre_uid)

        response.jsonapi_data = {
            'result': 'Signup Successful',
            'api_key': api_key.apikey,
            'user_id': pre_uid
        }
        return response

    @classmethod
    def get_new_api_key(cls, user_id):
        api_record = request.env['easy.api'].sudo().search([('id', '=', request.api_record['id'])])
        new_api_key = request.env['api.auth.apikey'].sudo().create({
            'easy_api_id': api_record.id,
            'user_id': user_id,
            'expiry': Datetime.now() + relativedelta(days=api_record.public_jsonapi_key_expiry),
            'api_key_choice': 'auto',
        })
        return new_api_key

    @classmethod
    def signin(cls, query, response):
        data = json.loads(request.httprequest.get_data(as_text=True))
        # Signup Must Require login, name and password as data in body.
        if not all([x in data and data[x] for x in ['login', 'password']]):
            raise Exception("Invalid Use of Method.")
        login = data['login']
        passwd = data['password']
        pre_uid = request.session.authenticate(request.db, login, passwd)
        if not pre_uid:
            raise Exception('Authentication Failed.')
        api_key = cls.get_user_api_key(pre_uid)
        if not api_key:
            raise Exception('Authentication Failed.')
        response.jsonapi_data = {
            'result': 'Login Successful',
            'api_key': api_key.apikey,
            'user_id': pre_uid
        }
        return response

    @classmethod
    def get_user_api_key(cls, user_id):
        api_record = request.env['easy.api'].sudo().search([('id', '=', request.api_record['id'])])
        api_key = api_record.api_key_ids.filtered_domain(
            [('user_id', '=', user_id)])
        if not api_key:
            api_key = cls.get_new_api_key(user_id)
            return api_key
        api_key = api_key.sorted('expiry', True)
        api_key = api_key[0]
        cls.update_api_key_expiry(api_key, api_record)
        return api_key

    @classmethod
    def update_api_key_expiry(cls, api_key, api_record):
        api_key.write({'expiry': Datetime.now() + relativedelta(days=api_record.public_jsonapi_key_expiry)})

    @classmethod
    def changepasswd(cls, query, response):
        data = json.loads(request.httprequest.get_data(as_text=True))
        # Signup Must Require login, name and password as data in body.
        if not all([x in data and data[x] for x in ['login', 'password', 'new_password']]):
            raise Exception("Invalid Use of Method.")
        login = data['login']
        passwd = data['password']
        new_passwd = data['new_password']
        pre_uid = request.session.authenticate(request.db, login, passwd)
        if not pre_uid:
            raise Exception('Authentication Failed.')
        the_user = request.env['res.users'].browse(pre_uid)
        the_user.change_password(passwd, new_passwd)
        request.env.cr.commit()
        pre_uid = request.session.authenticate(request.db, login, new_passwd)
        if not pre_uid:
            raise Exception('Unable to change password of the user.')
        api_key = cls.get_user_api_key(pre_uid)
        response.jsonapi_data = {
            'result': 'Password Update Successful',
            'api_key': api_key[0].apikey,
            'user_id': pre_uid
        }
        return response

    @classmethod
    def signout(cls, query, response):
        data = json.loads(request.httprequest.get_data(as_text=True))
        # Signup Must Require login, name and password as data in body.
        if not all([x in data and data[x] for x in ['user_id']]):
            raise Exception("Invalid Use of Method.")
        user = request.env['res.users'].sudo().search([('id', '=', int(data['user_id']))])
        if not user:
            raise Exception("User Not Found")
        cls.remove_user_api_key(user.id)
        response.jsonapi_data = {
            'result': 'Signout Successfully',
            'user_id': user.id
        }
        return response

    @classmethod
    def remove_user_api_key(cls, user_id):
        api_record = request.env['easy.api'].sudo().search([('id', '=', request.api_record['id'])])
        api_key = api_record.api_key_ids.filtered_domain(
            [('user_id', '=', user_id)])
        if not api_key:
            return
        api_key.unlink()
