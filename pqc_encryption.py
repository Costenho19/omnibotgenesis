from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

class PQCEncryption:
    def __init__(self, key: bytes):
        self.key = key[:32]  # Usamos los primeros 32 bytes para AES-256

    def encrypt(self, plaintext: str) -> str:
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
        iv = cipher.iv
        ciphertext = base64.b64encode(iv + ct_bytes).decode('utf-8')
        return ciphertext

    def decrypt(self, ciphertext: str) -> str:
        raw = base64.b64decode(ciphertext)
        iv = raw[:16]
        ct = raw[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')
        return plaintext
