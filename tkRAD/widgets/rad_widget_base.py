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
from ..core import i18n
from ..core import events as EV
from ..core import options as OPT
from ..core import services as SM
from ..core import tools


class RADWidgetBase:
    r"""
        Base class to integrate into tkinter composite subclasses;
        implements ready-to-use onboard services for
        rapid application development (RAD);
        /!\ this class is *NOT* a tkinter.Widget subclass /!\
        e.g.:
            class MyFrameWidget (RADWidgetBase, tkinter.Frame):
                ...
            # end class MyFrameWidget
    """

    # class constant defs
    STICKY_ALL = TK.NW + TK.SE

    GRID_OPTIONS = {
        "padx": 0,
        "pady": 0,
        "ipadx": 0,
        "ipady": 0,
        "sticky": STICKY_ALL,
    } # end of GRID_OPTIONS

    PACK_OPTIONS = {
        "side": TK.TOP,
        "fill": TK.BOTH,
        "expand": 1,
    } # end of PACK_OPTIONS

    RC_OPTIONS = {
        "dir": "widget_dir",
        "filename": "widget_filename",
        "file_ext": "widget_file_ext",
    } # end of RC_OPTIONS


    def __del__ (self):
        r"""
            class destructor;
        """
        # unregister from events
        self.events._on_widget_destroy(self)
        # unregister from services
        self.services._on_widget_destroy(self)
    # end def


    def __init__ (self, tk_owner=None, slot_owner=None, **kw):
        r"""
            implements RAD ready-to-use services:
            self.tk_owner : tkinter parent widget;
            self.events : RADEventManager maechanism
                --- see tkRAD.core.events for more detail;
            self.options : application-wide rc config options manager;
            self.services : RADServiceManager system
                --- see tkRAD.core.services for more detail;
            /!\ all implemented services are tkinter-INDEPENDENT /!\
        """
        # member inits
        self._init_instance_members(**kw)
        self.tk_owner = tk_owner
        self.slot_owner = slot_owner or tk_owner
        self.app = SM.ask_for("app", silent_mode=True)
        self.events = EV.get_event_manager()
        self.options = OPT.get_option_manager(**kw)
        self.services = SM.get_service_manager()
        # add rc options section e.g. [classname] for this class
        self.options.set_sections(
            # redef - if key does not already exist
            self.RC_OPTIONS.setdefault(
                "section", self.get_rc_section()
            )
        )
        # widget setup
        if self.is_tk_parent(tk_owner) and not kw.get("subclassed"):
            self.init_widget(**kw)
        # end if
    # end def


    def _init_instance_members (self, **kw):
        r"""
            protected method def;
            inits dict() UPPERCASED class members to become unique
            for each instanciation as dict() is naturally common to
            any reference linked to it;
            this is made to avoid conflicts between instances of same
            class or of same ancestors /!\
            no return value (void);
        """
        for _name in dir(self):
            _value = getattr(self, _name, None)
            if _name.isupper() and isinstance(_value, dict):
                setattr(self, _name, _value.copy())
            # end if
        # end for
    # end def


    def _only_tk (self, kw):
        r"""
            protected method def;
            filters external keywords to suit tkinter init options;
            returns filtered dict() of keywords;
        """
        # inits
        _dict = dict()
        # $ 2014-02-24 RS $
        # Caution:
        # TK widget *MUST* be init'ed before calling _only_tk() /!\
        # self.configure() needs self.tk to work well
        if hasattr(self, "tk") and hasattr(self, "configure"):
            _attrs = set(self.configure().keys()) & set(kw.keys())
            for _key in _attrs:
                _dict[_key] = kw.get(_key)
            # end for
        # end if
        return _dict
    # end def


    def cast_parent (self, widget):
        r"""
            casts @widget param to see if it is a real tkinter parent
            widget (tk.Widget, tk.BaseWidget or tk.Tk);
            raises TypeError on type mismatch;
            returns True on success, False otherwise;
        """
        if self.is_tk_parent(widget):
            return True
        else:
            raise TypeError(
                _(
                    "object must be one of tkinter "
                    "Widget, BaseWidget or Tk type, "
                    "not '{object_type}'."
                ).format(object_type=repr(widget))
            )
            return False
        # end if
    # end def


    def cast_widget (self, widget):
        r"""
            casts @widget param to see if it is a real tkinter.Widget;
            raises TypeError on type mismatch;
            returns True on success, False otherwise;
        """
        if self.is_tk_widget(widget):
            return True
        else:
            raise TypeError(
                _(
                    "object must be of tkinter Widget type, "
                    "not '{object_type}'."
                ).format(object_type=repr(widget))
            )
            return False
        # end if
    # end def


    def classname (self):
        r"""
            returns object's classname;
        """
        return str(self.__class__.__name__)
    # end def


    def destroy (self, *args, **kw):
        r"""
            event handler; manages with tkRAD services unregistering
            before destroying tkinter.Widget part of the subclass;
        """
        # class destructor
        self.__del__()
        # super class inits
        super().destroy()
    # end def


    def enable (self, state=True):
        r"""
            enables/disables current widget along with @state value;
            if @state is None, keeps widget state unchanged;
        """
        # change state
        self.enable_widget(self, state)
    # end def


    def enable_widget (self, tkwidget, state=True):
        r"""
            enables/disables @tkwidget along with @state boolean value;
            if @state is None, keeps @tkwidget state unchanged;
        """
        # all is okay?
        if state is not None and hasattr(tkwidget, "configure"):
            # change state
            tkwidget.configure(
                state=TK.NORMAL if state else TK.DISABLED
            )
        # end if
    # end def


    def enabled (self):
        r"""
            returns True if current widget is enabled i.e. different
            from TK.DISABLED state (including 'readonly' for ttk
            widgets);
            returns False otherwise;
        """
        return self.widget_enabled(self)
    # end def


    def get_rc_section (self):
        r"""
            hook method to be reimplemented in subclass;
            returns RC section name for the current class;
            by default, returns current class name;
        """
        # put your own code in subclass
        return self.classname()
    # end def


    def init_widget (self, **kw):
        r"""
            virtual method to be implemented in subclass;
            use this method to make your own widget setup
            straight right after __init__() without bothering
            with class constructors, e.g.:
                class MyClass (RADWidgetBase, TK.Frame):
                    # don't bother with __init__()
                    # all services are ready to use!
                    def init_widget (self, **kw):
                        # put your setup here, e.g.:
                        self.options.load()
                        self.events.connect("<<Event>>", self.method)
                        _srv = self.services.ask_for("my_app_service")
                    # end def
                # end class MyClass
        """
        # inits
        pass
    # end def


    def is_tk_parent (self, widget):
        r"""
            determines if @widget param is a real tkinter parent widget
            i.e. one of tk.Widget, tk.BaseWidget or tk.Tk;
            returns True on success, False otherwise;
        """
        return isinstance(widget, (TK.Widget, TK.BaseWidget, TK.Tk))
    # end def


    def is_tk_widget (self, widget):
        r"""
            determines if @widget param is a real tkinter.Widget;
            returns True on success, False otherwise;
        """
        return isinstance(widget, TK.Widget)
    # end def


    def widget_enabled (self, tkwidget):
        r"""
            returns True if @tkwidget is enabled i.e. different from
            TK.DISABLED state (including 'readonly' for ttk widgets);
            returns False otherwise;
        """
        return bool(tkwidget.cget("state") != TK.DISABLED)
    # end def

# end class RADWidgetBase
