# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo.fields import One2many, Many2one, Many2many



def json_api_prepare_create_value_one2many(self, data):
    value_list = []
    data_item = data['data']['relationships'][self.name]['data']
    if isinstance(data_item,dict):
        value_dict = {}
        for key, val in data_item['attributes'].items():
            value_dict[key] =  int(val) if isinstance(val, str) and val.isdigit() else val

        value_id = data_item.get('id')
        if value_id:
            value_list.append([1,value_id,value_dict])
        else:
            value_list.append([0,0,value_dict])

        return {self.name: value_list}

    if isinstance(data_item,list):
        for i in range(len(data_item)):
            value_dict = {}
            for key, val in data_item[i]['attributes'].items():
                value_dict[key] =  int(val) if isinstance(val, str) and val.isdigit() else val

            value_id = data_item[i].get('id')
            if value_id:
                value_list.append([1,value_id,value_dict])
            else:
                value_list.append([0,0,value_dict])

        return {self.name: value_list}

def json_api_prepare_create_value_many2many(self, data):
    if isinstance(data['data']['relationships'][self.name]['data'], dict):
        return {self.name: int(data['data']['relationships'][self.name]['data']['id'])}
    else:
        return {self.name: [int(val['id'])
                for val in data['data']['relationships'][self.name]['data']]}

def json_api_prepare_create_value_many2one(self, data):
    return {self.name: int(data['data']['relationships'][self.name]['data']['id'])}

def json_api_prepare_write_value_many2many(self, data, record):
    if isinstance(data['data']['relationships'][self.name]['data'], dict):
        return {self.name: int(data['data']['relationships'][self.name]['data']['id'])}
    else:
        return {self.name: [int(val['id'])
                for val in data['data']['relationships'][self.name]['data']]}

def json_api_prepare_write_value_many2one(self, data, record):
    return {self.name: int(data['data']['relationships'][self.name]['data']['id'])}

def json_api_prepare_write_value_one2many(self, data, record):
    id_list = [int(val['id']) for val in data['data']['relationships'][self.name]['data']
               if val.get('id')]
    for v in record[self.name]:
        if v.id not in id_list:
            record.write({self.name: [[3, v.id, 0]]})
    value_list = []
    for value in data['data']['relationships'][self.name]['data']:
        value_dict = {}
        if value.get('id'):
            if value.get('attributes'):
                for key, val in value['attributes'].items():
                    value_dict[key] =  int(val) if isinstance(val, str) and val.isdigit() else val
                value_list.append([1, int(value.get('id')), value_dict])
        else:
            if value.get('attributes'):
                for key, val in value['attributes'].items():
                    value_dict[key] =  int(val) if isinstance(val, str) and val.isdigit() else val
                value_list.append([0, 0, value_dict])
    return {self.name: value_list}

def json_api_prepare_relationship_write_value_many2one(self, data, record, method):
    if data['data'] is None:
        return {self.name: [[5,0,0]]}
    else:
        return {self.name: int(data['data']['id'])}

def json_api_prepare_relationship_write_value_many2many(self, data, record, method):
    if method == 'PATCH':
        if data['data']:
            if isinstance(data['data'], list):
                value_id = [int(v['id']) for v in data['data']]
                return {self.name: [[6,0,value_id]]}
            elif isinstance(data['data'], dict):
                value_id = [int(data['data']['id'])]
                return {self.name: [[6,0,value_id]]}
        else:
            return {self.name: [[5,0,0]]}
    elif method == 'POST':
        value_list = []
        value_ids = [int(val['id']) for val in data['data']]
        for val in value_ids:
            value_list.append([4, val, 0])
        return {self.name: value_list}
    elif method == 'DELETE':
        value_list = []
        value_ids = [int(val['id']) for val in data['data']]
        for val in value_ids:
            value_list.append([3, val, 0])
        return {self.name: value_list}

def json_api_prepare_relationship_write_value_one2many(self, data, record, method):
    if method == 'PATCH':
        if data['data']:
            id_list = [int(val['id']) for val in data['data'] if val.get('id')]
            for v in record[self.name]:
                if v.id not in id_list:
                    record.write({self.name: [[3, v.id, 0]]})
            value_list = []
            for value in data['data']:
                value_dict = {}
                if value.get('id'):
                    if value.get('attributes'):
                        for key, val in value['attributes'].items():
                            value_dict[key] =  int(val) if isinstance(val, str) and \
                                               val.isdigit() else val
                        value_list.append([1, int(value.get('id')), value_dict])
                else:
                    if value.get('attributes'):
                        for key, val in value['attributes'].items():
                            value_dict[key] =  int(val) if isinstance(val, str) and \
                                               val.isdigit() else val
                        value_list.append([0, 0, value_dict])
            return {self.name: value_list}
        else:
            return {self.name: [[5,0,0]]}

    elif method == 'POST':
        value_list = []
        for value in data['data']:
            value_dict = {}
            if value.get('id'):
                if value.get('attributes'):
                    for key, val in value['attributes'].items():
                        value_dict[key] =  int(val) if isinstance(val, str) and \
                                           val.isdigit() else val
                    value_list.append([1, int(value.get('id')), value_dict])
            else:
                if value.get('attributes'):
                    for key, val in value['attributes'].items():
                        value_dict[key] =  int(val) if isinstance(val, str) and \
                                           val.isdigit() else val
                    value_list.append([0, 0, value_dict])
        return {self.name: value_list}

    elif method == 'DELETE':
        value_list = []
        value_ids = [int(val['id']) for val in data['data']]
        for val in value_ids:
            value_list.append([3, val, 0])
        return {self.name: value_list}


One2many.json_api_prepare_create_value = json_api_prepare_create_value_one2many
Many2one.json_api_prepare_create_value = json_api_prepare_create_value_many2one
Many2many.json_api_prepare_create_value = json_api_prepare_create_value_many2many

One2many.json_api_prepare_write_value = json_api_prepare_write_value_one2many
Many2one.json_api_prepare_write_value = json_api_prepare_write_value_many2one
Many2many.json_api_prepare_write_value = json_api_prepare_write_value_many2many

One2many.json_api_prepare_relationship_write_value = json_api_prepare_relationship_write_value_one2many
Many2one.json_api_prepare_relationship_write_value = json_api_prepare_relationship_write_value_many2one
Many2many.json_api_prepare_relationship_write_value = json_api_prepare_relationship_write_value_many2many
