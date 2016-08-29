# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2015 Akretion (http://www.akretion.com).
#   @author Valentin CHEMIERE <valentin.chemiere@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import api, models, fields

from .abstract_task import AbstractTask
import logging
_logger = logging.getLogger(__name__)


class FileImport(AbstractTask):

    def run(self, config=None, async=True):
        att_ids = self.session.env['external.file.task'].browse(config['file_task_id']).run()
        impexp_file = self.session.env['impexp.file'].\
            create({'attachment_id': ir_attachment.id,
                    'task_id': self._id,
                    'state': 'done'})
        return impexp_file.id


class FileExport(AbstractTask):

    def run(self, config=None, file_id=None, async=True):
        task = self.session.env['external.file.task'].browse(config.id)
        file = self.session.env['impexp.file'].browse(file_id)
        file.attachment_id.write({'task_id': task.id})
        task.run()

class FileExportTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(FileExportTask, self)._get_available_tasks() + [
            ('file_export', 'File Export')
        ]

    def file_export_class(self):
        return FileExport


class FileImportTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(FileImportTask, self)._get_available_tasks() + [
            ('file_import', 'File Import')
        ]

    def file_import_class(self):
        return FileImport
