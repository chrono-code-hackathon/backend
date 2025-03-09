import time
import cryptography.hazmat.primitives.serialization as serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import base64
import json

# GitHub App credentials
APP_ID = 1169954  # Your GitHub App ID

# Load the Private Key from the downloaded .pem file
with open("key.pem", "r") as key_file:
    PRIVATE_KEY = key_file.read()

# Parse the private key
private_key = serialization.load_pem_private_key(
    PRIVATE_KEY.encode(),
    password=None
)

# Create JWT header
header = {
    "alg": "RS256",
    "typ": "JWT"
}

# Create JWT payload
payload = {
    "iat": int(time.time()),  # Issued at time
    "exp": int(time.time()) + 600,  # Expiration (10 minutes)
    "iss": APP_ID  # GitHub App ID
}

# Encode header and payload
header_json = json.dumps(header, separators=(',', ':')).encode()
payload_json = json.dumps(payload, separators=(',', ':')).encode()

header_b64 = base64.urlsafe_b64encode(header_json).decode().rstrip('=')
payload_b64 = base64.urlsafe_b64encode(payload_json).decode().rstrip('=')

# Create the message to sign
message = f"{header_b64}.{payload_b64}"

# Sign the message
signature = private_key.sign(
    message.encode(),
    padding.PKCS1v15(),
    hashes.SHA256()
)

# Encode the signature
signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')

# Create the JWT token
jwt_token = f"{message}.{signature_b64}"

print(f"JWT Token: {jwt_token}")