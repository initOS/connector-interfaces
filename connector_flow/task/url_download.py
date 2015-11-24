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

from openerp import models, api, _

from .abstract_task import AbstractTask
import urllib2

import logging
_logger = logging.getLogger(__name__)


class UrlDownload(AbstractTask):
    """Url Configuration options:
     - url
    """

    def run(self, config=None, async=True):
        url_config = config['url']
        url = url_config.get('url', '')
        try:
            u = urllib2.urlopen(url)
            file_name = 'Url download of ' + self.session.env['impexp.task'].\
                search_read([('id', '=', self._id)], ['name'])[0]['name']
            content = u.read()
            file_id = self.create_file(file_name, content)
            self.run_successor_tasks(file_id=file_id, async=async)
        except:
            print (_('Error downloading'))


class UrlDownloadTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(UrlDownloadTask, self)._get_available_tasks() + [
            ('url_download', 'Url Download')]

    def url_download_class(self):
        return UrlDownload
