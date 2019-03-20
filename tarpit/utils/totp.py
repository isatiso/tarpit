import base64
import struct
import hmac
import hashlib
import time
import random


def get_hotp_token(secret, intervals_no):
    key = base64.b32decode(secret, True)
    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    h = (struct.unpack(">I", h[o:o + 4])[0] & 0x7fffffff) % 1000000
    return f'{h:06d}'


def get_totp_token(secret):
    return get_hotp_token(secret, intervals_no=int(time.time()) // 30)

def get_totp_secret():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567', k=16))
