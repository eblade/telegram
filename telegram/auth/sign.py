from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA

def generate_key_pair(username):
    private_key = RSA.generate(2048)
    public_key = private_key.publickey()
    return private_key.exportKey(), public_key.exportKey()


class RSAVerifier(object):
    def __init__(self, public_key_getter):
        """
        Contructor for RSA Veriefier.

        :param function public_key_getter: A function that take the username and returns it's
                                    public key
        """
        self.public_key_getter = public_key_getter

    def verify(self, sender, signature, text):
        """
        Verify a signed message.

        :param unicode sender: The sender of the message "username[@domain]"
        :param unicode signature: The message's signature
        :param unicode text: The signed content
        :rtype: bool True if authentic, False otherwise
        """
        public_key = self.public_key_getter(sender)
        if public_key is None:
            print("Unable to find the public key for %s!" % sender)
            return False

        key = RSA.importKey(public_key)
        h = SHA.new(text)
        verifier = PKCS1_v1_5.new(key)
        return verifier.verify(h, signature)


class RSASigner(object):
    def __init__(self, private_key_getter):
        """
        Contructor for RSA Veriefier.

        :param function private_key_getter: A function that take the username and returns 
                                    it's private key
        """
        self.private_key_getter = private_key_getter

    def sign(self, sender, text):
        """
        Let a user sign a message.

        :param unicode sender: The sender of the message "username[@domain]"
        :param unicode text: The content tot sign
        :rtype: unicode The signature
        """
        private_key = self.private_key_getter
        if private_key is None:
            print("Unable to find the private key for %s!" % sender)
            return None

        key = RSA.importKey(private_key)
        h = SHA.new(text)
        signer = PKCS1_v1_5.new(key)
        return signer.sign(h)
