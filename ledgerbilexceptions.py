#!/usr/bin/python

"""error codes"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class LdgScheduleFileConfigError(BaseException):
    pass


class LdgScheduleThingParametersError(BaseException):
    pass


class LdgScheduleThingLabelError(BaseException):
    pass
