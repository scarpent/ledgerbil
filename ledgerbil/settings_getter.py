import os

try:
    from .settings import Settings
    settings = Settings()
except ModuleNotFoundError:  # pragma: no cover
    settings = None

reconciler_cache_file = os.path.join(
    os.path.expanduser('~'),
    '.ledgerbil_reconciler_cache'
)

defaults = {
    'DATE_FORMAT': '%Y/%m/%d',
    'DATE_FORMAT_MONTH': '%Y/%m',
    'DATE_FORMAT_YEAR': '%Y',
    'NETWORTH_ACCOUNTS': '(^assets ^liabilities)',
    'RECONCILER_CACHE_FILE': reconciler_cache_file,
}


def get_setting(setting, default=None):
    if settings and hasattr(settings, setting):
        return getattr(settings, setting)

    return defaults.get(setting, default)
