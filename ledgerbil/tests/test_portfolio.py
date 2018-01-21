import json
from unittest import mock

import pytest

from .. import portfolio
from .helpers import OutputFileTester


class MockSettings(object):
    PORTFOLIO_FILE = 'abcd'


def setup_module(module):
    portfolio.settings = MockSettings()


BIG_CO = 0
BONDS = 1
BONDS_2 = 2
BIG_NAME = 3


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
      },
      {
        "account": "assets: 401k: long account name that goes on...",
        "labels": ["401k", "flurb", "intl", "active", "smactive"],
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
    assert mock_get_history.call_count == len(portfolio_data)
    for data in portfolio_data:
        mock_get_history.assert_any_call(data)


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
@mock.patch(__name__ + '.portfolio.get_account_history')
def test_account_matching_regex(mock_get_history, mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--history', '--accounts', 'idx$'])
    portfolio.get_portfolio_report(args)
    assert mock_get_history.call_count == 2
    for data in portfolio_data[:BONDS]:
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
    history = portfolio.get_account_history(portfolio_data[BIG_CO])
    helper = OutputFileTester('test_portfolio_account_history')
    helper.save_out_file(history)
    helper.assert_out_equals_expected()


def test_get_account_history_no_labels_no_years():
    history = portfolio.get_account_history(portfolio_data[BONDS_2])
    helper = OutputFileTester('test_portfolio_account_history_empty')
    helper.save_out_file(history)
    helper.assert_out_equals_expected()


def test_get_account_history_long_name_no_years():
    history = portfolio.get_account_history(portfolio_data[BIG_NAME])
    helper = OutputFileTester('test_portfolio_account_history_empty_long')
    helper.save_out_file(history)
    helper.assert_out_equals_expected()


def test_add_up_yearly_numbers_single_account():
    accounts = [{
        'account': 'the account name',
        'years': {
            '2014': {'price': 100,
                     'shares': 10,
                     'contributions': {'total': 100, 'modifier': 0.75}},
            '2015': {'price': 110,
                     'shares': 20,
                     'contributions': {'total': 200, 'modifier': 0.25}},
        }
    }]
    expected = {
        2014: {'contrib_start': 75.0, 'contrib_end': 25.0, 'value': 1000.0},
        2015: {'contrib_start': 50.0, 'contrib_end': 150.0, 'value': 2200.0},
    }
    actual = portfolio.add_up_yearly_numbers(accounts, 2014, 2016)
    assert actual == expected


def test_add_up_yearly_numbers_two_accounts_same_years():
    accounts = [
        {
            'account': 'the account name',
            'years': {
                '2014': {'price': 100,
                         'shares': 10,
                         'contributions': {'total': 100, 'modifier': 0.75}},
                '2015': {'price': 110,
                         'shares': 20,
                         'contributions': {'total': 200, 'modifier': 0.25}},
            }
        },
        {
            'account': 'another account name',
            'years': {
                '2014': {'price': 300,
                         'shares': 50,
                         'contributions': {'total': 500, 'modifier': 0.50}},
                '2015': {'price': 330,
                         'shares': 100,
                         'contributions': {'total': 1000, 'modifier': 0.50}},
            }
        }
    ]
    expected = {
        2014: {'contrib_start': 325.0, 'contrib_end': 275.0, 'value': 16000.0},
        2015: {'contrib_start': 550.0, 'contrib_end': 650.0, 'value': 35200.0},
    }
    actual = portfolio.add_up_yearly_numbers(accounts, 2014, 2016)
    assert actual == expected


def test_add_up_yearly_numbers_single_account_missing_years():
    accounts = [{
        'account': 'the account name',
        'years': {
            '2013': {'price': 100,
                     'shares': 10,
                     'contributions': {'total': 100, 'modifier': 0.75}},
            '2015': {'price': 110,
                     'shares': 20,
                     'contributions': {'total': 200, 'modifier': 0.25}},
        }
    }]
    expected = {
        2013: {'contrib_start': 75.0, 'contrib_end': 25.0, 'value': 1000.0},
        2014: {'value': 1000},
        2015: {'contrib_start': 50.0, 'contrib_end': 150.0, 'value': 2200.0},
        2016: {'value': 2200},
        2017: {'value': 2200},
    }
    actual = portfolio.add_up_yearly_numbers(accounts, 2010, 2018)
    assert actual == expected


def test_add_up_yearly_numbers_multiple_accounts_missing_years():
    accounts = [
        {
            'account': 'the account name',
            'years': {
                '2013': {'price': 100,
                         'shares': 10,
                         'contributions': {'total': 100, 'modifier': 0.75}},
                '2015': {'price': 110,
                         'shares': 20,
                         'contributions': {'total': 200, 'modifier': 0.25}},
            },
        },
        {
            'account': 'another account name',
            'years': {
                '2014': {'price': 300,
                         'shares': 50,
                         'contributions': {'total': 500, 'modifier': 0.50}},
                '2015': {'price': 330,
                         'shares': 100,
                         'contributions': {'total': 1000, 'modifier': 0.50}},
                '2018': {'price': 250,
                         'shares': 110,
                         'contributions': {'total': 800, 'modifier': 0.75}},
            }
        }
    ]
    expected = {
        2013: {'contrib_start': 75.0, 'contrib_end': 25.0, 'value': 1000.0},
        2014: {'contrib_start': 250.0, 'contrib_end': 250.0, 'value': 16000},
        2015: {'contrib_start': 550.0, 'contrib_end': 650.0, 'value': 35200.0},
        2016: {'value': 35200},
        2017: {'value': 35200},
        2018: {'contrib_start': 600.0, 'contrib_end': 200.0, 'value': 29700},
    }
    actual = portfolio.add_up_yearly_numbers(accounts, 2010, 2019)
    assert actual == expected


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
