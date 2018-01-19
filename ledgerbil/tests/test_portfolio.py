from unittest import mock

from .. import portfolio


class MockSettings(object):
    PORTFOLIO_FILE = 'abc'


def setup_module(module):
    portfolio.settings = MockSettings()


def test_get_portfolio_report():
    assert portfolio.get_portfolio_report(None) == 'hi!'


@mock.patch(__name__ + '.portfolio.print')
def test_main(mock_print):
    portfolio.main([])
    expected = 'hi!'
    mock_print.assert_called_once_with(expected)
