# -*- coding: utf-8 -*-
import csv
from cStringIO import StringIO

from odoo import fields, models

from .abstract_task import AbstractChunkReadTask


class CsvExport(AbstractChunkReadTask):
    """
    Reads a chunk and writes it into a CSV file.

    `config` example:
    ```
    {
        'encoding': 'utf-8',
        'filename': None,  # no default
        'csv': {
            'delimiter': ',',
            'doublequote': True,
            'escapechar': None,
            'lineterminator': '\r\n',
            'quotechar': '"',
            'quoting': csv.QUOTE_MINIMAL,
            'skipinitialspace': False,
        },
    }
    ```
    """

    def read_chunk(self, config=None, chunk_data=None, **kwargs):
        if not chunk_data:
            return None

        # output encoding defaults to utf-8
        encoding = config.get('encoding', 'utf-8')

        def encode_value(value):
            if isinstance(value, unicode):
                return value.encode(encoding)
            return value

        data = StringIO()
        options = config.get('csv', {})
        writer = csv.writer(data, **options)
        for row in chunk_data:
            writer.writerow(map(encode_value, row))

        file_id = self.create_file(config.get('filename'), data.getvalue())
        return [{
            'file_id': file_id,
        }]


class CsvExportTask(models.Model):
    _inherit = "impexp.task"

    task = fields.Selection(selection_add=[
        ('csv_export', "CSV Export"),
    ])

    def csv_export_class(self):
        return CsvExport
