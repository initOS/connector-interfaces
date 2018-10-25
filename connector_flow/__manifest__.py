# -*- coding: utf-8 -*-
# Copyright (C) 2018 initOS GmbH (<http://www.initos.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Framework for connector-based task flows',
    'version': '10.0.1.0.0',
    'category': 'Connector',
    'author': 'initOS GmbH, Odoo Community Association (OCA)',
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
