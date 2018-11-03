# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ImpExpTaskFlow(models.Model):
    _name = "impexp.task.flow"
    _description = "A flow of tasks that are connected by transitions"

    name = fields.Char(
        required=True,
    )
    task_ids = fields.One2many(
        'impexp.task', 'flow_id',
        string="Tasks in Flow",
    )
    channel_id = fields.Many2one(
        'queue.job.channel',
        string="Channel",
    )
    channel = fields.Char(
        compute='_compute_channel',
        inverse='_inverse_channel',
        string="Channel",
    )

    @api.multi
    @api.depends('channel')
    def _inverse_channel(self):
        pool = self.env['queue.job.function']
        for record in self:
            channel = record.channel
            record.channel_id = pool._find_or_create_channel(channel) \
                if channel else False

    @api.multi
    @api.depends('channel_id')
    def _compute_channel(self):
        for record in self:
            channel = record.channel_id
            record.channel = channel.complete_name if channel else False

    @api.multi
    def do_run(self, **kwargs):
        self.ensure_one()
        start_tasks = self.task_ids.filtered(lambda t: t.flow_start)
        if len(start_tasks) != 1:
            raise Exception("Flow #%d does not have a unique start; got %s"
                            % (self.id, start_tasks.mapped(lambda t: t.name),))
        return start_tasks.do_run(**kwargs)

    @api.multi
    def do_run_sync(self, **kwargs):
        kwargs['asynch'] = False
        self.do_run(**kwargs)
