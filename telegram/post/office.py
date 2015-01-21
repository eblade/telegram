from __future__ import print_function
from gevent import monkey; monkey.patch_all()
from gevent.pool import Pool
from gevent.queue import Queue, Empty
from telegram.auth.sign import DummyVerifier


def clean_headers(headers):
    lower = {k.lower(): v for k, v in headers.items()}
    return {k: v for k, v in lower.items() if k.startswith('x-telegram-') or k == 'content-type'}


class PostOffice(object):
    def __init__(self, domain):
        self.domain = domain
        """ @type: list of [str] """
        self._inbox = {}
        """ @type: dict of [str, gevent.queue.Queue] """
        self._verifier_pool = Pool(64)
        self._verifier = DummyVerifier()
        self._listeners = {}

    def create_post_box(self, user):
        self._inbox[user] = Queue()

    def listen(self, username, callback):
        self._listeners[username] = callback
        print(u'Registered listener for ' + username)

    def post(self, headers, body):
        """
        :param bottle.BaseRequest message:
        """
        text = body.read()
        self._verifier_pool.spawn(self.sort, clean_headers(headers), text)

    def post_local(self, headers, body):
        """
        Do local sorting without any verification; the source is local.

        :param headers:
        :param body:
        :return:
        """
        headers = clean_headers(headers)
        sender = headers.get('x-telegram-from')
        receiver = headers.get('x-telegram-to')

        assert sender is not None, 'Missing header x-telegram-from'
        assert receiver is not None, 'Missing header x-telegram-to'

        content_type = headers.get('content-type', 'text/plain')
        assert content_type.startswith('text/plain'), 'Unsupported content-type "%s"' % str(content_type)

        if '@' in receiver:
            username, domain = receiver.split('@')
        else:
            username, domain = receiver, self.domain

        assert domain == self.domain, 'This domain is not handled by this server'
        assert username in self._inbox.keys(), 'There is no such user or group on this server'

        try:
            self._listeners[username](headers, body)
        except KeyError:
            self._inbox[username].put((headers, body))

    def sort(self, headers, body):
        """
        Sort the mail to the right inbox, if it can be verified.

        :param headers:
        :param body:
        """
        sender = headers.get('x-telegram-from')
        receiver = headers.get('x-telegram-to')
        sign_method = headers.get('x-telegram-sign-method', 'RSA')
        sign = headers.get('x-telegram-sign')
        content_type = headers.get('content-type', 'text/plain')

        assert sender is not None, 'Missing header x-telegram-from'
        assert receiver is not None, 'Missing header x-telegram-to'
        assert sign_method == 'RSA', 'Unsupported signing method "%s"' % str(sign_method)
        assert sign is not None, 'Missing header x-telegram-sign'
        assert content_type == 'text/plain', 'Unsupported content-type "%s"' % str(content_type)

        username, domain = receiver.split('@')
        assert domain == self.domain, 'This domain is not handled by this server'
        assert username in self._inbox.keys(), 'There is no such user or group on this server'

        assert self._verifier.verify(sender, receiver, body), 'Unable to verify message'

        try:
            self._listeners[username](headers, body)
        except KeyError:
            self._inbox[username].put((headers, body))

    def fetch(self, username):
        assert username in self._inbox.keys(), 'No inbox for user'
        try:
            return self._inbox[username].get_nowait()
        except Empty:
            return None







