# -*- coding: utf-8 -*-
##############################################################################
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

class ChunkRevisit(models.TransientModel):
    """
    This wizard will relaunch the chunks
    """
    _name = "chunk.revisit"
    _description = "Relaunch chunks"

    async = fields.Boolean(string='Run Asynchronously', default=True)

    @api.multi
    def relaunch_chunk(self):
        self.ensure_one()
        chunk_ids = self.env.context.get('active_ids')
        assert chunk_ids
        for chunk in self.env['impexp.chunk'].browse(chunk_ids):
            if chunk.last_task_id:
                task = chunk.last_task_id
            elif chunk.file_id.task_id:
                task = chunk.file_id.task_id
            if task:
                task_instance = task.get_task_instance()
                #TODO: add async to wizard
                task_instance.run_successor_tasks(chunk_id=chunk.id, async=self.async, revisit=True)

        return {'type': 'ir.actions.act_window_close'}
