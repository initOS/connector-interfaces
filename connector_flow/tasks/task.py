# -*- coding: utf-8 -*-
from odoo import fields, models

# method of wrapping copied from functools.wraps

WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__doc__',)
# WRAPPER_UPDATES = ('__dict__',)  # not writable for classes
WRAPPER_UPDATES = ()


def wraps(wrapped, assigned=WRAPPER_ASSIGNMENTS, updated=WRAPPER_UPDATES):
    """Decorate a wrapper class to look like the wrapped class

    :param wrapped: the original class
    :param assigned: a tuple naming the attributes assigned directly from the
                     wrapped class to the wrapper class (defaults to
                     WRAPPER_ASSIGNMENTS)
    :param updated: a tuple naming the attributes of the wrapper class that are
                    updated with the corresponding attribute from the wrapped
                    class (defaults to WRAPPER_UPDATES)
    :return: the updated `wrapper`
    """
    def wrapping(wrapper):
        for attr in assigned:
            setattr(wrapper, attr, getattr(wrapped, attr))
        for attr in updated:
            dp = getattr(wrapper, attr)
            dp = dict(dp)
            dp.update(getattr(wrapped, attr, {}))
            setattr(wrapper, attr, dp)
        return wrapper

    return wrapping


def Task(selection=None, name=None):
    """
    Decorate a class for use as connector flow task

    Usage:
    ```
    @Task(selection='my_task', name="My Task")
    class CsvImport(AbstractTask):
        def run(self, config=None, asynch=True, **kwargs):
            pass
    ```

    :param selection: the impexp.task's task selection value
    :param name: the impexp.task's task selection name
    :return: the decorator
    """
    def decorator(Cls):
        # inject the decorator into the module of the decorated class,
        # otherwise the Odoo inheritance won't be detected
        Task.func_globals['__name__'] = Cls.__module__

        @wraps(Cls)
        class ClsTask(models.Model):
            _inherit = "impexp.task"

            task = fields.Selection(selection_add=[
                (selection, name),
            ])

        setattr(ClsTask, selection + '_class', lambda self: Cls)
        return ClsTask

    return decorator
