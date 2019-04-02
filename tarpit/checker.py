class RequestParameter:

    __param_name__ = None
    __param_type__ = None
    __param_subparam__ = None
    __param_optional__ = True
    __param_default__ = None

    def __init__(self, name):
        self.__param_name__ = name

    def __rshift__(self, attr_type):
        if self.__param_type__ is not None:
            raise ValueError('Type of Parameter already set.')
        if not isinstance(attr_type, (type, list, set)):
            raise ValueError(
                f'Type of Parameter must be a instance of "type" "list" or "set", not "{type(attr_type).__name__}"'
            )
        if isinstance(attr_type, type):
            self.__param_type__ = attr_type
        elif isinstance(attr_type, (list, set)):
            self.__param_type__ = type(attr_type)
            self.__param_subparam__ = attr_type
            self.__param_default__ = type(attr_type)()

        return self

    @property
    def optional(self):
        return self.__param_optional__

    @property
    def default(self):
        return self.__param_default__

    @property
    def type(self):
        return self.__param_type__

    @property
    def name(self):
        return self.__param_name__

    @property
    def subparam(self):
        return self.__param_subparam__


class P(RequestParameter):
    __param_optional__ = True

    def __ge__(self, value):
        self.__param_default__ = value
        return self


class M(RequestParameter):
    __param_optional__ = False

    def __ge__(self, value):
        raise ValueError('Only optional parameter can set default value.')