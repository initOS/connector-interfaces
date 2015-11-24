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


class Config(models.Model):
    _name = 'impexp.config'
    _description = 'A wrapper class for an import/export configuration'

    name = fields.Char(string='Name', required=True)
    encoding = fields.Char(string='Encoding', required=True, default='utf-8')
    delimiter = fields.Selection(string='Delimiter', selection=[
                                                                (",", '<,> - Comma'),
                                                                (";", '<;> - Semicolon'),
                                                                ("\t", '<TAB> - Tab'),
                                                                (" ", '<SPACE> - Space'),
                                                                ("|", '<|> - Vertical bar'),
                                                                ], default=";")
    quotechar = fields.Selection(string='Quote char', selection=[
                                                            ("'", '<\'> - Single quotation mark'),
                                                            ('"', '<"> - Double quotation mark'),
                                                            ], default='"')
    lineterminator = fields.Selection(string='Line terminator', selection=[
                                                            ("\n", '<\n> - LF (Unix)'),
                                                            ("\r\n", '<\r\n> - CR + LF (Windows)'),
                                                            ("\r", '<\r> - CR (Apple)'),
                                                            ], default="\r\n")
    title_row = fields.Boolean(string='Title row?')
    ftp_host = fields.Char(string='Host')
    ftp_port = fields.Char(string='Port')
    ftp_user = fields.Char(string='User')
    ftp_password = fields.Char(string='Password')
    ftp_download_directory = fields.Char(string='Download directory', help='directory on the FTP server where files are downloaded from')
    ftp_move_directory = fields.Char(string='Move directory', help='If present, files will be moved to this directory on the FTP server after download')
    ftp_file_names = fields.Char(string='File names', help='List of files to process, separated by commas. If empty, all the files in the directory will be processed ')
    ftp_delete_files = fields.Boolean(string='Delete files?', help='If true, files will be deleted on the FTP server after download')
    url = fields.Char(string='Url')
