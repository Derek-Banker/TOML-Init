import logging
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionManager:
    DEFAULT_SALT_SIZE = 16
    DEFAULT_ITERATIONS = 100_000

    def __init__(self,
                 logger: logging.Logger | None = None
                 ) -> None:
        
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            if isinstance(logger, logging.Logger):
                self.logger = logger
            else:
                raise TypeError("Provided parameter `logger` is not a valid instance of `logging.Logger`.")

    @staticmethod
    def generate_salt(length: int = DEFAULT_SALT_SIZE) -> bytes:
        return os.urandom(length)

    @staticmethod
    def derive_key(password: str, 
                   salt: bytes, 
                   iterations: int = DEFAULT_ITERATIONS
                  ) -> bytes:
        """Derives a Fernet-compatible key from a password and salt."""

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt(self, 
                data: str, 
                key: bytes
               ) -> bytes:
        """Encrypt a string using the supplied key."""

        if not isinstance(data, str) or not isinstance(key, bytes):
            raise TypeError("data must be str and key must be bytes")
        try:
            fernet = Fernet(key)
            return fernet.encrypt(data.encode())
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, 
                token: bytes, 
                key: bytes
               ) -> str:
        """Decrypt a token using the supplied key."""

        if not isinstance(token, bytes) or not isinstance(key, bytes):
            raise TypeError("token and key must be bytes")
        try:
            fernet = Fernet(key)
            return fernet.decrypt(token).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise

    @staticmethod
    def hash(data: str, 
             salt: bytes
            ) -> bytes:
        """Hash data with SHA256 and a salt."""
        
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(salt + data.encode())
        return digest.finalize()
