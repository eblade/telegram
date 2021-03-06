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
from ..widgets import rad_window as RW
from . import rad_xml_frame as XF


class RADXMLWindow (RW.RADWindow):
    r"""
        general purpose tkRAD Toplevel Window class implementing
        tkinter XML widget building;
    """

    def _init_mainframe (self, **kw):
        r"""
            inherited from RADWindowBase class;
        """
        # widget inits
        self.mainframe = kw.get("mainframe") or XF.RADXMLFrame(self, **kw)
        if hasattr(self.mainframe, "set_xml_filename"):
            self.mainframe.set_xml_filename(
                kw.get("xml_filename") or "mainwindow"
            )
        # end if
        # shortcut inits
        self.tk_children = self.mainframe.winfo_children
        self.mainframe.quit_app = self._slot_quit_app
    # end def

# end class RADXMLWindow
