__author__ = 'johan'


class InternalAuth(object):
    def __init__(self):
        self._users = {}

    def add_user(self, username, password):
        if username in self._users:
            raise NameError(u'User "%s" already exists.' % username)
        self._users[username] = password

    def authenticate(self, username, password):
        try:
            if self._users[username] == password:
                return True
        except KeyError:
            pass
        return False
