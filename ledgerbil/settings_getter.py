try:
    from .settings import Settings
    settings = Settings()
except ModuleNotFoundError:  # pragma: no cover
    settings = None

defaults = {
    'DATE_FORMAT': '%Y/%m/%d',
    'DATE_FORMAT_MONTH': '%Y/%m',
    'DATE_FORMAT_YEAR': '%Y',
    'NETWORTH_ACCOUNTS': '(^assets ^liabilities)',
}


def get_setting(setting, default=None):
    if settings and hasattr(settings, setting):
        return getattr(settings, setting)

    return defaults.get(setting, default)
