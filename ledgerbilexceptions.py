"""error codes"""

__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class LdgException(Exception):
    def __init__(self, value):
        self.value = value


class LdgScheduleFileConfigError(LdgException):
    pass


class LdgScheduleThingParametersError(LdgException):
    pass


class LdgScheduleThingLabelError(LdgException):
    pass


class LdgScheduleUnrecognizedIntervalUom(LdgException):
    pass


class LdgReconcilerMoreThanOneMatchingAccount(LdgException):
    pass


class LdgReconcilerMultipleStatuses(LdgException):
    pass
