from __future__ import print_function
import json
import os
from gevent import monkey; monkey.patch_all()
from gevent.pool import Pool
from gevent.queue import Queue, Empty
from telegram.auth.sign import DummyVerifier




class PostOffice(object):
    def __init__(self, config_dir=None):
        """ @type: list of [str] """
        self._inbox = {}
        """ @type: dict of [str, gevent.queue.Queue] """
        self._verifier_pool = Pool(64)
        self._verifier = DummyVerifier()
        self._listeners = {}
        self.domain = 'localhost'
        self.users = {}
        if config_dir is not None:
            self.load_config(config_dir)

    def load_config(self, config_dir):
        self.users_filename = os.path.join(config_dir, 'users.json')
        self.office_filename = os.path.join(config_dir, 'office.json')

        with open(self.users_filename, 'r') as f:
            self.users = json.load(f)
            for username in self.users.keys():
                self.create_post_box(username)

        try:
            with open(self.office_filename, 'r') as f:
                settings = json.load(f)
                self.domain = settings.get('domain', 'localhost')
        except:
            pass

    def create_post_box(self, username):
        """
        Create a postbox for a user.

        :param str username:
        """
        self._inbox[username] = Queue()

    def listen(self, username, callback):
        """
        Register a listener callback for a username.

        :param str username: The username
        :param function callback: The callback(headers, message)
        """
        listeners = self._listeners.get(username)
        if listeners is None:
            self._listeners[username] = [callback]
        else:
            listeners.append(callback)
        print(u'Registered listener for ' + username)

    def post(self, headers, body, foreign=True):
        """
        Post a message into this office.

        :param dict headers: Message headers
        :param unicode body: Message Body
        :param bool foreign: True if this message comes from the outside, False otherwise
        """
        text = body.read()
        self._verifier_pool.spawn(self._sort, _clean_headers(headers), text, foreign=foreign)

    def fetch(self, username):
        """
        Fetch the next available message in the inbox of a user. Returns None if empty.

        :param str username: The username
        :rtype: tuple of [dict, str]|None
        """
        assert username in self._inbox.keys(), 'No inbox for user'
        try:
            return self._inbox[username].get_nowait()
        except Empty:
            return None

    def _sort(self, headers, body, foreign=True):
        """
        Do local sorting without any verification; the source is local.

        :param dict headers: Message headers
        :param unicode body: Message Body
        :param bool foreign: True if this message comes from the outside, False otherwise
        """
        headers = _clean_headers(headers)
        body = _clean_body(body)

        sender = headers.get('x-telegram-from')
        receiver = headers.get('x-telegram-to')
        content_type = headers.get('content-type', 'text/plain')

        assert sender is not None, 'Missing header x-telegram-from'
        assert receiver is not None, 'Missing header x-telegram-to'
        assert content_type.startswith('text/plain'), 'Unsupported content-type "%s"' % str(content_type)

        if foreign:
            sign_method = headers.get('x-telegram-sign-method', 'RSA')
            sign = headers.get('x-telegram-sign')
            assert sign_method == 'RSA', 'Unsupported signing method "%s"' % str(sign_method)
            assert sign is not None, 'Missing header x-telegram-sign'
            assert '@' in receiver
            username, domain = receiver.split('@')
            assert self._verifier.verify(sender, receiver, body), 'Unable to verify message'
        else:
            if '@' in receiver:
                username, domain = receiver.split('@')
            else:
                username, domain = receiver, self.domain

        assert domain == self.domain, 'This domain is not handled by this server'
        assert username in self._inbox.keys(), 'There is no such user or group on this server'

        deliveries = 0
        for listener in self._listeners.get(username):
            try:
                listener(headers, body)
                deliveries += 1
            except:
                pass

        if deliveries == 0:
            self._inbox[username].put((headers, body))


def _clean_headers(headers):
    lower = {k.lower(): v for k, v in headers.items()}
    return {k: v for k, v in lower.items() if k.startswith('x-telegram-') or k == 'content-type'}


def _clean_body(body):
    tag = False
    quote = False
    out = ""

    for c in body:
        if c == '<' and not quote:
            tag = True
        elif c == '>' and not quote:
            tag = False
        elif c in ("'", '"') and tag:
            quote = not quote
        elif not tag:
            out += c

    return out