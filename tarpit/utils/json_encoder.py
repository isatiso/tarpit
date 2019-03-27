# coding:utf-8

import json
from json import JSONEncoder


def tarpit_default(o):
    try:
        return iter(o)
    except TypeError:
        return {k: str(o.__dict__[k]) for k in o.__dict__}


json._default_encoder = JSONEncoder(
    skipkeys=False,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=None,
    default=tarpit_default,
)


def tarpit_dumps(obj):
    return json.dumps(obj, default=tarpit_default)


def tarpit_loads(obj):
    return json.loads(obj)
