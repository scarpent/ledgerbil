import json
from unittest import mock

import pytest

from .. import portfolio


class MockSettings(object):
    PORTFOLIO_FILE = 'abcd'


def setup_module(module):
    portfolio.settings = MockSettings()


portfolio_json_data = '''\
    [
      {
        "account": "assets: 401k: big co 500 idx",
        "labels": [
          "large",
          "401k",
          "flurb"
        ],
        "years": {
            "2016": {
              "symbol": "abcdx",
              "price": 80.23,
              "shares": 1000,
              "contributions": {
                "total": 1500,
                "year_start": 0.5
              },
              "note": "optional..."
            },
            "2017": {
              "symbol": "abcdx",
              "price": 81.57,
              "shares": 1200,
              "contributions": {
                "total": 1500,
                "year_start": 0.5
              }
            }
          }
      },
      {
        "account": "assets: 401k: bonds idx",
        "labels": [
          "bonds",
          "401k",
          "flurb"
        ],
        "years": {
            "2016": {
              "symbol": "lmnop",
              "price": 19.76,
              "shares": 1750,
              "contributions": {
                "total": 750,
                "year_start": 0.4
              }
            },
            "2015": {
              "symbol": "lmnop",
              "price": 20.31,
              "shares": 2000,
              "contributions": {
                "total": 750,
                "year_start": 0.5
              }
            }
          }
      }
    ]'''
portfolio_data = json.loads(portfolio_json_data)


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report(mock_get_portfolio_data):
    mock_get_portfolio_data.return_value = portfolio_data
    args = portfolio.get_args(['-a', 'qwertyable'])
    expected = 'No accounts matched qwertyable'
    assert portfolio.get_portfolio_report(args) == expected


def test_get_portfolio_data():
    jsondata = '{"key": "value"}'
    expected = {'key': 'value'}
    with mock.patch(__name__ + '.portfolio.open',
                    mock.mock_open(read_data=jsondata)) as m:
        data = portfolio.get_portfolio_data()

    assert data == expected
    m.assert_called_once_with('abcd', 'r')


@mock.patch(__name__ + '.portfolio.get_portfolio_report', return_value='hi!')
@mock.patch(__name__ + '.portfolio.print')
def test_main(mock_print, mock_report):
    portfolio.main([])
    expected = 'hi!'
    mock_print.assert_called_once_with(expected)


@pytest.mark.parametrize('test_input, expected', [
    (['-a', '401k'], '401k'),
    (['--accounts', '(a|b|c)$'], '(a|b|c)$'),
    ([], '.*'),  # default
])
def test_args_accounts(test_input, expected):
    args = portfolio.get_args(test_input)
    assert args.accounts_regex == expected


@pytest.mark.parametrize('test_input, expected', [
    (['-H'], True),
    (['--history'], True),
    ([], False),
])
def test_args_command(test_input, expected):
    args = portfolio.get_args(test_input)
    assert args.history is expected
