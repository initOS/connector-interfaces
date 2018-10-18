# -*- coding: utf-8 -*-
from odoo import fields, models


class ImpExpFile(models.Model):
    _name = "impexp.file"
    _description = "Wrapper for a file to be imported/exported"

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
    attachment_id = fields.Many2one(
        'ir.attachment',
        string="Attachment",
        required=True,
        readonly=True,
    )
    name = fields.Char(
        related='attachment_id.name',
        required=True,
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
        default='new',
        required=True,
        readonly=True,
    )
