# -*- coding: utf-8 -*-
from odoo import fields, models


class ImpExpChunk(models.Model):
    _name = "impexp.chunk"
    _description = "Structured (parsed) data from a file to be " \
                   "imported/exported"

    create_date = fields.Datetime(
        string="Created on",
        index=True,
        readonly=True,
    )
    write_date = fields.Datetime(
        string="Last Modified on",
        index=True,
        readonly=True,
    )
    name = fields.Char(
        required=True,
        readonly=True,
    )
    data = fields.Text(
        required=True,
    )
    file_id = fields.Many2one(
        'impexp.file',
        string="File",
        readonly=True,
    )
    task_id = fields.Many2one(
        'impexp.task',
        string="Task",
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('new', "New"),
            ('failed', "Failed"),
            ('done', "Done"),
        ],
        readonly=True,
        default='new',
    )
