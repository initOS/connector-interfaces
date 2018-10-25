# -*- coding: utf-8 -*-
from ast import literal_eval

from odoo import api, exceptions, fields, models
from odoo.addons.queue_job.job import job as qjob
from odoo.addons.queue_job.job import related_action

from ..tools import now


class ImpExpTaskTransition(models.Model):
    _name = "impexp.task.transition"
    _description = "Transition between tasks"

    task_from_id = fields.Many2one(
        'impexp.task',
        string="Output-producing Task",
    )
    task_to_id = fields.Many2one(
        'impexp.task',
        string="Input-consuming Task",
    )


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
        start_task = False
        for task in self.task_ids:
            if task.flow_start:
                start_task = task
                break
        if not start_task:
            raise Exception("Flow #%d has no start" % self.id)
        return start_task.do_run(**kwargs)


class ImpExpTask(models.Model):
    _name = "impexp.task"
    _description = "A wrapper class for an import/export task"

    @api.model
    def _get_available_tasks(self):
        return []

    name = fields.Char(
        required=True,
    )
    task = fields.Selection(
        selection=[],  # to be extended by user-defined tasks
        required=True,
    )
    config = fields.Text(
        string="Configuration",
    )
    max_retries = fields.Integer(
        string="Maximal Number of Re-tries if Run Asynchronously",
        required=True,
        default=1,
    )
    flow_id = fields.Many2one(
        'impexp.task.flow',
        string="Task Flow",
    )
    transitions_out_ids = fields.One2many(
        'impexp.task.transition', 'task_from_id',
        string="Outgoing Transitions",
    )
    transitions_in_ids = fields.One2many(
        'impexp.task.transition', 'task_to_id',
        string="Incoming Transitions",
    )
    flow_start = fields.Boolean(
        string="Is Start of Task Flow",
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

    @api.one
    @api.constrains('flow_start', 'flow_id')
    def _check_unique_flow_start(self):
        """Check that there is at most one task that starts the
           flow in a task flow"""
        if self.flow_start:
            flow_start_count = self.search_count([
                ('flow_id', '=', self.flow_id.id),
                ('flow_start', '=', True),
            ])
            if flow_start_count > 1:
                raise exceptions.ValidationError(
                    "The start of a task flow #%d has to be unique."
                    % self.flow_id.id)

    @api.multi
    def _config(self):
        """Parse task configuration"""
        self.ensure_one()
        config = self.config
        if config:
            return literal_eval(config)
        return {}

    @api.multi
    # pylint: disable=unused-argument
    def do_run(self, asynch=True, dt=None, **kwargs):
        self.ensure_one()
        if asynch:
            args = dict(
                description=self.name,
                max_retries=self.max_retries,
            )
            channel = self.channel_id or self.flow_id.channel_id or False
            if channel:
                args['channel'] = channel.complete_name
            this = self.with_delay(**args)
        else:
            this = self
        result = this._run_task(asynch=asynch, dt=now(), **kwargs)
        # If we run asynchronously, we ignore the result
        # (which is the UUID of the job in the queue).
        if not asynch:
            return result
        return True

    @api.multi
    def get_task_instance(self):
        self.ensure_one()
        task_method = self.task
        task_class = getattr(self, task_method + '_class')()
        return task_class(self)

    @api.multi
    def run_task(self, **kwargs):
        self.ensure_one()
        task_instance = self.get_task_instance()
        config = self._config()
        return task_instance.run(config=config, **kwargs)

    @qjob(default_channel='root')
    @related_action(action='related_action_impexp_task')
    @api.multi
    def _run_task(self, **kwargs):
        return self.run_task(**kwargs)

    @api.model
    # redirected from queue.job's related_action_impexp_task
    def get_related_action(self, job=None, **kwargs):
        assert job, "Job argument missing"
        assert job.model_name == self._name, (job.model_name, self._name)
        task_instance = self.browse(job.record_ids).get_task_instance()
        return task_instance.related_action(job=job, **kwargs)
