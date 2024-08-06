import os

# Generate a random 24-byte secret key
secret_key = os.urandom(24)

# Print the key in a format that can be used in your configuration
print(secret_key.hex())
