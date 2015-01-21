from __future__ import print_function

import random
import string
from datetime import datetime, timedelta


def generate_token(length):
    pool = string.letters + string.digits
    return ''.join(random.choice(pool) for i in xrange(length))



class SessionHandler(object):
    def __init__(self, expiry=3600):
        self._sessions = {}
        self._expiry = timedelta(seconds=expiry)

    def create(self, user):
        token = generate_token(64)
        expiry = datetime.now() + self._expiry
        self._sessions[token] = (user, expiry)
        print('Created token %s -> %s' % (token, user))
        return token

    def get_cookie_header(self, token):
        (user, expiry) = self._sessions[token]
        return u'auth-token=%s; Expires=%s' % (token, expiry.strftime('%a, %d-%b-%Y %H:%M:%S %Z'))
        #return u'auth-token=%s; Expires=%s; Secure' % (token, expiry.strftime('%a, %d-%b-%Y %H:%M:%S %Z'))

    def validate(self, token):
        try:
            (user, expiry) = self._sessions[token]
            return user
        except KeyError:
            return None
