import uos
from ucryptolib import aes
 
MODE_CBC = 2
BLOCK_SIZE = 16
 
# key size must be 16 or 32
key = b"q\x06\xfd\xc1\x01'\x8a<\x1bV\xf0\xf4\xda\x0e\xf05q\x17Ws\x16\x18\xbfqL\x10\x9c\xe0\xed\x11F\xa1"
iv = b'gf4]\xd8\xf27Tg\xa7\xf5\xfdb,\xf6\xc3'
 
###################################################
#             AES ECB Cryptographic               #
###################################################
 
plaintext = 'w;somewifi'
print('Plain Text:', plaintext)
 
# Padding plain text with space 
pad = BLOCK_SIZE - len(plaintext) % BLOCK_SIZE
plaintext = plaintext + " "*pad
 
# Generate iv with HW random generator 
# iv = uos.urandom(BLOCK_SIZE)
cipher = aes(key,MODE_CBC,iv)
 
ct_bytes = iv + cipher.encrypt(plaintext)
print ('AES-CBC encrypted:', ct_bytes)
 
iv = ct_bytes[:BLOCK_SIZE]
cipher = aes(key,MODE_CBC,iv)
decrypted = cipher.decrypt(ct_bytes)[BLOCK_SIZE:]
print('AES-CBC decrypted:', decrypted.strip())
