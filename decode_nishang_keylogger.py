#!/usr/bin/env python3

# Decode Nishang Keylogger exfill data
# Right now you need to manually copy the encoded 
# text into the variable...

import base64
import zlib

def decode_text(encoded_text):
    # Decode base64-encoded string
    decoded_text = base64.b64decode(encoded_text)
    
    # Decompress zlib-compressed data
    decompressed_text = zlib.decompress(decoded_text, -15)
    
    # Return the decoded and decompressed string as a UTF-8 string
    return decompressed_text.decode('utf-8')

encoded_text = 'rU/JDcAgDPtX6g5dAIkz0DnYf5cqiSlE4tFHH7lsx4HuqF3n0V1LUqpfJ3ACBoaCshDdWrKKohYFK28Wlqe40hCPIsa3vQlX6GmCcBqMX+9hWXytbvjh6cWAeS43hPXC9H5eonIi2NeBkiT/qZ0OP7Rr7M9tWDs+'
decoded_text = decode_text(encoded_text)
print(decoded_text)
