import inspect
import string
import random
import time
from tarpit.err import MissingArgumentError, ArgumentTypeError

pool = string.ascii_letters + string.digits


def checker(func):
    """Decorator to create a parameters checker."""
    parameters = inspect.signature(func).parameters

    for name, value in parameters.items():
        if value.kind == value.VAR_KEYWORD:
            continue
        if value.kind == value.VAR_POSITIONAL:
            continue

        if value.annotation == value.empty:
            raise ValueError(f'Annotation of key <"{name}"> is not exists.')

    def inner(**kwargs):
        for name, value in parameters.items():
            if value.kind == value.VAR_KEYWORD:
                continue
            if value.kind == value.VAR_POSITIONAL:
                continue

            if kwargs.get(name) is None:
                if value.default != value.empty:
                    kwargs[name] = value.default
                else:
                    raise MissingArgumentError(name)

            if kwargs[name] is not None and not isinstance(
                    kwargs[name], value.annotation):
                try:
                    kwargs[name] = value.annotation(kwargs[name])
                except:
                    raise ArgumentTypeError(name, value.annotation)

        return kwargs

    return inner


def rand6():
    return ''.join(random.choice(pool) for _ in range(6))


def rand12():
    rand = ''.join(random.choice(pool) for _ in range(8))
    stamp = hex(int(time.time()))[-4:]
    return rand + stamp