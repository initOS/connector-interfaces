# -*- coding: utf-8 -*-
from odoo import models


class QueueJob(models.Model):
    _inherit = "queue.job"

    def related_action_impexp_task(self, **kwargs):
        return self.env['impexp.task'].get_related_action(job=self, **kwargs)
