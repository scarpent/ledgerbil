try:
    from .settings import Settings
    settings = Settings()
except ModuleNotFoundError:  # pragma: no cover
    settings = None

defaults = {
    'DATE_FORMAT': '%Y/%m/%d'
}


def get_setting(setting):
    if settings and hasattr(settings, setting):
        return getattr(settings, setting)

    return defaults.get(setting, None)
