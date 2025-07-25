from pqcrypto.sign.dilithium2 import generate_keypair, sign, verify
from pqcrypto.exceptions import SignatureError

class PQCEncryption:
    def __init__(self, private_key=None, public_key=None):
        if private_key and public_key:
            self.public_key = public_key
            self.private_key = private_key
        else:
            self.public_key, self.private_key = generate_keypair()

    def sign_message(self, message: str) -> bytes:
        return sign(message.encode(), self.private_key)

    def verify_signature(self, message: str, signature: bytes) -> bool:
        try:
            verify(message.encode(), signature, self.public_key)
            return True
        except SignatureError:
            return False

