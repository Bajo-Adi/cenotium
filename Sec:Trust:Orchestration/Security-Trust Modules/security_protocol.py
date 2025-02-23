from cryptography.fernet import Fernet
import hmac
import hashlib
import json
from typing import Dict
from datetime import datetime


class SecurityProtocol:
    """
    Handles encryption, decryption, and message signing for secure agent communication.
    
    This class provides cryptographic operations for securing inter-agent messages using
    Fernet symmetric encryption and HMAC-SHA256 signatures.
    
    Attributes:
        key (bytes): The current Fernet encryption key
        cipher_suite (Fernet): Instance of Fernet cipher for encryption/decryption
        trusted_keys (Dict[str, bytes]): Historical keys for message decryption
        signing_key (bytes): Key used for message signing
    """
    
    def __init__(self):
        """
        Initializes the SecurityProtocol with new encryption keys and cipher suite.
        """
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        self.trusted_keys: Dict[str, bytes] = {}
        self.signing_key = b"your-signing-key"
        
    def encrypt_message(self, message: dict) -> bytes:
        """
        Encrypts a dictionary message using Fernet symmetric encryption.
        
        Args:
            message (dict): The message to encrypt
            
        Returns:
            bytes: The encrypted message
            
        Raises:
            ValueError: If message cannot be serialized
        """
        message_bytes = json.dumps(message).encode()
        return self.cipher_suite.encrypt(message_bytes)
    
    def decrypt_message(self, encrypted_message: bytes) -> dict:
        """
        Decrypts a Fernet-encrypted message back to dictionary.
        
        Args:
            encrypted_message (bytes): The encrypted message
            
        Returns:
            dict: The decrypted message
            
        Raises:
            InvalidToken: If the message is invalid or tampered with
        """
        decrypted_bytes = self.cipher_suite.decrypt(encrypted_message)
        return json.loads(decrypted_bytes)
    
    def sign_message(self, message: dict) -> str:
        """
        Creates a digital signature for a message using HMAC-SHA256.
        
        Args:
            message (dict): The message to sign
            
        Returns:
            str: Hexadecimal signature string
        """
        message_bytes = json.dumps(message, sort_keys=True).encode()
        signature = hmac.new(self.signing_key, message_bytes, hashlib.sha256)
        return signature.hexdigest()
    
    def verify_signature(self, message: dict, signature: str) -> bool:
        """
        Verifies a message's digital signature.
        
        Args:
            message (dict): The message to verify
            signature (str): The signature to check
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        expected_signature = self.sign_message(message)
        return hmac.compare_digest(signature, expected_signature)

    def rotate_keys(self):
        """
        Rotates encryption keys for enhanced security.
        
        Generates a new key and stores the old key in trusted_keys with timestamp.
        Old keys are retained for decrypting historical messages.
        """
        new_key = Fernet.generate_key()
        old_key = self.key
        self.trusted_keys[datetime.now().isoformat()] = old_key
        self.key = new_key
        self.cipher_suite = Fernet(new_key)
    