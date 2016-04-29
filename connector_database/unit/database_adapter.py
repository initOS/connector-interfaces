# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import threading
import logging

try:
    import pyodbc
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning('pyodbc not available')

from openerp.addons.connector.unit.backend_adapter import BackendAdapter
_logger = logging.getLogger(__name__)

lock = threading.Lock()
DATABASE_MAX_CHUNK = 2000


class DatabaseAdapter(BackendAdapter):
    """Base connector Database adapter"""
    _cnx = None
    # Python module that implements DB-API
    _module = None
    # placeholder for arguments in queries / prepared statements
    _query_arg_placeholder = '?'
    _table_name = None
    # unique identifier of the database database
    # multiple column key not identified
    _prefix = None
    _data_set_lookup_disable = False
    _filter_read = False

    def _connect_arguments(self):
        return self.backend_record.dsn, {}

    def _connect(self):
        if not self._module:
            raise NotImplementedError(
                "DB API module must be specified in a superclass"
            )
        args, kwargs = self._connect_arguments()
        DatabaseAdapter._cnx = self._module.connect(*args, **kwargs)
        DatabaseAdapter._cnx = module.connect(self.backend_record.dsn,
                                          unicode_results=True)

    @property
    def cnx(self):
        with lock:
            if DatabaseAdapter._cnx is None:
                self._connect()
            cursor = DatabaseAdapter._cnx.cursor()
            # we check if cursor is active, Naive implementation
            try:
                cursor.execute('SELECT 1').fetchone()
            except self._module.ProgrammingError:
                self._connect()
            finally:
                cursor.close()
        return DatabaseAdapter._cnx

    def _sql_query(self, sql, *args):
        """Execute an SQL query and return pyodbc rows

        :param sql: SQL query
        :type sql: str

        :return: pyodbc rows see https://code.google.com/p/pyodbc/wiki/Rows
        """
        # _module may have no context manager
        # e.g. see http://code.google.com/p/pyodbc/issues/detail?id=100
        cursor = self.cnx.cursor()
        try:
            if args:
                cursor.execute(sql, args)
            else:
                cursor.execute(sql)
            # We may use fetchmany with smaller data range
            return cursor.fetchall()
        except self._module.DatabaseError as exc:
            _logger.error((sql, args))
            _logger.error(repr(exc))
            raise exc
        finally:
            cursor.close()

    def get_unique_key_column(self):
        """Retrun the unique key of a SQL row

        :return: unique key
        :rtype: str
        """
        raise NotImplementedError(
            'get_unique_key_column not implemented for %s' % self
        )

    def get_date_columns(self):
        """Define creation and update columns of SQL row

        :return: can return  a tuple (create_date, modify_date) or None
        """
        return None

    def get_sql_conditions(self):
        """ Return where clause + args"""
        return ('', [])

    def adapt_dates_query(self):
        """Adds required SQL to add create_time and modify_time to
        query result row"""
        if not self.get_date_columns():
            return ''
        return (", %s as create_time, %s as modify_time" %
                self.get_date_columns())

    def adapt_dates_filter(self, date):
        """Standardize date columns name

        :param date: tuple of (create_date_name, update_date_name)
        :type date: tuple

        :return: unified date clause
        :rtype: str

        """
        return " create_time > %s or modify_time > %s" \
            % self._query_arg_placeholder,
            [date, date]

    def get_read_sql(self, code_slice):
        """Provides default SQL to read from Database data

        :param code_slice: list of external code to read
        :type code_slice: iterable of string

        :return: SQL query
        :rtype: str
        """
        # pyodbc does not support array formatting
        in_format = ', '.join([self._query_arg_placeholder] * len(code_slice))
        if self._filter_read:
            sql = "SELECT *%s FROM %s %s AND %s IN (%s)" % (
                self.adapt_dates_query(),
                self._table_name,
                self.get_sql_conditions()[0],
                self.get_unique_key_column(),
                in_format
            )
        else:
            sql = "SELECT *%s FROM %s WHERE %s IN (%s)" % (
                self.adapt_dates_query(),
                self._table_name,
                self.get_unique_key_column(),
                in_format
            )
        return sql

    def lookup_data_set(self, data_set, code):
        """ Return a generator of matching data in data_set memoizer

        :param data_set: Memoizer dict
        :type data_set: dict

        :param code: lookup code
        :type code: str

        :return: a generator of matching data in data_set memoizer
        :rtype: generator
        """
        return (x for x in data_set
                if getattr(x, self.get_unique_key_column(), None) == code)

    def read(self, database_codes, data_set=None):
        """ Return a generator of data read from Database date source

        :database_codes: list of code to read
        :type database_code: list
        :param data_set: Memoizer dict
        :type data_set: dict

        :return: a generator of data read from Database date source
        :rtype: generator
        """
        if not isinstance(database_codes, list):
            database_codes = [database_codes]
        # Optimisation tweak, negotiate database connexion is consumming
        # and not efficient for initial import
        if data_set and not self._data_set_lookup_disable:
            for code in database_codes:
                lookup = self.lookup_data_set(data_set, code)
                for row in lookup:
                    yield row
            return

        # SQL server number of remote argument are limited to 2100
        # we slice code in part of 2000
        # Slice code taken from Python Cookbook
        sliced_codes = [database_codes[i:i + DATABASE_MAX_CHUNK]
                        for i in xrange(0, len(database_codes), DATABASE_MAX_CHUNK)]
        for code_slice in sliced_codes:
            sql = self.get_read_sql(code_slice)
            if self._filter_read:
                # we preprend other where clause arguments
                code_slice[0:0] = self.get_sql_conditions()[1]
            for row in self._sql_query(sql, *code_slice):
                yield row

    def get_missing_sql(self, code_slice):
        """Provides default SQL to read Database data
        that are not in openerp

        :param code_slice: list of external code to read
        :type code_slice: iterable of string
        :return: SQL query
        :rtype: str
        """
        # pyodbc does not support array formatting
        in_format = ', '.join([self._query_arg_placeholder] * len(code_slice))
        sql = "SELECT %s FROM %s WHERE %s  IN (%s)" % (
            self.get_unique_key_column(),
            self._table_name,
            self.get_unique_key_column(),
            in_format
        )
        return sql

    def code_from_row(self, row):
        # If the cursor returns a dictionary, we can use the
        #  the column name. If it returns a list, we assume it will be
        #  at the first position (the query must be designed accordingly).
        code_column = self.get_unique_key_column()
        if isinstance(x, list):
            code_column = 0
        return row[code_column]

    def missing(self, codes):
        """Get missing records in Odoo for current backend
        :param codes: list of missing codes
        :type codes: list

        :return: list of missing pyodbc rows
                 see https://code.google.com/p/pyodbc/wiki/Row
        """
        # SQL server number of remote argument are limited to 2100
        # we slice code in part of 2000
        # Slice code taken from Python cookbook
        sliced_codes = [codes[i:i + DATABASE_MAX_CHUNK]
                        for i in xrange(0, len(codes), DATABASE_MAX_CHUNK)]
        res = set()
        for code_slice in sliced_codes:
            sql = self.get_missing_sql(code_slice)
            for x in selfi._sql_query(sql, *code_slice):
                res.add(self.code_from_row(x))
        existing = set(codes)
        return list(existing - res)

    def search(self, date=False):
        """Search all data in Database backend at lookup date

        :param date: lookup date for data
        :type date: Odoo date string
        :return: a list of database code
        :rtype: list
        """
        # Some databases does not suport alias in where clause
        # we have to do a derived table
        # Derived table allow to add global where clause
        # Maybe add a hook get_search_sql but it does not seems
        # really relevent here
        args = []
        filter_where, filter_args = self.get_sql_conditions()
        sql = """SELECT code FROM
                  (SELECT %s AS code %s FROM %s %s) src_table
             """ % (self.get_unique_key_column(),
                    self.adapt_dates_query(),
                    self._table_name,
                    filter_where)
        args += filter_args
        if date and self.get_date_columns():
            date_where, date_args = self.adapt_dates_filter(date)
            args += date_args
            sql += "WHERE %s" % date_where
        res = self._sql_query(sql, *args)
        # we may want to return generator but list seems more usable
        return [self.code_from_row(x) for x in res]
