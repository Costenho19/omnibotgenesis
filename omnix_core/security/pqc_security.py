"""
OMNIX V5.1 - POST-QUANTUM CRYPTOGRAPHY MODULE
==============================================
Implementación de seguridad post-cuántica usando estándares NIST 2024
- ML-KEM-768 (Kyber-768) para encriptación de claves
- ML-DSA-65 (Dilithium-3) para firmas digitales

Creado: Noviembre 2025
Autor: Harold Nunes - OMNIX Team
Estándares: NIST FIPS 203 y FIPS 204
"""

import json
import base64
import logging
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
import hashlib

try:
    from pqc.kem import kyber768
    from pqc.sign import dilithium3
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False
    kyber768 = None  # type: ignore
    dilithium3 = None  # type: ignore
    logging.warning("⚠️ pypqc no disponible - Seguridad PQC desactivada")


class PostQuantumSecurity:
    """
    Sistema de seguridad post-cuántica para OMNIX
    Protege contra ataques de computadoras cuánticas
    """
    
    def __init__(self):
        self.logger = logging.getLogger("OMNIX.PQC")
        self.pqc_enabled = PQC_AVAILABLE
        self.version = "1.0.0"
        self.nist_standard = "FIPS 203 (ML-KEM) + FIPS 204 (ML-DSA)"
        
        if self.pqc_enabled:
            self.logger.info("🔐 POST-QUANTUM CRYPTOGRAPHY ACTIVADA")
            self.logger.info(f"📜 Estándar: {self.nist_standard}")
            self.logger.info("🔑 Kyber-768 (ML-KEM-768) - Encriptación")
            self.logger.info("✍️ Dilithium-3 (ML-DSA-65) - Firmas Digitales")
        else:
            self.logger.error("❌ PQC NO DISPONIBLE - Instalar: pip install pypqc")
    
    def generate_keypair_encryption(self) -> Optional[Tuple[bytes, bytes]]:
        """
        Genera par de claves para encriptación usando Kyber-768
        
        Returns:
            (public_key, secret_key) o None si hay error
        """
        if not self.pqc_enabled:
            self.logger.error("❌ PQC no disponible")
            return None
        
        try:
            public_key, secret_key = kyber768.keypair()
            self.logger.info("✅ Par de claves Kyber-768 generado")
            self.logger.info(f"   📏 Clave pública: {len(public_key)} bytes")
            self.logger.info(f"   📏 Clave secreta: {len(secret_key)} bytes")
            return public_key, secret_key
        except Exception as e:
            self.logger.error(f"❌ Error generando claves Kyber: {e}")
            return None
    
    def encapsulate_secret(self, public_key: bytes) -> Optional[Tuple[bytes, bytes]]:
        """
        Encapsula un secreto compartido usando la clave pública del receptor
        
        Args:
            public_key: Clave pública Kyber-768 del receptor
        
        Returns:
            (shared_secret, ciphertext) o None si hay error
        """
        if not self.pqc_enabled:
            self.logger.error("❌ PQC no disponible")
            return None
        
        try:
            shared_secret, ciphertext = kyber768.encap(public_key)
            self.logger.info("✅ Secreto encapsulado con Kyber-768")
            self.logger.info(f"   📏 Secreto compartido: {len(shared_secret)} bytes")
            self.logger.info(f"   📏 Texto cifrado: {len(ciphertext)} bytes")
            return shared_secret, ciphertext
        except Exception as e:
            self.logger.error(f"❌ Error encapsulando secreto: {e}")
            return None
    
    def decapsulate_secret(self, ciphertext: bytes, secret_key: bytes) -> Optional[bytes]:
        """
        Desencapsula el secreto compartido usando la clave secreta
        
        Args:
            ciphertext: Texto cifrado recibido
            secret_key: Clave secreta Kyber-768 propia
        
        Returns:
            shared_secret o None si hay error
        """
        if not self.pqc_enabled:
            self.logger.error("❌ PQC no disponible")
            return None
        
        try:
            shared_secret = kyber768.decap(ciphertext, secret_key)
            self.logger.info("✅ Secreto desencapsulado con Kyber-768")
            return shared_secret
        except Exception as e:
            self.logger.error(f"❌ Error desencapsulando secreto: {e}")
            return None
    
    def generate_keypair_signature(self) -> Optional[Tuple[bytes, bytes]]:
        """
        Genera par de claves para firmas digitales usando Dilithium-3
        
        Returns:
            (public_key, secret_key) o None si hay error
        """
        if not self.pqc_enabled:
            self.logger.error("❌ PQC no disponible")
            return None
        
        try:
            public_key, secret_key = dilithium3.keypair()
            self.logger.info("✅ Par de claves Dilithium-3 generado")
            self.logger.info(f"   📏 Clave pública: {len(public_key)} bytes")
            self.logger.info(f"   📏 Clave secreta: {len(secret_key)} bytes")
            return public_key, secret_key
        except Exception as e:
            self.logger.error(f"❌ Error generando claves Dilithium: {e}")
            return None
    
    def sign_message(self, message: bytes, secret_key: bytes) -> Optional[bytes]:
        """
        Firma un mensaje usando Dilithium-3
        
        Args:
            message: Mensaje a firmar
            secret_key: Clave secreta Dilithium-3
        
        Returns:
            signature o None si hay error
        """
        if not self.pqc_enabled:
            self.logger.error("❌ PQC no disponible")
            return None
        
        try:
            signature = dilithium3.sign(message, secret_key)
            self.logger.info("✅ Mensaje firmado con Dilithium-3")
            self.logger.info(f"   📏 Firma: {len(signature)} bytes")
            return signature
        except Exception as e:
            self.logger.error(f"❌ Error firmando mensaje: {e}")
            return None
    
    def verify_signature(self, signature: bytes, message: bytes, public_key: bytes) -> bool:
        """
        Verifica una firma digital usando Dilithium-3
        
        Args:
            signature: Firma a verificar
            message: Mensaje original
            public_key: Clave pública Dilithium-3 del firmante
        
        Returns:
            True si la firma es válida, False en caso contrario
        """
        if not self.pqc_enabled:
            self.logger.error("❌ PQC no disponible")
            return False
        
        try:
            dilithium3.verify(signature, message, public_key)
            self.logger.info("✅ Firma verificada correctamente")
            return True
        except Exception as e:
            self.logger.error(f"❌ Firma inválida: {e}")
            return False
    
    def secure_api_key(self, api_key: str, public_key: bytes) -> Optional[Dict[str, str]]:
        """
        Encripta una API key usando PQC para transmisión segura
        
        Args:
            api_key: API key a proteger
            public_key: Clave pública del receptor
        
        Returns:
            Dict con ciphertext y shared_secret encriptado, o None si hay error
        """
        if not self.pqc_enabled:
            self.logger.error("❌ PQC no disponible")
            return None
        
        try:
            result = self.encapsulate_secret(public_key)
            if not result:
                return None
            
            shared_secret, ciphertext = result
            
            key_hash = hashlib.sha256(shared_secret).digest()
            encrypted_key = bytes(a ^ b for a, b in zip(api_key.encode(), key_hash[:len(api_key)]))
            
            return {
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'encrypted_key': base64.b64encode(encrypted_key).decode('utf-8'),
                'timestamp': datetime.now().isoformat(),
                'algorithm': 'Kyber-768 (ML-KEM-768)'
            }
        except Exception as e:
            self.logger.error(f"❌ Error protegiendo API key: {e}")
            return None
    
    def sign_trading_order(self, order_data: Dict[str, Any], secret_key: bytes) -> Optional[str]:
        """
        Firma una orden de trading para garantizar autenticidad
        
        Args:
            order_data: Datos de la orden de trading
            secret_key: Clave secreta Dilithium-3
        
        Returns:
            Firma en base64 o None si hay error
        """
        if not self.pqc_enabled:
            self.logger.error("❌ PQC no disponible")
            return None
        
        try:
            order_json = json.dumps(order_data, sort_keys=True).encode('utf-8')
            signature = self.sign_message(order_json, secret_key)
            
            if signature:
                self.logger.info(f"✅ Orden de trading firmada: {order_data.get('symbol', 'N/A')}")
                return base64.b64encode(signature).decode('utf-8')
            return None
        except Exception as e:
            self.logger.error(f"❌ Error firmando orden: {e}")
            return None
    
    def verify_trading_order(self, order_data: Dict[str, Any], signature_b64: str, public_key: bytes) -> bool:
        """
        Verifica la autenticidad de una orden de trading
        
        Args:
            order_data: Datos de la orden
            signature_b64: Firma en base64
            public_key: Clave pública del firmante
        
        Returns:
            True si la orden es auténtica, False en caso contrario
        """
        if not self.pqc_enabled:
            self.logger.error("❌ PQC no disponible")
            return False
        
        try:
            order_json = json.dumps(order_data, sort_keys=True).encode('utf-8')
            signature = base64.b64decode(signature_b64)
            
            is_valid = self.verify_signature(signature, order_json, public_key)
            
            if is_valid:
                self.logger.info(f"✅ Orden verificada: {order_data.get('symbol', 'N/A')}")
            else:
                self.logger.warning(f"⚠️ Orden inválida: {order_data.get('symbol', 'N/A')}")
            
            return is_valid
        except Exception as e:
            self.logger.error(f"❌ Error verificando orden: {e}")
            return False
    
    def get_security_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el estado de seguridad PQC
        
        Returns:
            Diccionario con información del sistema PQC
        """
        return {
            'pqc_enabled': self.pqc_enabled,
            'version': self.version,
            'nist_standard': self.nist_standard,
            'algorithms': {
                'encryption': 'Kyber-768 (ML-KEM-768)',
                'signature': 'Dilithium-3 (ML-DSA-65)'
            },
            'security_level': {
                'kyber768': 'AES-192 equivalent (~Level 3)',
                'dilithium3': 'NIST Level 3 (~192-bit classical security)'
            },
            'key_sizes': {
                'kyber768_public': '1184 bytes',
                'kyber768_secret': '2400 bytes',
                'kyber768_ciphertext': '1088 bytes',
                'dilithium3_public': '1952 bytes',
                'dilithium3_secret': '4000 bytes',
                'dilithium3_signature': '~3309 bytes'
            },
            'quantum_resistant': True,
            'nist_approved': True,
            'production_ready': True
        }


def demo_pqc_encryption():
    """Demostración de encriptación post-cuántica"""
    print("\n" + "="*70)
    print("🔐 DEMOSTRACIÓN: ENCRIPTACIÓN POST-CUÁNTICA (Kyber-768)")
    print("="*70)
    
    pqc = PostQuantumSecurity()
    
    if not pqc.pqc_enabled:
        print("❌ PQC no disponible")
        return
    
    print("\n1️⃣ Generando par de claves del receptor...")
    result = pqc.generate_keypair_encryption()
    if not result:
        return
    public_key, secret_key = result
    
    print("\n2️⃣ Encapsulando secreto compartido...")
    result = pqc.encapsulate_secret(public_key)
    if not result:
        return
    shared_secret_sender, ciphertext = result
    
    print("\n3️⃣ Desencapsulando secreto compartido...")
    shared_secret_receiver = pqc.decapsulate_secret(ciphertext, secret_key)
    
    if shared_secret_sender == shared_secret_receiver:
        print("✅ ¡ÉXITO! Secretos coinciden - Comunicación segura establecida")
        print(f"   Secreto compartido: [REDACTED] ({len(shared_secret_sender)} bytes)")
    else:
        print("❌ ERROR: Secretos no coinciden")


def demo_pqc_signatures():
    """Demostración de firmas digitales post-cuánticas"""
    print("\n" + "="*70)
    print("✍️ DEMOSTRACIÓN: FIRMAS DIGITALES POST-CUÁNTICAS (Dilithium-3)")
    print("="*70)
    
    pqc = PostQuantumSecurity()
    
    if not pqc.pqc_enabled:
        print("❌ PQC no disponible")
        return
    
    print("\n1️⃣ Generando par de claves para firmas...")
    result = pqc.generate_keypair_signature()
    if not result:
        return
    public_key, secret_key = result
    
    message = b"OMNIX Trading Order: BUY BTC/USD 0.1 @ $50000"
    print(f"\n2️⃣ Firmando mensaje: {message.decode()}")
    signature = pqc.sign_message(message, secret_key)
    
    if not signature:
        return
    
    print("\n3️⃣ Verificando firma...")
    is_valid = pqc.verify_signature(signature, message, public_key)
    
    if is_valid:
        print("✅ ¡ÉXITO! Firma válida - Mensaje auténtico")
    else:
        print("❌ ERROR: Firma inválida")
    
    print("\n4️⃣ Intentando verificar con mensaje alterado...")
    fake_message = b"OMNIX Trading Order: BUY BTC/USD 100 @ $50000"
    is_valid_fake = pqc.verify_signature(signature, fake_message, public_key)
    
    if not is_valid_fake:
        print("✅ ¡CORRECTO! Firma rechazada - Sistema detectó manipulación")
    else:
        print("❌ ERROR: Sistema vulnerable")


def demo_trading_order_signature():
    """Demostración de firma de órdenes de trading"""
    print("\n" + "="*70)
    print("📊 DEMOSTRACIÓN: FIRMA DE ÓRDENES DE TRADING")
    print("="*70)
    
    pqc = PostQuantumSecurity()
    
    if not pqc.pqc_enabled:
        print("❌ PQC no disponible")
        return
    
    print("\n1️⃣ Generando claves de trading...")
    result = pqc.generate_keypair_signature()
    if not result:
        return
    public_key, secret_key = result
    
    order = {
        'symbol': 'BTC/USD',
        'type': 'buy',
        'amount': 0.5,
        'price': 50000,
        'timestamp': datetime.now().isoformat(),
        'user_id': 'harold_nunes'
    }
    
    print(f"\n2️⃣ Firmando orden de trading...")
    print(f"   Symbol: {order['symbol']}")
    print(f"   Type: {order['type'].upper()}")
    print(f"   Amount: {order['amount']} BTC")
    print(f"   Price: ${order['price']}")
    
    signature = pqc.sign_trading_order(order, secret_key)
    
    if not signature:
        return
    
    print(f"\n   Firma generada: {signature[:50]}...")
    
    print("\n3️⃣ Verificando orden...")
    is_valid = pqc.verify_trading_order(order, signature, public_key)
    
    if is_valid:
        print("✅ Orden auténtica - APROBADA para ejecución")
    else:
        print("❌ Orden inválida - RECHAZADA")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    print("\n" + "🚀"*35)
    print("OMNIX V5.1 - SISTEMA DE SEGURIDAD POST-CUÁNTICA")
    print("Protección contra computadoras cuánticas")
    print("Estándares NIST 2024: FIPS 203 + FIPS 204")
    print("🚀"*35)
    
    pqc = PostQuantumSecurity()
    
    if pqc.pqc_enabled:
        info = pqc.get_security_info()
        print("\n📋 INFORMACIÓN DEL SISTEMA:")
        print(json.dumps(info, indent=2))
        
        demo_pqc_encryption()
        demo_pqc_signatures()
        demo_trading_order_signature()
        
        print("\n" + "="*70)
        print("✅ TODAS LAS DEMOSTRACIONES COMPLETADAS")
        print("🔐 OMNIX está protegido contra ataques cuánticos")
        print("="*70 + "\n")
    else:
        print("\n❌ Sistema PQC no disponible")
        print("Instalar con: pip install pypqc\n")
