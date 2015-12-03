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

from openerp import models, fields, api, exceptions, _

import logging
_logger = logging.getLogger(__name__)


class ImpExpMap(models.Model):
    _name = 'impexp.map'
    _description = 'A wrapper class for an import/export mapping'

    name = fields.Char(string='Name', required=True)
    target_model_id = fields.Many2one('ir.model', 'Target Model')
    type = fields.Selection([
                             ('update', 'Only Update'),
                             ('create', 'Only Create'),
                             ('both', 'Update & Create')
                             ], string='Type')
    field_ids = fields.One2many('impexp.field', 'map_id',
                                string='Fields', copy=False)
    decimals_separator = fields.Selection(string='Decimals separator', selection=[(',', 'Comma (,)'),
                                                         ('.', 'Dot (.)')], required=True, default='.')
    thousands_separator = fields.Selection(string='Thousands separator', selection=[('none', 'None'), (',', 'Comma (,)'),
                                                         ('.', 'Dot (.)')], required=True, default='none')


class ImpExpField(models.Model):
    _name = 'impexp.field'
    _description = 'A wrapper class for an import/export mapping field'
    _order = "position asc, id asc"

    map_id = fields.Many2one('impexp.map', required=True, string='Import map', select=True)
    position = fields.Integer('Position')
    pk = fields.Boolean(string='PK?')
    type = fields.Selection(string='Type', selection=[('add', 'Only add'),
                                                         ('update', 'Only update'),
                                                         ('both', 'Add & update'),
                                                         ('no', "None, just select / pk")], required=True, default='both')
    target_model_id = fields.Many2one('ir.model', 'Target Model', related='map_id.target_model_id', readonly=True)
    target_field_id = fields.Many2one('ir.model.fields', required=True, string='Field', select=True)
    chars_to_delete = fields.Char('Chars to clean', help="List of characters to remove, separated by commas (,)")
    value = fields.Text('Value')
    field_type = fields.Char()
    related_field_model = fields.Char()
    condition = fields.Text('Python condition', required=False, help="Condition that has to be True to apply the value")

    @api.onchange('target_field_id')
    def onchange_target_field_id(self):
        if self.target_field_id:
            self.field_type = self.target_field_id.ttype
            self.related_field_model = self.target_field_id.relation
        else:
            self.field_type = False
            self.related_field_model = False
