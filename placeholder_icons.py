from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

# Generate the private key
private_key = ec.generate_private_key(ec.SECP256R1())

# Get the public key
public_key = private_key.public_key()

# Convert private key to bytes
private_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Convert public key to bytes
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

# Base64 encode the keys
private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8')
public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8')

print(f"VAPID_PRIVATE_KEY = '{private_key_b64}'")
print(f"VAPID_PUBLIC_KEY = '{public_key_b64}'")