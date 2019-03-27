# coding:utf-8
import sys


def _dump(sign, color, show_all, *args):
    sys.stdout.write(f'\n\033[0;{color}m')
    for arg in args:
        if show_all:
            sys.stdout.write('\n' + arg)
        else:
            sys.stdout.write('\n' + arg[:1000])
            if len(arg) > 1000:
                sys.stdout.write(' ...')
    sys.stdout.write(f'\n\033[0m')
    sys.stdout.flush()


def dump_in(*args):
    _dump('<', 32, False, *args)


def dump_out(*args):
    _dump('>', 33, False, *args)


def dump_error(*args):
    _dump('%', 31, True, *args)
