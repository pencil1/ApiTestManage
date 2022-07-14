from .error_code import *


def parameter_validator(param, **kwargs):
    if not param:
        raise ParameterException(**kwargs)
    return param
