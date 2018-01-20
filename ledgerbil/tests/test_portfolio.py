import json
from unittest import mock

import pytest

from .. import portfolio
from .helpers import OutputFileTester


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
            "shares": 12200.78,
            "contributions": {
              "total": 1500.79,
              "modifier": 0.5
            },
            "note": "optional..."
          },
          "2018": {
            "symbol": "abcdx",
            "price": 83.11,
            "shares": 1700,
            "contributions": {
              "total": 500,
              "modifier": 0.5
            }
          },
          "2017": {
            "symbol": "abcdx",
            "price": 81.57,
            "shares": 999,
            "contributions": {
              "total": 11500,
              "modifier": 0.5
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
            "price": 119.76,
            "shares": 3750,
            "contributions": {
              "total": 750,
              "modifier": 0.4
            }
          },
          "2015": {
            "symbol": "lmnop",
            "price": 20.31,
            "shares": 2000,
            "contributions": {
              "total": 750,
              "modifier": 0.5
            }
          }
        }
      },
      {
        "account": "assets: 401k: bonds idx 2",
        "labels": [],
        "years": {}
      }
    ]
    '''
portfolio_data = json.loads(portfolio_json_data)


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', 'qwertyable'])
    expected = 'No accounts matched qwertyable'
    assert portfolio.get_portfolio_report(args) == expected


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
@mock.patch(__name__ + '.portfolio.get_account_history')
def test_account_matching_all(mock_get_history, mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--history'])
    portfolio.get_portfolio_report(args)
    assert mock_get_history.call_count == 3
    for data in portfolio_data:
        mock_get_history.assert_any_call(data)


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
@mock.patch(__name__ + '.portfolio.get_account_history')
def test_account_matching_regex(mock_get_history, mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--history', '--accounts', 'idx$'])
    portfolio.get_portfolio_report(args)
    assert mock_get_history.call_count == 2
    for data in portfolio_data[:1]:
        mock_get_history.assert_any_call(data)


def test_get_portfolio_data():
    jsondata = '{"key": "value"}'
    expected = {'key': 'value'}
    with mock.patch(__name__ + '.portfolio.open',
                    mock.mock_open(read_data=jsondata)) as m:
        data = portfolio.get_portfolio_data()

    assert data == expected
    m.assert_called_once_with('abcd', 'r')


def test_get_account_history():
    history = portfolio.get_account_history(portfolio_data[0])
    helper = OutputFileTester('test_portfolio_account_history')
    helper.save_out_file(history)
    helper.assert_out_equals_expected()


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
