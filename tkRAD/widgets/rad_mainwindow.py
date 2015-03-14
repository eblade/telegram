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
import tkinter as TK
from . import rad_window_base as WB


class RADMainWindow (WB.RADWindowBase, TK.Tk):
    r"""
        Lightweight MainWindow class for people not using tkinter XML
        widget building on a mainframe;
        supports all RADWidgetBase app-wide services by default;
        supports on-board self.statusbar widget by default;
        supports on-board self.mainframe widget container by default;
        supports on-board RADXMLMenu self.topmenu by default;
        supports main window states 'maximized', 'minimized', 'normal'
        and 'hidden' in gettings and settings;
        implements connected slots for event signals "PendingTaskOn"
        and "PendingTaskOff";
        implements connected slot for confirmation dialog before really
        quitting application;
        will pop up a tkinter messagebox with last traceback on raised
        exceptions during inits;
        will also report entire traceback in stderr on raised
        exceptions during inits;
    """

    # class constant defs
    WINDOW_ID = "mainwindow"

    def __init__ (self, **kw):
        r"""
            class constructor - main inits
            no return value (void);
        """
        # superclass inits
        TK.Tk.__init__(self)
        WB.RADWindowBase.__init__(self, tk_owner=None, **kw)
    # end def

# end class RADMainWindow
