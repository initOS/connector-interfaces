# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning


class StockImport(models.TransientModel):
    _name = "stock.import"
    _description = "Stock Import"

    flow_id = fields.Many2one('impexp.task.flow', string='Task Flow', required=True)
    datas = fields.Binary(string='File', required=True)
    datas_fname = fields.Char(string='File Name', size=256)
    location_id = fields.Many2one('stock.location', string='Source Location', required=True)
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True)

    @api.multi
    def run_import(self):
        self.ensure_one()
        task_id = False
        for task in self.flow_id.task_ids:
            if task.flow_start:
                task_id = task.id
                break
        if not task_id:
            raise except_orm(_('No start task!'),
                _("You must define a starting task for the flow!"))
        
        pick_type_obj = self.env['stock.picking.type']
        pick_type = pick_type_obj.search([('default_location_src_id', '=', self.location_id.id),
                                        ('default_location_dest_id', '=', self.location_dest_id.id)])
        if not pick_type:
            pick_type = pick_type_obj.search([('default_location_src_id', 'child_of', self.location_id.id),
                                            ('default_location_dest_id', 'child_of', self.location_dest_id.id)])
        if not pick_type:
            pick_type = pick_type_obj.browse([1])

        import_wiz = self.env['impexp.wizard.runtask'].create({
                        'flow_id': self.flow_id.id,
                        'task_id': task_id,
                        'datas': self.datas,
                        'datas_fname': self.datas_fname,
                        'async': False})
        import_wiz.sudo().with_context({'location_id': self.location_id, 
                                 'location_dest_id': self.location_dest_id, 
                                 'picking_type_id': pick_type[0]}).run_task()
        if import_wiz.attachment_id:
            impexp_file = self.env['impexp.file'].search([('attachment_id', '=', import_wiz.attachment_id.id)])
            result = self.env['impexp.chunk'].search([('file_id', '=', impexp_file.id), ('name', 'like', 'picking_id'),('state', '=', 'done')], limit=1)
            if result:
                pick_id = eval(result.res).get('id', False)
                action = self.env['ir.actions.act_window'].for_xml_id('stock', 'action_picking_tree_all')
                action.update({
                    'domain': [('id', '=', pick_id)],
                })
                return action
        return {'type': 'ir.actions.act_window_close'}
