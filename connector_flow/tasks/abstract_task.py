# -*- coding: utf-8 -*-
from base64 import b64decode, b64encode

import simplejson

from odoo import _

from ..tools import now
# for convenience, make the decorator available for import also from this ile
from .task import Task  # pylint: disable=unused-import


class AbstractTask(object):
    """Base class for tasks"""

    def __init__(self, task):
        self.task = task
        self.env = task.env
        assert len(task.ids) == 1, "Single task instance ID expected"
        self._id = task.ids[0]

    @staticmethod
    def _now(tz=None):
        return now(tz=tz)

    def _tz(self):
        """Returns the timezone of the user that ran this task"""
        users_pool = self.env['res.users']
        tz = users_pool.browse(self.env.uid).partner_id.tz
        return tz

    def run_task(self, task_id, **kwargs):
        return self.env['impexp.task'].browse(task_id).do_run(**kwargs)

    def related_action(self, job=None, **kwargs):
        """Overwrite this method to add a related action function for a
           specific task type."""
        pass

    def run(self, config=None, asynch=True, **kwargs):
        """
        All the task core action happens here.

        :param config: the configuration, as read from impexp.task's `config`
        :type config: dict
        :param asynch: run asynchronously?
        :type asynch: bool
        :param kwargs: additional args, handed over from the predecessor task
        """
        raise NotImplementedError

    def run_successor_tasks(self, **kwargs):
        successors = self.env['impexp.task.transition'].search_read([
            ('task_from_id', '=', self._id),
        ], ['task_to_id'])
        retval = None
        for succ in successors:
            retval = self.run_task(succ['task_to_id'][0], **kwargs)
        return retval

    def create_file(self, filename, data):
        ir_attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': b64encode(data),
            'datas_fname': filename,
        })
        impexp_file = self.env['impexp.file'].create({
            'attachment_id': ir_attachment.id,
            'task_id': self._id,
            'state': 'done',
        })
        return impexp_file.id

    def load_file(self, file_id):
        f = self.env['impexp.file'].browse(file_id)
        if f.attachment_id.datas:
            return b64decode(f.attachment_id.datas)
        return None


class AbstractChunkWriteTask(AbstractTask):
    """Task that writes and feeds data as a chunk"""

    def run(self, config=None, asynch=True, **kwargs):
        chunk_vals = self.prepare_chunk(config=config, **kwargs)
        if chunk_vals:
            data = chunk_vals.get('data', None)
            if data and not isinstance(data, basestring):
                data = simplejson.dumps(data)
                chunk_vals['data'] = data
            chunk = self.env['impexp.chunk'].create(chunk_vals)
            self.run_successor_tasks(chunk_id=chunk.id, asynch=asynch)

    def prepare_chunk(self, config=None, **kwargs):
        """
        Returns a dict with data for creating a chunk.

        The field `data` may contain non-string data, which will automatically
        be dumped into a JSON string.
        :rtype: dict
        """
        raise NotImplementedError


def action_open_chunk(chunk_id):
    """Window action to open a view of a given chunk"""
    return {
        'name': _("Chunk"),
        'type': 'ir.actions.act_window',
        'res_model': 'impexp.chunk',
        'view_type': 'form',
        'view_mode': 'form',
        'res_id': chunk_id,
    }


class AbstractChunkReadTask(AbstractTask):
    """Task that reads and processes a chunk of data"""

    def related_action(self, job=None, **kwargs):
        """Returns window action to open the chunk belonging to the job.
           This is an example for a related action function."""
        chunk_id = job.kwargs.get('chunk_id')
        if chunk_id:
            return action_open_chunk(chunk_id)
        return None

    def run(self, config=None, chunk_id=None, asynch=True, **kwargs):
        chunk = self.env['impexp.chunk'].browse(chunk_id)
        chunk_data = chunk.data
        new_state = 'failed'
        try:
            result = self.read_chunk(
                config=config, chunk_data=chunk_data, **kwargs)
            for succ_kwargs in (result or []):
                self.run_successor_tasks(asynch=asynch, **succ_kwargs)
            new_state = 'done'
        finally:
            chunk.write({'state': new_state})

    def read_chunk(self, config=None, chunk_data=None, **kwargs):
        """
        Processes the chunk and returns an iterator of kwargs dicts for the
        successor task.

        :rtype: Iterator[dict]
        """
        raise NotImplementedError
