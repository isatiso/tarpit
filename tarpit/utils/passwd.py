# coding:utf-8
"""Some function to generate code."""
import random
import time
import string
import hmac

pool = string.ascii_letters + string.digits


def generate_id():
    stamp = hex(int(time.time()))[2:]
    rand = ''.join(random.choice(pool) for _ in range(8))
    return rand + stamp


def encode_passwd(mixin, passwd):
    return hmac.new(mixin.encode(), passwd.encode()).hexdigest()
