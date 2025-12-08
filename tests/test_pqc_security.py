"""
OMNIX V6.5.4 - Post-Quantum Cryptography Test Suite
Tests for Kyber-768 (ML-KEM-768) and Dilithium-3 (ML-DSA-65)
NIST FIPS 203 and FIPS 204 compliant
"""

import unittest
import warnings
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings('ignore')


class TestPQCLibrary(unittest.TestCase):
    """Test that pypqc library is installed and functional"""
    
    def test_pypqc_import(self):
        """Test pypqc can be imported"""
        try:
            from pqc.kem import kyber768
            from pqc.sign import dilithium3
            self.assertIsNotNone(kyber768)
            self.assertIsNotNone(dilithium3)
        except ImportError as e:
            self.fail(f"pypqc import failed: {e}")
    
    def test_kyber768_keypair(self):
        """Test Kyber-768 key generation"""
        from pqc.kem import kyber768
        public_key, secret_key = kyber768.keypair()
        self.assertEqual(len(public_key), 1184)
        self.assertEqual(len(secret_key), 2400)
    
    def test_kyber768_encapsulation(self):
        """Test Kyber-768 encapsulation/decapsulation"""
        from pqc.kem import kyber768
        public_key, secret_key = kyber768.keypair()
        shared_secret, ciphertext = kyber768.encap(public_key)
        self.assertEqual(len(shared_secret), 32)
        self.assertEqual(len(ciphertext), 1088)
        decrypted_secret = kyber768.decap(ciphertext, secret_key)
        self.assertEqual(shared_secret, decrypted_secret)
    
    def test_dilithium3_keypair(self):
        """Test Dilithium-3 key generation"""
        from pqc.sign import dilithium3
        public_key, secret_key = dilithium3.keypair()
        self.assertEqual(len(public_key), 1952)
        self.assertEqual(len(secret_key), 4032)
    
    def test_dilithium3_sign_verify(self):
        """Test Dilithium-3 signature and verification"""
        from pqc.sign import dilithium3
        public_key, secret_key = dilithium3.keypair()
        message = b"OMNIX Trading Order: BUY BTC/USD @ $100,000"
        signature = dilithium3.sign(message, secret_key)
        self.assertEqual(len(signature), 3309)
        dilithium3.verify(signature, message, public_key)
    
    def test_dilithium3_tamper_detection(self):
        """Test that tampering is detected"""
        from pqc.sign import dilithium3
        public_key, secret_key = dilithium3.keypair()
        message = b"Original message"
        signature = dilithium3.sign(message, secret_key)
        tampered_message = b"Tampered message"
        with self.assertRaises(Exception):
            dilithium3.verify(signature, tampered_message, public_key)


class TestPostQuantumSecurity(unittest.TestCase):
    """Test the PostQuantumSecurity class"""
    
    def test_pqc_enabled(self):
        """Test that PQC is enabled"""
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        self.assertTrue(pqc.pqc_enabled)
    
    def test_generate_encryption_keypair(self):
        """Test encryption key pair generation"""
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        result = pqc.generate_keypair_encryption()
        self.assertIsNotNone(result)
        public_key, secret_key = result
        self.assertEqual(len(public_key), 1184)
        self.assertEqual(len(secret_key), 2400)
    
    def test_generate_signature_keypair(self):
        """Test signature key pair generation"""
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        result = pqc.generate_keypair_signature()
        self.assertIsNotNone(result)
        public_key, secret_key = result
        self.assertEqual(len(public_key), 1952)
        self.assertEqual(len(secret_key), 4032)
    
    def test_encapsulate_decapsulate(self):
        """Test secret encapsulation/decapsulation"""
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        keypair = pqc.generate_keypair_encryption()
        public_key, secret_key = keypair
        result = pqc.encapsulate_secret(public_key)
        shared_secret, ciphertext = result
        decrypted = pqc.decapsulate_secret(ciphertext, secret_key)
        self.assertEqual(shared_secret, decrypted)
    
    def test_sign_verify_message(self):
        """Test message signing and verification"""
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        keypair = pqc.generate_keypair_signature()
        public_key, secret_key = keypair
        message = b"Test trading order"
        signature = pqc.sign_message(message, secret_key)
        self.assertIsNotNone(signature)
        is_valid = pqc.verify_signature(signature, message, public_key)
        self.assertTrue(is_valid)
    
    def test_sign_trading_order(self):
        """Test trading order signature"""
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        keypair = pqc.generate_keypair_signature()
        public_key, secret_key = keypair
        order = {
            'symbol': 'BTC/USD',
            'type': 'buy',
            'amount': 0.5,
            'price': 100000,
            'timestamp': '2025-12-08T12:00:00Z'
        }
        signature = pqc.sign_trading_order(order, secret_key)
        self.assertIsNotNone(signature)
        is_valid = pqc.verify_trading_order(order, signature, public_key)
        self.assertTrue(is_valid)
    
    def test_security_info(self):
        """Test security info retrieval"""
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        info = pqc.get_security_info()
        self.assertTrue(info['pqc_enabled'])
        self.assertTrue(info['quantum_resistant'])
        self.assertEqual(info['algorithms']['encryption'], 'Kyber-768 (ML-KEM-768)')
        self.assertEqual(info['algorithms']['signature'], 'Dilithium-3 (ML-DSA-65)')


