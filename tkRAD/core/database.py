#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    tkRAD - tkinter Rapid Application Development library

    (c) 2013+ Raphaël SEBAN <motus@laposte.net>

    This program is free software: you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.

    If not, see: http://www.gnu.org/licenses/
"""

# lib imports
import os.path as OP
import sqlite3 as DB
from . import path as P


# private module member
__database = None


def get_database (**kw):
    """
        retrieves app-wide unique instance;
    """
    global __database
    if not isinstance(__database, Database):
        __database = Database(**kw)
    # end if
    return __database
# end def


class Database:
    """
        SQLite database layer;
    """

    # class constant defs
    ALL = "all"
    DEFAULT_PATH = "^/data/sqlite3/database.db"


    def __init__ (self, **kw):
        """
            class constructor;
        """
        # mandatory inits
        self.auto_commit = bool(kw.get("auto_commit", True))
        self.db_path = kw.get("db_path") or self.DEFAULT_PATH
        self.connection = None
        self.cursor = None
        # hook_method
        self._start(**kw)
    # end def


    def _start (self, **kw):
        """
            protected method def;
            hook method to be reimplemented in subclass, if necessary;
        """
        # hook_method
        self.init_members(**kw)
        # hook method
        self.open_database(**kw)
        # hook method
        self.init_database(**kw)
    # end def


    def close_database (self, *args, **kw):
        """
            event handler;
            closes current database connection, if any;
            raises DatabaseError otherwise;
        """
        # pending connection?
        if self.connection:
            # should auto commit?
            if self.auto_commit:
                # commit changes
                self.commit()
            # end if
            # close database
            self.connection.close()
            # reset members
            self.connection = None
            self.cursor = None
        # no pending connection
        else:
            # throw exception
            raise DatabaseError(
                "could not close database: "
                "no pending connection by now (DB not open?)."
            )
        # end if
    # end def


    def commit (self, *args, **kw):
        """
            event handler;
            commits current pending transaction in database;
            raises DatabaseError otherwise;
        """
        # pending connection?
        if self.connection:
            # commit transaction
            self.connection.commit()
        # no pending connection
        else:
            # throw exception
            raise DatabaseError(
                "could not commit current transaction in database: "
                "no pending connection by now (DB not open?)."
            )
        # end if
    # end def


    @property
    def db_path (self):
        """
            database pathname (canonized);
        """
        return self.__db_path
    # end def


    @db_path.setter
    def db_path (self, value):
        # comply with tkRAD path support
        value = P.normalize(value)
        # got value?
        if value:
            # set new path
            self.__db_path = value
        # keep unchanged
        else:
            # throw exception
            raise DatabaseError(
                "expected plain string of chars in "
                "'db_path' attribute."
            )
        # end if
    # end def


    @db_path.deleter
    def db_path (self):
        del self.__db_path
    # end def


    def dump_data (self, table_or_view, limit=100, formatter=None, output=None):
        """
            dumps all data from @table_or_view to stdout (CLI);
            @formatter callback function / method must be of
            callback(table_or_view, rows) signature;
            debug utility - could be reimplemented in subclass to meet
            your needs;
        """
        # param inits
        if not callable(formatter):
            # reset to callable
            formatter = self.dump_data_formatter
        # end if
        # dump data from table (or view)
        print(
            "\nDumping data from '{tov}' limited to max. {lim} rows\n"
            .format(tov=table_or_view, lim=limit),
            file=output,
        )
        # get all records along with @limit
        _rows = self.get_all(table_or_view, limit)
        # got a recordset?
        if _rows:
            # show formatted table or view
            print(formatter(table_or_view, _rows), file=output)
        else:
            print("This table/view is *EMPTY*.", file=output)
        # end if
    # end def


    def dump_data_formatter (self, table_or_view, rows):
        """
            generic data formatter for self.dump_data() method;
        """
        # line inits
        _line_sep = lambda width: "+-{}-+\n".format("-" * width)
        _line_start = "| "
        _line_end = " |"
        _get_line = lambda data, align="": (
            "{s}{d}{e}\n".format(
                s=_line_start,
                d=_field_sep.join(
                    [
                        "{{v:{a}{w}}}"
                        .format(a=align, w=_widths[_i])
                        .format(v=_v)
                        for _i, _v in enumerate(data)
                    ]
                ),
                e=_line_end
            )
        )
        # field inits
        _field_sep = " | "
        _fields = self.get_column_names()
        _widths = [len(_f) for _f in _fields]
        # first pass - evaluating column widths
        for _row in rows:
            for _index, _field in enumerate(_row):
                _widths[_index] = (
                    max(_widths[_index], len(str(_field)))
                )
            # end for
        # end for
        # evaluate line's total width
        _line_width = int(
            sum(_widths) + len(_field_sep) * (len(_fields) - 1)
        )
        # build table/view headers
        _fstring = _line_sep(_line_width)
        # table/view name
        _fstring += (
            "{s}{{t:^{w}}}{e}\n"
            .format(s=_line_start, w=_line_width, e=_line_end)
            .format(t=table_or_view)
        )
        _fstring += _line_sep(_line_width)
        # field names
        _fstring += _get_line(_fields, align="^")
        _fstring += _line_sep(_line_width)
        # secund pass - formatting rows
        for _row in rows:
            # field values
            _fstring += _get_line(_row)
            _fstring += _line_sep(_line_width)
        # end for
        # return formatted string
        return _fstring
    # end def


    def dump_tables (self, *args, limit=100, formatter=None, output=None):
        """
            dumps listed tables/views to stdout (CLI);
            debug utility - could be reimplemented in subclass to meet
            your needs;
        """
        # browse table or view list
        for _table_or_view in args:
            # dump table or view data
            self.dump_data(_table_or_view, limit, formatter, output)
        # end for
    # end def


    def fetch (self, qty=1, default=None):
        """
            fetches @qty rows resulting from a self.sql_query();
            if @qty < 2, same as self.cursor.fetchone();
            if @qty == "all", same as self.cursor.fetchall();
            if @qty == None, same as self.cursor.fetchmany();
            otherwise, same as self.cursor.fetchmany(size=@qty);
            by default, @qty = 1;
        """
        # enabled?
        if self.cursor:
            # fetch many rows?
            if qty is None:
                return self.cursor.fetchmany() or default
            # fetch all rows?
            elif str(qty).lower() == self.ALL:
                return self.cursor.fetchall() or default
            # fetch one row at a time?
            elif qty < 2:
                return self.cursor.fetchone() or default
            # fetch many rows with size
            else:
                return self.cursor.fetchmany(qty) or default
            # end if
        else:
            # throw exception
            raise DatabaseError(
                "could not fetch data: "
                "no pending cursor by now (DB not open?)."
            )
        # end if
    # end def


    def get_all (self, table_name, limit=100):
        """
            retrieves all fields in a recordset of max. @limit rows
            for table @table_name;
        """
        self.sql_query(
            "SELECT * FROM '{}' LIMIT {}".format(table_name, limit)
        )
        return self.fetch(self.ALL)
    # end def


    def get_column_names (self):
        """
            retrieves field names of the last SQL query, if any;
        """
        # enabled?
        if self.cursor:
            return tuple(c[0] for c in self.cursor.description or "")
        else:
            # throw exception
            raise DatabaseError(
                "could not get column names: "
                "no pending cursor by now (DB not open?)."
            )
        # end if
    # end def


    def get_record (self, table_name, row_id):
        """
            retrieves an unique record for table @table_name along
            with @row_id row identifier;
        """
        self.sql_query(
            "SELECT * FROM '{}' WHERE ROWID = ? LIMIT 1"
            .format(table_name),
            row_id
        )
        return self.fetch()
    # end def


    def init_database (self, **kw):
        """
            hook method to be reimplemented in subclass;
        """
        # put your own code here
        pass
    # end def


    def init_members (self, **kw):
        """
            hook method to be reimplemented in subclass;
        """
        # put your own code here
        pass
    # end def


    def is_open (self):
        """
            determines if database is currently opened or not;
        """
        return bool(self.connection and self.cursor)
    # end def


    @property
    def last_row_id (self):
        """
            READ-ONLY attribute;
            returns row id of the last modified row using SQL INSERT
            statement;
            returns None when not relevant;
        """
        # enabled?
        if self.cursor:
            # last row id
            return self.cursor.lastrowid
        else:
            # throw exception
            raise DatabaseError(
                "could not retrieve last row id: "
                "no pending cursor by now (DB not open?)."
            )
        # end if
    # end def


    @last_row_id.setter
    def last_row_id (self, value):
        """
            READ-ONLY attribute;
        """
        # throw exception
        raise DatabaseError(
            "'last_row_id' is a READ-ONLY attribute."
        )
    # end def


    def open_database (self, *args, **kw):
        """
            event handler;
            opens database along with @db_path pathname;
            falls back to self.DEFAULT_PATH if omitted;
            sets row factory to recommended sqlite3.Row structure;
            initializes a DB self.cursor on-the-fly;
        """
        # open database
        self.connection = DB.connect(
            # comply with tkRAD path support
            P.normalize(
                self.db_path or kw.get("db_path") or self.DEFAULT_PATH
            )
        )
        # set row factory with default sqlite3.Row (recommended)
        self.row_factory = DB.Row
        # get a new db cursor
        self.cursor = self.connection.cursor()
    # end def


    def rollback (self, *args, **kw):
        """
            event handler;
            cancels current pending transaction in database;
            raises DatabaseError otherwise;
        """
        # pending connection?
        if self.connection:
            # cancel transaction
            self.connection.rollback()
        # no pending connection
        else:
            # throw exception
            raise DatabaseError(
                "could not rollback current transaction in database: "
                "no pending connection by now (DB not open?)."
            )
        # end if
    # end def


    @property
    def row_factory (self):
        """
            gets current row factory;
            raises DatabaseError otherwise;
        """
        # pending connection?
        if self.connection:
            # get current row factory
            return self.connection.row_factory
        # no pending connection
        else:
            # throw exception
            raise DatabaseError(
                "could not retrieve current row factory: "
                "no pending connection by now (DB not open?)."
            )
        # end if
    # end def


    @row_factory.setter
    def row_factory (self, value):
        """
            sets a new row factory for current database;
            raises DatabaseError otherwise;
        """
        # pending connection?
        if self.connection and callable(value):
            # set new row factory
            self.connection.row_factory = value
        # no pending connection
        else:
            # throw exception
            raise DatabaseError(
                "could not set up row factory for database: "
                "value is not a callable or "
                "no pending connection by now (DB not open?)."
            )
        # end if
    # end def


    def sql_query (self, query, *args, **kw):
        """
            executes a unique SQL statement;
            use sql_script() instead, if you're looking for many SQL
            statements with no arguments (SQL script);
        """
        # enabled?
        if self.cursor:
            # execute unique SQL statement
            self.cursor.execute(query, args or kw)
            # should auto commit?
            if self.auto_commit:
                # commit changes
                self.commit()
            # end if
        else:
            # throw exception
            raise DatabaseError(
                "could not execute SQL statement: "
                "no pending cursor by now (DB not open?)."
            )
        # end if
    # end def


    def sql_script (self, script):
        """
            executes an SQL multiple statement script;
            use sql_query() instead, if you're looking for only one
            SQL statement with optional arguments;
        """
        # enabled?
        if self.cursor:
            # execute SQL script
            self.cursor.executescript(script)
            # should auto commit?
            if self.auto_commit:
                # commit changes
                self.commit()
            # end if
        else:
            # throw exception
            raise DatabaseError(
                "could not execute SQL script: "
                "no pending cursor by now (DB not open?)."
            )
        # end if
    # end def

# end class Database


# exception handling

class DatabaseError (Exception):
    """
        exception handler for Database class;
    """
    pass
# end class
