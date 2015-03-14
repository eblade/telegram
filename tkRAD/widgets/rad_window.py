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


class RADWindow (WB.RADWindowBase, TK.Toplevel):
    r"""
        Lightweight Toplevel Window class for people not using tkinter
        XML widget building on a mainframe;
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
    CONFIG = {
        # for subclasses pre-configuration
    } # end of CONFIG

    WINDOW_ID = "window"


    def __init__ (self, master=None, **kw):
        r"""
            class constructor - main inits
            no return value (void);
        """
        # default values
        self.CONFIG = self.CONFIG.copy()
        self.CONFIG.update(kw)
        # superclass inits
        TK.Toplevel.__init__(self)
        self.configure(**self._only_tk(self.CONFIG))
        # hide ugly orphan Tk() window
        if TK._default_root and not self.is_tk_parent(master):
            TK._default_root.withdraw()
        # end if
        WB.RADWindowBase.__init__(self, master, **self.CONFIG)
    # end def


    def _init_events (self, **kw):
        r"""
            protected method def;
            this could be overridden in subclass;
            no return value (void);
        """
        # super inits
        super()._init_events(**kw)
        # bind events
        self.events.connect_dict(
            {
                "close": self._slot_close_window,
                "Close": self._slot_close_window,
            }
        )
    # end def


    def _init_wm_protocols (self, **kw):
        r"""
            protected method def;
            this could be overridden in subclass;
            no return value (void);
        """
        # capture window manager's events handling
        self.protocol("WM_DELETE_WINDOW", self._slot_close_window)
    # end def


    def _slot_close_window (self, *args, **kw):
        r"""
            protected method def;
            this should be overridden in subclass;
            no return value (void);
        """
        # put here your own window closing procedure
        self._slot_quit_app()
    # end def

# end class RADWindow
