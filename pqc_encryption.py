from cryptography.fernet import Fernet
import base64
import os

# Simulamos clave post-cuántica con Fernet por ahora
key = base64.urlsafe_b64encode(os.urandom(32))
cipher = Fernet(key)

def encrypt_message(message: str) -> str:
    return cipher.encrypt(message.encode()).decode()

def decrypt_message(token: str) -> str:
    return cipher.decrypt(token.encode()).decode()

