# coding:utf-8
"""Worker Module."""
import sys

from tarpit.task import CeleryConfig
from tarpit.config import _ENV as env

if __name__ == 'worker':
    queue = None
    cc = CeleryConfig()
    if 'worker' in sys.argv[:3]:
        for i, arg in enumerate(sys.argv):
            if arg.startswith(env) and sys.argv[i - 1] == '-Q':
                queue = arg.split(':')[1]
                break

        if queue in cc.queue_list:
            __import__(cc.queue_list[queue]['module'])
        else:
            exit(f'Unknown queue name: "{queue}"')
