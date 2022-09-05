from .error_code import *


def parameter_validator(param, **kwargs):
    if param == 0:
        return param
    if not param:
        raise ParameterException(**kwargs)
    return param
