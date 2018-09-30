from .. import settings_getter


class MockSettingsEmpty:
    pass


class MockSettings:
    DATE_FORMAT = '%Y/%m/%d'


def test_empty_settings_date_format():
    settings_getter.settings = MockSettingsEmpty()
    assert settings_getter.get_setting('DATE_FORMAT') == '%Y/%m/%d'


def test_settings_date_format():
    settings_getter.settings = MockSettings()
    assert settings_getter.get_setting('DATE_FORMAT') == '%Y/%m/%d'


def test_settings_setting_not_there_and_no_default():
    settings_getter.settings = MockSettings()
    assert settings_getter.get_setting('FUBAR') is None
