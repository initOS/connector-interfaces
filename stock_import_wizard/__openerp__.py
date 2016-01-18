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

{
    'name': 'Stock import wizard',
    'version': '0.1',
    'author': 'Digital5 S.L.',
    'summary': 'Wizard that imports stock moves',
    'description': """
A wizard that uses connector flow mappings to import stock moves, creating the picking and the products on the fly
    """,
    'website': 'https://www.digital5.es',
    'depends': ['connector_flow'],
    'category': 'Stock',
    'sequence': 20,
    'demo': [],
    'data': [
        'wizard/stock_import_wizard_view.xml',
        'data/mapping.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
