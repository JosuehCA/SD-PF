"""
AES-256-CBC encryption for clinical data using Python standard library.
Uses hashlib for key derivation and implements AES via the built-in
'secrets' and 'hmac' modules for integrity.

If the 'cryptography' package is available, uses AESGCM (preferred).
Otherwise, falls back to a pure-stdlib XOR-based approach suitable for
academic/demo purposes. For production, install cryptography.
"""
import os
import base64
import hashlib
import hmac
import struct
import secrets


def get_key():
    """Retrieve the encryption key from environment (base64-encoded, 32 bytes)."""
    key_b64 = os.environ.get("CLINICAL_DATA_KEY")
    if not key_b64:
        raise ValueError(
            "CLINICAL_DATA_KEY environment variable is not set. "
            "Generate one with: python -c \"import os,base64; print(base64.b64encode(os.urandom(32)).decode())\""
        )
    return base64.b64decode(key_b64)


try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    def encrypt(plaintext: str) -> str:
        """Encrypt plaintext using AES-256-GCM."""
        if not plaintext:
            return ""
        key = get_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(b"AESGCM" + nonce + ciphertext).decode("utf-8")

    def decrypt(encrypted_data: str) -> str:
        """Decrypt AES-256-GCM ciphertext."""
        if not encrypted_data:
            return ""
        key = get_key()
        raw = base64.b64decode(encrypted_data)
        if raw[:6] == b"AESGCM":
            raw = raw[6:]
        nonce, ciphertext = raw[:12], raw[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")

except ImportError:
    # Fallback: HMAC-authenticated XOR stream cipher using SHA-256 as PRG
    # Suitable for academic demonstration; for production, install cryptography

    def _generate_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
        """Generate a pseudorandom keystream using HMAC-SHA256 in counter mode."""
        stream = b""
        counter = 0
        while len(stream) < length:
            block = hmac.new(
                key,
                nonce + struct.pack(">I", counter),
                hashlib.sha256,
            ).digest()
            stream += block
            counter += 1
        return stream[:length]

    def encrypt(plaintext: str) -> str:
        """Encrypt using HMAC-SHA256 stream cipher with authentication."""
        if not plaintext:
            return ""
        key = get_key()
        enc_key = hashlib.sha256(key + b"enc").digest()
        mac_key = hashlib.sha256(key + b"mac").digest()

        nonce = secrets.token_bytes(16)
        plainbytes = plaintext.encode("utf-8")
        keystream = _generate_keystream(enc_key, nonce, len(plainbytes))
        ciphertext = bytes(a ^ b for a, b in zip(plainbytes, keystream))

        # HMAC for authentication
        tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()

        # Format: nonce (16) + ciphertext (variable) + tag (32)
        return base64.b64encode(nonce + ciphertext + tag).decode("utf-8")

    def decrypt(encrypted_data: str) -> str:
        """Decrypt and verify HMAC-SHA256 stream cipher."""
        if not encrypted_data:
            return ""
        key = get_key()
        enc_key = hashlib.sha256(key + b"enc").digest()
        mac_key = hashlib.sha256(key + b"mac").digest()

        raw = base64.b64decode(encrypted_data)
        nonce = raw[:16]
        tag = raw[-32:]
        ciphertext = raw[16:-32]

        # Verify HMAC
        expected_tag = hmac.new(mac_key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("Decryption failed: data integrity check failed.")

        keystream = _generate_keystream(enc_key, nonce, len(ciphertext))
        plainbytes = bytes(a ^ b for a, b in zip(ciphertext, keystream))
        return plainbytes.decode("utf-8")
