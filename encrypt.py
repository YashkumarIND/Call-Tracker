from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

load_dotenv()

try:
    # Retrieve the FERNET_KEY environment variable
    fernet_key_str = os.getenv("FERNET_KEY")

    # Check if the key is None or empty
    if not fernet_key_str:
        raise ValueError("FERNET_KEY environment variable is missing or empty")

    # Ensure the equal sign is at the end of the key string
    if fernet_key_str[-1] != '=':
        fernet_key_str += '='

    # Convert the string key to bytes
    fernet_key = fernet_key_str.encode()

    # Create a Fernet cipher suite with the key
    cipher_suite = Fernet(fernet_key)

    # Encryption and decryption functions
    def encrypt_data(data):
        encrypted_data = cipher_suite.encrypt(data.encode())
        return encrypted_data

    def decrypt_data(encrypted_data):
        decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
        return decrypted_data

except ValueError as ve:
    print("ValueError initializing Fernet cipher suite:", ve)
except Exception as e:
    print("Error initializing Fernet cipher suite:", e)
