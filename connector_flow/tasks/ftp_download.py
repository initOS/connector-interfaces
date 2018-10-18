# -*- coding: utf-8 -*-
import logging

import ftputil
from odoo import fields, models

from .abstract_task import AbstractTask

_logger = logging.getLogger(__name__)


class FtpDownload(AbstractTask):
    """FTP Configuration options:
     - host, user, password, port
     - download_directory:  directory on the FTP server where files are
                            downloaded from
     - move_directory:  If present, files will be moved to this directory
                        on the FTP server after download.
     - delete_files:  If true, files will be deleted on the FTP server
                      after download.
    """

    def _handle_new_source(
            self, ftp_conn, download_directory, filename, move_directory):
        """Open and read given file into create_file method,
           move file if move_directory is given"""
        with ftp_conn.open(
            self._source_name(download_directory, filename), mode='rb'
        ) as file_obj:
            data = file_obj.read()
        return self.create_file(filename, data)

    def _source_name(self, download_directory, filename):
        """Get the full filename, incl. directory"""
        return download_directory + '/' + filename

    def _move_file(self, ftp_conn, source, target):
        """Moves a file on the FTP server"""
        _logger.info("FTP download moving file %s to %s", source, target)
        ftp_conn.rename(source, target)

    def _delete_file(self, ftp_conn, source):
        """Deletes a file from the FTP server"""
        _logger.info("FTP download deleting file %s", source)
        ftp_conn.remove(source)

    def run(self, config=None, asynch=True, **kwargs):
        ftp_config = config['ftp']
        download_directory = ftp_config.get('download_directory', '')
        move_directory = ftp_config.get('move_directory', '')
        port_session_factory = ftputil.session.session_factory(
            port=int(ftp_config.get('port', 21)))
        with ftputil.FTPHost(
            ftp_config['host'], ftp_config['user'], ftp_config['password'],
            session_factory=port_session_factory
        ) as ftp_conn:
            file_list = ftp_conn.listdir(download_directory)
            downloaded_files = []
            for ftp_file in file_list:
                if ftp_conn.path.isfile(
                        self._source_name(download_directory, ftp_file)):
                    file_id = self._handle_new_source(
                        ftp_conn, download_directory, ftp_file, move_directory)
                    self.run_successor_tasks(file_id=file_id, asynch=asynch)
                    downloaded_files.append(ftp_file)

            # Move/delete files only after all files have been processed.
            if ftp_config.get('delete_files'):
                for ftp_file in downloaded_files:
                    self._delete_file(ftp_conn, self._source_name(
                        download_directory, ftp_file))
            elif move_directory:
                if not ftp_conn.path.exists(move_directory):
                    ftp_conn.mkdir(move_directory)
                for ftp_file in downloaded_files:
                    self._move_file(
                        ftp_conn,
                        self._source_name(download_directory, ftp_file),
                        self._source_name(move_directory, ftp_file))
        self.run_successor_tasks(asynch=asynch)


class FtpDownloadTask(models.Model):
    _inherit = "impexp.task"

    task = fields.Selection(selection_add=[
        ('ftp_download', "FTP Download"),
    ])

    def ftp_download_class(self):
        return FtpDownload
