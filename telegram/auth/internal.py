import os
from Crypto.Hash import SHA512


def hashpass(password):
    password = bytes(password)
    hash = SHA512.new(password)
    return hash.hexdigest()


class InternalAuth(object):
    def __init__(self, config_dir=None):
        self._users = {}
        if config_dir is not None:
            self.load_config(config_dir)

    def load_config(self, config_dir):
        self.passwd_filename = os.path.join(config_dir, 'passwd')
        with open(self.passwd_filename, 'r') as f:
            for l in f.readlines():
                user, password = l.strip().split(':', 1)
                self._users[user] = password
                print("Added internal authentication for user %s." % user)

    def add_user(self, username, password):
        if username in self._users:
            raise NameError(u'User "%s" already exists.' % username)
        self._users[username] = hashpass(password)

    def authenticate(self, username, password):
        try:
            if self._users[username] == hashpass(password):
                return True
        except KeyError:
            pass
        return False
