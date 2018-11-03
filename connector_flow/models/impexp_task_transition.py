# -*- coding: utf-8 -*-
from odoo import fields, models


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
