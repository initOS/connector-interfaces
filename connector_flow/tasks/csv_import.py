# -*- coding: utf-8 -*-
import csv
import logging
from base64 import b64decode

import simplejson

from .abstract_task import AbstractTask, Task

_logger = logging.getLogger(__name__)


class AbstractTableRowImport(AbstractTask):
    """
    Parses a blob and stores the lines in chunks.

    The first line may contain headers.  In this case, declare
    `'includes_header': True` in the `config`, and the chunks will be dicts
    with the headers as keys.  Otherwise, the chunks will be lists.

    `config` defaults to
    ```
    {
        'includes_header': False,
    }
    ```
    """

    def _row_generator(self, file_data, config=None):
        """Parses a given blob into rows; returns an iterator to rows"""
        raise NotImplementedError

    def run(self, config=None, file_id=None, asynch=True, **kwargs):
        if not file_id:
            return

        includes_header = config.get('includes_header', False)

        lineno = 0
        header = None
        file_rec = self.env['impexp.file'].browse(file_id)
        datas = b64decode(file_rec.attachment_id.datas)
        rows = self._row_generator(datas, config=config)
        for row in rows:
            lineno += 1
            if includes_header and lineno == 1:
                header = row
                continue
            if not row:
                continue
            name = "%s, line %d" % (file_rec.attachment_id.datas_fname, lineno)
            data = row
            if header:
                data = dict(zip(header, data))
            chunk_id = self.env['impexp.chunk'].create({
                'name': name,
                'data': simplejson.dumps(data),
                'file_id': file_rec.id,
                'task_id': file_rec.task_id.id,
            }).id

            self.run_successor_tasks(chunk_id=chunk_id, asynch=asynch)

            if lineno % 1000 == 0:
                _logger.info("Created %d chunks", lineno)
        _logger.info("Created total of %d chunks", lineno)

        file_rec.write({'state': 'done'})


@Task(selection='csv_import', name="CSV Import")
class CsvImport(AbstractTableRowImport):
    """
    Parses a CSV file and stores the lines as chunks.

    `config` example:
    ```
    {
        'includes_header': False,  # headers in first line?
        'encoding': 'utf-8',  # input file encoding
        'chunk_encoding': 'utf-8',
        'csv': {
            'delimiter': ',',
            'doublequote': True,
            'escapechar': None,
            'lineterminator': '\r\n',
            'quotechar': '"',
            'quoting': 0,  # csv.QUOTE_MINIMAL
            'skipinitialspace': False,
        },
    }
    ```
    """

    def _row_generator(self, file_data, config=None):
        encoding = config.get('encoding', 'utf-8')
        chunk_encoding = config.get('chunk_encoding', 'utf-8')
        data = file_data.decode(encoding)\
                        .encode(chunk_encoding)\
                        .split("\n")
        options = config.get('csv', {})
        return csv.reader(data, **options)
