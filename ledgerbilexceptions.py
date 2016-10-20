#!/usr/bin/python

"""error codes"""

from __future__ import print_function


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class LdgException(Exception):
    pass


class LdgScheduleFileConfigError(LdgException):
    pass


class LdgScheduleThingParametersError(LdgException):
    pass


class LdgScheduleThingLabelError(LdgException):
    pass


class LdgScheduleUnrecognizedIntervalUom(LdgException):
    pass
