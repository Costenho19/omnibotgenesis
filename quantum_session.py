# quantum_session.py

import os
import hashlib
import uuid
from datetime import datetime
from pqc_encryption import PQCEncryption
from database import guardar_sesion_cuantica, obtener_sesion_cuantica

pqc = PQCEncryption()

def generar_session_id(user_id: str) -> str:
    """Genera un ID de sesión único con hash SHA-512."""
    raw = f"{user_id}-{uuid.uuid4()}-{datetime.utcnow().isoformat()}"
    return hashlib.sha512(raw.encode()).hexdigest()

def firmar_session(user_id: str, session_id: str) -> bytes:
    """Firma el ID de sesión con Dilithium."""
    return pqc.sign_with_dilithium(session_id.encode())

def verificar_session(user_id: str, session_id: str, firma: bytes) -> bool:
    """Verifica la firma cuántica para la sesión actual."""
    return pqc.verify_dilithium_signature(session_id.encode(), firma)

def nueva_sesion_segura(user_id: str):
    """Genera, firma y guarda una nueva sesión segura."""
    session_id = generar_session_id(user_id)
    firma = firmar_session(user_id, session_id)
    guardar_sesion_cuantica(user_id, session_id, firma)
    return session_id, firma

def sesion_valida(user_id: str):
    """Verifica si la sesión actual del usuario es válida."""
    datos = obtener_sesion_cuantica(user_id)
    if not datos:
        return False
    session_id, firma = datos
    return verificar_session(user_id, session_id, firma)
