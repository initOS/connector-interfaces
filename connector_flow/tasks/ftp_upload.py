# -*- coding: utf-8 -*-
import logging
from base64 import b64decode

import ftputil

from .abstract_task import AbstractTask, Task

_logger = logging.getLogger(__name__)


@Task(selection='ftp_upload', name="FTP Upload")
class FtpUpload(AbstractTask):
    """FTP Configuration options:
     - host, user, password, port
     - upload_directory:  directory on the FTP server where files are
                          uploaded to
    """

    def _handle_existing_target(self, ftp_conn, target_name, data):
        raise Exception("%s already exists" % target_name)

    def _handle_new_target(self, ftp_conn, filename, data):
        with ftp_conn.open(filename, mode='wb') as file_obj:
            file_obj.write(data)
            _logger.info("FTP upload wrote %s, size %d", filename, len(data))

    def _target_name(self, ftp_conn, upload_directory, filename):
        return upload_directory + '/' + filename

    def _upload_file(self, config, filename, data):
        ftp_config = config['ftp']
        upload_directory = ftp_config.get('upload_directory', '')
        port_session_factory = ftputil.session.session_factory(
            port=int(ftp_config.get('port', 21))
        )
        with ftputil.FTPHost(
            ftp_config['host'], ftp_config['user'], ftp_config['password'],
            session_factory=port_session_factory
        ) as ftp_conn:
            target_name = self._target_name(
                ftp_conn, upload_directory, filename)
            if ftp_conn.path.isfile(target_name):
                self._handle_existing_target(ftp_conn, target_name, data)
            else:
                self._handle_new_target(ftp_conn, target_name, data)

    def run(self, config=None, file_id=None, asynch=True, **kwargs):
        f = self.env['impexp.file'].browse(file_id)
        self._upload_file(config, f.attachment_id.datas_fname,
                          b64decode(f.attachment_id.datas))
        self.run_successor_tasks(asynch=asynch)
