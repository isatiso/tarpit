# coding:utf-8
"""Some Verify Function."""
import re

PATTERN = dict(
    email=re.compile(r'^([\w\-.]+)@([\w-]+)(\.([\w-]+))+$'),
    password=re.compile(
        r'^[0-9A-Za-z`~!@#$%^&*()_+\-=\{\}\[\]:;"\'<>,.\\|?/]{6,24}$'))


def check_mail(email):
    """Check Email Pattern."""
    return re.match(PATTERN['email'], email)


def check_password(password):
    """Check Password Pattern."""
    return re.match(PATTERN['password'], password)
