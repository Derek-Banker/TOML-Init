import base64
import logging
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionManager:
    DEFAULT_SALT_SIZE: int  = 16
    DEFAULT_ITERATIONS: int = 100_000

    def __init__(
        self,
        salt_b64: str | None = None,
        key_b64: str | None = None,
        logger: logging.Logger | None = None
    ) -> None:
        self.salt_b64 = salt_b64
        self.key_b64 = key_b64
        if logger is None:
            self.logger = logging.getLogger(__name__)
        elif isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            raise TypeError("Provided parameter `logger` is not a valid instance of `logging.Logger`.")

    @staticmethod
    def generate_salt(length: int = DEFAULT_SALT_SIZE) -> str:
        """Generate a new random salt and return as base64 string."""
        return base64.b64encode(os.urandom(length)).decode("ascii")

    @staticmethod
    def derive_key(password: str, salt_b64: str, iterations: int = DEFAULT_ITERATIONS) -> str:
        """Derive a base64-encoded Fernet key from a password and base64 salt."""
        salt = base64.b64decode(salt_b64)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode("ascii")  # Fernet expects key as base64 string

    def set_salt(self, salt_b64: str) -> None:
        """Set the instance's salt."""
        self.salt_b64 = salt_b64

    def set_key(self, key_b64: str) -> None:
        """Set the instance's derived key."""
        self.key_b64 = key_b64

    def encrypt(self, data: str, key_b64: str | None = None) -> str:
        """Encrypt data, returning a base64 string."""
        key = key_b64 or self.key_b64
        if key is None:
            raise ValueError("No key provided and no key set in instance.")
        if not isinstance(data, str):
            raise TypeError("data must be str")
        try:
            fernet = Fernet(key.encode("ascii"))
            encrypted_bytes = fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_bytes).decode("ascii")
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_b64: str, key_b64: str | None = None) -> str:
        """Decrypt base64-encoded data, returning plaintext string."""
        key = key_b64 or self.key_b64
        if key is None:
            raise ValueError("No key provided and no key set in instance.")
        try:
            fernet = Fernet(key.encode("ascii"))
            encrypted_bytes = base64.b64decode(encrypted_b64)
            return fernet.decrypt(encrypted_bytes).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise

    def hash(self, data: str, salt_b64: str | None = None) -> str:
        """Hash data with SHA256 and base64-encoded salt, returning base64 digest."""
        salt = salt_b64 or self.salt_b64
        if salt is None:
            raise ValueError("No salt provided and no salt set in instance.")
        salt_bytes = base64.b64decode(salt)
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(salt_bytes + data.encode())
        return base64.b64encode(digest.finalize()).decode("ascii")
