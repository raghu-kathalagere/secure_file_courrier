from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes

# ========== RSA ==========

def generate_rsa_keypair(bits: int = 2048):
    """
    Generate a new RSA keypair.
    Returns (public_pem_str, private_pem_str).
    """
    key = RSA.generate(bits)
    private_pem = key.export_key().decode("utf-8")
    public_pem = key.publickey().export_key().decode("utf-8")
    return public_pem, private_pem

def encrypt_file_key_for_user(file_key: bytes, public_key_pem: str) -> bytes:
    """
    Encrypt the AES file key using the user's RSA public key (PKCS1-OAEP).
    """
    public_key = RSA.import_key(public_key_pem)
    cipher_rsa = PKCS1_OAEP.new(public_key)
    encrypted_key = cipher_rsa.encrypt(file_key)
    return encrypted_key

def decrypt_file_key_for_user(encrypted_file_key: bytes, private_key_pem: str) -> bytes:
    """
    Decrypt the AES file key using the user's RSA private key.
    """
    private_key = RSA.import_key(private_key_pem)
    cipher_rsa = PKCS1_OAEP.new(private_key)
    file_key = cipher_rsa.decrypt(encrypted_file_key)
    return file_key

# ========== AES-GCM ==========

def generate_aes_key(length: int = 32) -> bytes:
    """
    Generate a random AES key (default 256-bit = AES-256).
    """
    return get_random_bytes(length)

def aes_gcm_encrypt(plaintext: bytes, key: bytes):
    """
    Encrypt plaintext using AES-256-GCM.
    Returns (ciphertext, nonce, tag).
    """
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return ciphertext, cipher.nonce, tag

def aes_gcm_decrypt(ciphertext: bytes, key: bytes, nonce: bytes, tag: bytes) -> bytes:
    """
    Decrypt ciphertext using AES-256-GCM.
    Raises ValueError if authentication fails.
    """
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext

def aes_gcm_encrypt_to_blob(plaintext: bytes, key: bytes) -> bytes:
    """
    Encrypt plaintext and return a single blob: nonce | tag | ciphertext.
    nonce (16 bytes) + tag (16 bytes) + ciphertext.
    """
    ciphertext, nonce, tag = aes_gcm_encrypt(plaintext, key)
    return nonce + tag + ciphertext

def aes_gcm_decrypt_from_blob(blob: bytes, key: bytes) -> bytes:
    """
    Decrypt a blob of the format: nonce | tag | ciphertext.
    Assumes nonce = 16 bytes, tag = 16 bytes.
    """
    if len(blob) < 32:
        raise ValueError("Invalid encrypted blob")
    nonce = blob[:16]
    tag = blob[16:32]
    ciphertext = blob[32:]
    return aes_gcm_decrypt(ciphertext, key, nonce, tag)
