__author__ = 'johan'

from Crypto.PublicKey import RSA


class DummyVerifier(object):
    def verify(self, sender, signature, text):
        return True
