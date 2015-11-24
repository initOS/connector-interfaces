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

from openerp import models, fields, api


class CronTaskWizard(models.TransientModel):
    _name = 'impexp.wizard.crontask'

    name = fields.Char('Name', required=True)
    user_id = fields.Many2one('res.users', 'User', required=True)
    interval_number = fields.Integer('Interval Number', help="Repeat every x.", default=1)
    interval_type = fields.Selection([('minutes', 'Minutes'),
        ('hours', 'Hours'), ('work_days', 'Work Days'), ('days', 'Days'), ('weeks', 'Weeks'),
        ('months', 'Months')], 'Interval Unit', default='days')
    numbercall = fields.Integer('Number of Calls', help='How many times the method is called,\na negative number indicates no limit.', default=-1)
    doall = fields.Boolean('Repeat Missed', help="Specify if missed occurrences should be executed when the server restarts.")
    priority = fields.Integer('Priority', help='The priority of the job, as an integer: 0 means higher priority, 10 means lower priority.', default=5)
    nextcall = fields.Datetime('Next Execution Date', required=True, help="Next planned execution date for this job.", default=fields.Datetime.now)
    task_id = fields.Many2one('impexp.task', string='Task', required=True)
    async = fields.Boolean(string='Run Asynchronously', default=True)

    @api.multi
    def cron_task(self):
        self.ensure_one()
        kwargs = {'async': self.async}
        ir_cron = self.env['ir.cron'].\
                create({'name': self.name,
                        'user_id': self.user_id.id,
                        'interval_number': self.interval_number,
                        'interval_type': self.interval_type,
                        'numbercall': self.numbercall,
                        'nextcall': self.nextcall,
                        'doall': self.doall,
                        'priority': self.priority,
                        'model': 'impexp.task',
                        'active': True,
                        'function': 'do_run',
                        'args': kwargs})

        return {'type': 'ir.actions.act_window_close'}
