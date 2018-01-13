class LdgException(Exception):
    def __init__(self, value):
        self.value = value


class LdgSchedulerError(LdgException):
    pass


class LdgReconcilerError(LdgException):
    pass
