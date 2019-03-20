# coding:utf-8
"""Some function to generate code."""
import random
import time
import string
import hmac

from tarpit.config import CONFIG as O_O

pool = string.ascii_letters + string.digits


def rand6():
    return ''.join(random.choice(pool) for _ in range(6))


def rand12():
    rand = ''.join(random.choice(pool) for _ in range(8))
    stamp = hex(int(time.time()))[-4:]
    return rand + stamp


def generate_id():
    stamp = hex(int(time.time()))[2:]
    rand = ''.join(random.choice(pool) for _ in range(8))
    return rand + stamp


def encode_passwd(passwd):
    return hmac.new(O_O.server.pass_mixin.encode('utf-8'),
                    passwd.encode()).hexdigest()


def encode_msg(code, timestamp, user_id):
    return hmac.new(code.encode(),
                    (str(timestamp) + str(user_id)).encode()).hexdigest()
