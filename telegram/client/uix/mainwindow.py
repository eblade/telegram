#!/usr/bin/env python3

""" Telegram Client Main Window Module """

import tkRAD
import tkRAD.core.async as ASYNC
import tkRAD.core.options as OPTIONS

from telegram.client import TelegramClient, TelegramSocket
from telegram.client import PasswordRequired, LoginFailed, SendError
from telegram.client.uix.link_manager import LinkManager
from telegram.post import SystemMessage

class MainWindow(tkRAD.RADXMLMainWindow):
    """ Telegram Client Main Window """
    

    # Initialization

    def init_widget(self, **kw):
        self.topmenu.xml_build()
        self.async = ASYNC.get_async_manager()
        self.connect_statusbar("show_statusbar")
        self.client = None
        self.after_idle(self.init_deferred)

    def init_deferred(self):
        self.xml_build()

        # Put Settings into the Settings Boxes
        o = OPTIONS.get_option_manager()
        self.connection_domain.insert(0, o['connection'].get('domain'))
        self.connection_username.insert(0, o['connection'].get('username'))
        self.connection_mode.insert(0, o['connection'].get('mode'))

        self.after_idle(self.bind_events)

    def bind_events(self):
        # Setup Menu
        self.showing_settings = False
        self.events.connect('File:Settings', self.on_toggle_settings)
        self.fix_gui_settings()

        # Setup Message Text Box
        self.text_message.bind("<Return>", self.on_send_message)

        # Setup Messages Text Box
        self.link_manager = LinkManager(self.text_messages)

        # Setup Password Text Box
        self.showing_password = False
        self.text_password.bind("<Return>", self.on_send_password)
        self.fix_gui_password()

        self.after_idle(self.init_client)

    def init_client(self):
        if self.client is not None:
            self.client.close()

        o = OPTIONS.get_option_manager()
        mode = o['connection'].get('mode')
        if mode in ('http', 'https'):
            self.client = TelegramClient()
            self.client.protocol = mode
        elif mode in ('ws', 'wss'):
            self.client = TelegramSocket()
            self.client.protocol = 'http' if mode == 'ws' else 'https'
        else:
            print("No such protocol: " + self.protocol)
            return

        self.client.domain = o['connection'].get('domain')
        self.client.port = 8080
        self.client.username = o['connection'].get('username')
        self.client.token = o['connection'].get('token')
        self.to = o['connection'].get('to')
        self.client.on_message_callback = self.on_message
        self.client.on_token_change_callback = self.on_token_change
        try:
            self.client.auth()
            self.on_info("Logged in with previous token")
            self.after_idle(self.on_poll_messages)
        except PasswordRequired:
            self.on_login()


    # Graphical Objects
    
    @property
    def frame_messaging(self):
        return self.mainframe.get_object_by_id("frame_messaging")

    @property
    def frame_settings(self):
        return self.mainframe.get_object_by_id("frame_settings")

    @property
    def text_message(self):
        return self.mainframe.get_object_by_id("text_message")

    @property
    def text_messages(self):
        return self.mainframe.get_object_by_id("text_messages")

    @property
    def text_password(self):
        return self.mainframe.get_object_by_id("text_password")

    @property
    def connection_domain(self):
        return self.mainframe.get_object_by_id("connection_domain")

    @property
    def connection_username(self):
        return self.mainframe.get_object_by_id("connection_username")

    @property
    def connection_mode(self):
        return self.mainframe.get_object_by_id("connection_mode")


    # Event Handlers

    def on_send_message(self, event):
        if event.state == 1:
            return  # User pressed shift+return
        message = event.widget.get('1.0', 'end').strip()
        try:
            self.client.send(self.to, message)
            event.widget.delete('1.0', 'end')
        except SendError:
            self.on_error("Could not send message")
        return 'break'  # prevent actual new-line
        
    def on_poll_messages(self, *args):
        if self.client.polling:
            self.client.receive()
            self.async.run_after(self.client.recommended_wait * 1000,
                                 self.on_poll_messages)
        else:
            self.client.connect()

    def on_login(self, *args):
        self.on_info("Password Required")
        self.showing_password = True
        self.fix_gui_password()

    def on_send_password(self, event):
        self.on_info("Logging in...")
        self.showing_password = False
        self.fix_gui_password()
        try:
            self.client.auth(event.widget.get())
            self.on_info("Login Successful!")
            self.on_poll_messages()
        except LoginFailed:
            self.on_errot("Login Failed!")
            self.on_login()

    def on_message(self, message):
        m = self.text_messages
        m['state'] = 'normal'
        m.insert('end', message.telegram_from, 
                 self.link_manager.add(self.on_user_tag_click, 
                                       message.telegram_from))
        m.insert('end', ' to ')
        m.insert('end', message.telegram_to, 
                 self.link_manager.add(self.on_user_tag_click, 
                                       message.telegram_to))
        m.insert('end', ': ')
        m.insert('end', message.content + '\n')
        m['state'] = 'disabled'
        
    def on_token_change(self, token):
        o = OPTIONS.get_option_manager()
        o['connection']['token'] = token

    def on_user_tag_click(self, user):
        if user:
            self.to = user
            
    def on_toggle_settings(self, *args, **kwargs):
        self.showing_settings = not self.showing_settings
        self.fix_gui_settings()

    def on_info(self, message):
        self.on_message(SystemMessage(
            self.client.username, 
            message,
            status_code=200
        ))

    def on_error(self, message):
        self.on_message(SystemMessage(
            self.client.username, 
            message,
            status_code=401
        ))

    # GUI Alterations

    def fix_gui_settings(self):
        if self.showing_settings:
            self.frame_settings.pack(fill="both", expand=True)
        else:
            self.frame_settings.pack_forget()
            o = OPTIONS.get_option_manager()
            o['connection']['domain'] = str(self.connection_domain.get())
            o['connection']['username'] = str(self.connection_username.get())
            o['connection']['mode'] = str(self.connection_mode.get())

    def fix_gui_password(self):
        if self.showing_password:
            self.text_message.pack_forget()
            self.text_password.pack()
            self.text_password.delete(0)
        else:
            self.text_password.pack_forget()
            self.text_message.pack(fill="both", expand=True)
