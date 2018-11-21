class LdgException(Exception):
    pass


class LdgSchedulerError(LdgException):
    pass


class LdgReconcilerError(LdgException):
    pass


class LdgPortfolioError(LdgException):
    pass
