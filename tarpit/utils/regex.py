# coding:utf-8
"""Some Verify Function."""
import re


class Patterns():

    def __init__(self):
        self.email = re.compile(r'^([\w\-.]+)@([\w-]+)(\.([\w-]+))+$')
        self.password = re.compile(
            r'^[0-9A-Za-z`~!@#$%^&*()_+\-=\{\}\[\]:;"\'<>,.\\|?/]{6,24}$')

    def check(self, pattern_name, target):
        if not hasattr(self, pattern_name):
            return False
        pattern = self.__getattribute__(pattern_name)
        return re.match(pattern, target)
