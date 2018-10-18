# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
#    Copyright (C) 2018 initOS GmbH (<http://www.initos.com>).
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
{
    'name': 'Connector-based task flow for import/export',
    'version': '10.0.1.0.0',
    'category': 'Connector',
    'author': 'initOS GmbH,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'http://www.initos.com',
    'depends': [
        'connector',
        'queue_job',
    ],
    'external_dependencies': {
        'python': [
            'ftputil',
            'simplejson',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',  # first, because defines main menu
        'views/impexp_chunk_view.xml',
        'views/impexp_file_view.xml',
        'views/impexp_task_view.xml',
        'wizards/run_task_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
