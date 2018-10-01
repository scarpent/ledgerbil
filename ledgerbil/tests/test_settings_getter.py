import pytest

from .. import settings, settings_getter


class MockSettingsEmpty:
    pass


class MockSettings:
    DATE_FORMAT = '%Y-%m-%d'


def teardown_function():
    settings_getter.settings = settings.Settings()


@pytest.mark.parametrize('test_input, expected', [
    ('DATE_FORMAT', '%Y/%m/%d'),
    ('DATE_FORMAT_MONTH', '%Y/%m'),
    ('NETWORTH_ACCOUNTS', '(^assets ^liabilities)'),
    ('FUBAR_NO_DEFAULT', None),
])
def test_empty_or_missing_settings_defaults(test_input, expected):
    settings_getter.settings = MockSettingsEmpty()
    assert settings_getter.get_setting(test_input) == expected


def test_settings_date_format():
    settings_getter.settings = MockSettings()
    assert settings_getter.get_setting('DATE_FORMAT') == '%Y-%m-%d'
