import hashlib
import time

class VoiceSignature:
    def __init__(self, secret_phrase: str):
        self.secret_phrase = secret_phrase

    def sign_message(self, message: str) -> str:
        timestamp = str(int(time.time()))
        payload = f"{message}|{self.secret_phrase}|{timestamp}"
        signature = hashlib.sha3_512(payload.encode('utf-8')).hexdigest()
        return signature

    def verify_signature(self, message: str, signature: str) -> bool:
        expected_signature = self.sign_message(message)
        return signature == expected_signature
