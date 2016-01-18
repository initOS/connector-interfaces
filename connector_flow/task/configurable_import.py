# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import urllib2
from base64 import b64encode
from datetime import datetime

from openerp import models, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.addons.connector_flow.task.abstract_task \
    import AbstractChunkReadTask

import logging
_logger = logging.getLogger(__name__)


class ConfigurableImport(AbstractChunkReadTask):
    def read_chunk(self, config=None, chunk_data=None, async=True, chunk_id=None, task_id=None, results = {}, mapping=None):
        #get fields
        if task_id is None:
            raise except_orm(_('Insufficient Data!'),
                _('The map is not accesible from the chunk'))
        task = self.session.env['impexp.task'].browse(task_id)
        chunk = self.session.env['impexp.chunk'].browse(chunk_id)
        mapping = mapping or task.map_id
        fields = mapping.field_ids
        
        model = mapping.target_model_id.model
        obj = self.session.env[model]
        
        values = {}
        pk_data = {}
        for field in fields:
            if field.target_field_id.ttype == "many2one" and field.type in ['create','both'] and field.m2o_map_id:
                m2o_chunk = chunk.copy({'name': chunk.name + "/" + field.target_field_id.name,
                                        'last_task_id': False})
                try:
                    results = self.read_chunk(config=config, chunk_data=chunk_data, async=async, chunk_id=m2o_chunk.id, task_id=task_id, results=results, mapping=field.m2o_map_id)
                    new_state = 'done'
                except Exception as e:
                    _logger.info('Error importing chunk %s with exception %s' % (m2o_chunk.id, e, ))
                    new_state = 'failed'
                finally:
                    m2o_chunk.write({'state': new_state})
                if results.get('id', False):
                    results[str(field.target_field_id.name)] = results.pop('id')
                    values[str(field.target_field_id.name)] = results[str(field.target_field_id.name)].id
            else:
                value = self._get_field_value(field, chunk_data, results)
                if field.target_field_id.ttype == "many2one":
                    results[str(field.target_field_id.name)] = self.session.env[field.target_field_id.relation].browse(value)
                values[field.target_field_id.name] = value
                if field.pk:
                    pk_data[field.target_field_id.name] = value
        
        existing = False
        if pk_data:
            # get existing id for pks
            existing = self._search_id(model, pk_data, one=True)

        if existing:  # there is a match for pks
            results['id'] =  existing
            if mapping.type != 'create':  # if its only create, nothing to do; else we are updating
                fields_to_use = fields.search([('id', 'in', fields.ids), ('type', 'in', ['update', 'both'])])
                use_values = {field.target_field_id.name: values[field.target_field_id.name] for field in fields_to_use}
                if use_values:
                    existing.write(use_values)
                    _logger.info('Updated model %s with id %s' % (model, existing.id, ))
        else:  # no match
            if mapping.type != 'update':  # if its only update, nothing to do; else we are creating
                fields_to_use = fields.search([('id', 'in', fields.ids), ('type', 'in', ['create', 'both'])])
                use_values = {field.target_field_id.name: values[field.target_field_id.name] for field in fields_to_use}
                new_id = obj.create(use_values)
                _logger.info('Created model %s with id %s' % (model, new_id, ))
                results['id'] =  new_id
        
        res = {}
        for key, value in results.items():
            if isinstance(value, models.BaseModel):
                res[key] = value.id
        chunk.res = str(res)
        return results
        
    def _search_id(self, model, data, one=True):
        '''
        returns id / ids for a given search
        :param model: model name
        :param data: dict with field:value for the search
        :param one: True if the return is a unique id, False if it has to be a list with all the results
        '''
        if not data:
            return False
        try:
            model_obj = self.session.env[model]
            search_str = []
            for key, value in data.items():
                search_str.append((key, '=', value))
            res = model_obj.search(search_str)
            #TODO: maybe add a second search with ilike, but only for str fields - how to do it?
            if not res:
                _logger.info('Searching id for model %s with data %s gave zero results' % (model, str(data)))
                return False
            if len(res) > 1:
                if one:
                    _logger.info('Searching unique id for model %s with data %s gave results %s, assigned first value' % (model, str(data), str(res)))
                    res = res[0]
            else:
                res = res[0]  # single id
            return res
        except ValueError:
            _logger.info('Searching id for model %s with data %s gave error %s' % (model, str(data), ValueError))

    def _parse_value(self, field, value):
        '''
        parses the value to evaluate, depending on type
            text, char: as string
            boolean: as string (i.e. 'yes') -> it will be used as such
            integer: as integer
            float: as float
        not implemented in field to use _search_id
        :param value: the string from the chunk data
        '''
        field.ensure_one()
        if not value:
            return False
        ftype = field.target_field_id.ttype
        if ftype in ['char', 'text', 'boolean', 'selection']:
            return value
        elif ftype == 'integer':
            if field.map_id.thousands_separator != 'none':
                value = value.replace(field.map_id.thousands_separator, '')
            if field.map_id.decimals_separator != '.':
                value = value.replace(field.map_id.decimals_separator, '.')
            return int(value or 0)
        elif ftype == 'float':
            if field.map_id.thousands_separator != 'none':
                value = value.replace(field.map_id.thousands_separator, '')
            if field.map_id.decimals_separator != '.':
                value = value.replace(field.map_id.decimals_separator, '.')
            #XXX: what if there is an associated number of decimals with no decimal separator (i.e. 325=3.25) -> not taken into account
            return float(value or 0.0)
        elif ftype == 'many2one':
            #always search by name -> if you need to search for other fields you have to make a submapping with all the fields to pk / only search
            m2o_obj = self._search_id(field.target_field_id.relation, {'name': value})
            return m2o_obj and m2o_obj.id or False
        elif ftype == 'binary':
            try:
                url_obj = urllib2.urlopen(value)
                return b64encode(url_obj.read())
            except ValueError:
                _logger.info('Could not retrieve url %s for field %s' % (value, field.field_description))
        else:
            #TODO: rest of field types
            raise except_orm(_('Field type to be developped'),
                _("The field type '%s' has not been developped yet!") % (ftype,))

    def _get_field_value(self, field, data, results):
        '''
        returns the value processes for creation/search/etc in field
        :param field: the field record
        :param data: the chunk data
        '''
        field.ensure_one()
        #get v as value
        try:
            v = False
            if field.position>0:
                v = data[field.position - 1].strip()  # -1 because it starts in 0, but the user does not know
            if field.chars_to_delete:
                chars = field.chars_to_delete.split()
                for char in chars:
                    v = v.replace(char, '')
            v = self._parse_value(field, v)
        except Exception as e:
            raise except_orm(_('Field cannot be parsed'),
                _("The field '%s' cannot be parsed with data %s, with error %s") % (field.target_field_id.name, data[field.position], e, ))
        
        #condition and value can use v
        if field.condition:
            condition = field.condition
            """ dangerous: it may be a second field, and therefore it wont work ->better to put it in the value
            #load previous results by replacing them by its dictionary value
            for key in results.keys():
                condition = condition.replace(key, "results['%s']" % (key, ))
            """
            try:
                condition = eval(condition)
                if not condition:
                    return False
            except Exception as e:
                _logger.info('Cannot eval condition %s with data %s' % (field.condition, str(data), ))
                return False

        if not field.value:  # the value as it is
            res = v
        else:
            try:
                #load previous results by replacing them by its dictionary value
                value = field.value
                """ dangerous: it may be a second field, and therefore it wont work ->better to put it in the value
                for key in results.keys():
                    value = value.replace(key, "results['%s']" % (key, ))
                """
                res = eval(value)
            except Exception as e:
                _logger.info('Cannot eval value %s with data %s' % (field.value, str(data), ))
                return False
        return res

    def _field_dict(self, fields, data, results):
        '''
        makes a dict for all the fields with the data, to be applied to a create or write
        :param fields: all the fields to be translated into the dict
        :param data: the data from the chunk
        '''
        res = {}
        for field in fields:
            res[field.target_field_id.name] = self._get_field_value(field, data, results)
        return res

class ConfigurableImportTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(ConfigurableImportTask, self)._get_available_tasks() \
            + [('configurable_import', 'Configurable Import')]

    def configurable_import_class(self):
        return ConfigurableImport