class TestPQCKeySizes(unittest.TestCase):
    """Verify key sizes match NIST specifications"""
    
    def test_kyber768_key_sizes(self):
        """Verify Kyber-768 follows NIST FIPS 203"""
        from pqc.kem import kyber768
        public_key, secret_key = kyber768.keypair()
        self.assertEqual(len(public_key), 1184, "Kyber-768 public key should be 1184 bytes")
        self.assertEqual(len(secret_key), 2400, "Kyber-768 secret key should be 2400 bytes")
        shared_secret, ciphertext = kyber768.encap(public_key)
        self.assertEqual(len(shared_secret), 32, "Shared secret should be 32 bytes (256 bits)")
        self.assertEqual(len(ciphertext), 1088, "Kyber-768 ciphertext should be 1088 bytes")
    
    def test_dilithium3_key_sizes(self):
        """Verify Dilithium-3 follows NIST FIPS 204"""
        from pqc.sign import dilithium3
        public_key, secret_key = dilithium3.keypair()
        self.assertEqual(len(public_key), 1952, "Dilithium-3 public key should be 1952 bytes")
        self.assertEqual(len(secret_key), 4032, "Dilithium-3 secret key should be 4032 bytes")
        message = b"Test"
        signature = dilithium3.sign(message, secret_key)
        self.assertEqual(len(signature), 3309, "Dilithium-3 signature should be 3309 bytes")


def run_pqc_health_check():
    """Run PQC health check for CI/CD pipeline"""
    print("=" * 60)
    print("OMNIX V6.5.4 - Post-Quantum Cryptography Health Check")
    print("=" * 60)
    
    try:
        from pqc.kem import kyber768
        from pqc.sign import dilithium3
        print("✅ pypqc library: INSTALLED")
    except ImportError:
        print("❌ pypqc library: NOT AVAILABLE")
        return False
    
    try:
        public_key, secret_key = kyber768.keypair()
        shared_secret, ciphertext = kyber768.encap(public_key)
        decrypted = kyber768.decap(ciphertext, secret_key)
        assert shared_secret == decrypted
        print(f"✅ Kyber-768 (ML-KEM-768): FUNCTIONAL")
        print(f"   Public Key: {len(public_key)} bytes")
        print(f"   Secret Key: {len(secret_key)} bytes")
        print(f"   Ciphertext: {len(ciphertext)} bytes")
    except Exception as e:
        print(f"❌ Kyber-768: FAILED - {e}")
        return False
    
    try:
        pub_sign, sec_sign = dilithium3.keypair()
        message = b"OMNIX Trading Order Verification"
        signature = dilithium3.sign(message, sec_sign)
        dilithium3.verify(signature, message, pub_sign)
        print(f"✅ Dilithium-3 (ML-DSA-65): FUNCTIONAL")
        print(f"   Public Key: {len(pub_sign)} bytes")
        print(f"   Secret Key: {len(sec_sign)} bytes")
        print(f"   Signature: {len(signature)} bytes")
    except Exception as e:
        print(f"❌ Dilithium-3: FAILED - {e}")
        return False
    
    try:
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        if pqc.pqc_enabled:
            print("✅ PostQuantumSecurity: ENABLED")
        else:
            print("❌ PostQuantumSecurity: DISABLED")
            return False
    except Exception as e:
        print(f"❌ PostQuantumSecurity: FAILED - {e}")
        return False
    
    print("=" * 60)
    print("🎉 PQC HEALTH CHECK PASSED - System is Quantum-Resistant")
    print("   NIST Standards: FIPS 203 (ML-KEM) + FIPS 204 (ML-DSA)")
    print("=" * 60)
    return True


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--health':
        success = run_pqc_health_check()
        sys.exit(0 if success else 1)
    else:
        unittest.main(verbosity=2)
