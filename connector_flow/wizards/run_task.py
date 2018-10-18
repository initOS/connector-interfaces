# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RunTaskWizard(models.TransientModel):
    _name = "impexp.wizard.runtask"

    flow_id = fields.Many2one(
        'impexp.task.flow',
        string="Task Flow",
    )
    task_id = fields.Many2one(
        'impexp.task',
        string="Task",
        required=True,
    )
    datas = fields.Binary(
        string="File",
    )
    datas_fname = fields.Char(
        string="File Name",
        size=256,
    )
    asynch = fields.Boolean(
        string="Run Asynchronously",
        default=True,
    )
    attachment_id = fields.Many2one(
        'ir.attachment',
        string="Result File",
    )

    @api.onchange('flow_id')
    def onchange_flow(self):
        task_id = False
        for task in self.flow_id.task_ids:
            if task.flow_start:
                task_id = task.id
                break
        self.task_id = task_id

    @api.multi
    def run_task(self):
        self.ensure_one()
        kwargs = {'asynch': self.asynch}
        if self.datas:
            upload_name = "Upload from run task wizard: %s" \
                % self.datas_fname
            ir_attachment = self.env['ir.attachment'].create({
                'name': upload_name,
                'datas': self.datas,
                'datas_fname': self.datas_fname,
            })
            file_rec = self.env['impexp.file'].create({
                'attachment_id': ir_attachment.id,
                'task_id': self.task_id.id,
            })
            kwargs['file_id'] = file_rec.id
        self.task_id.do_run(**kwargs)
