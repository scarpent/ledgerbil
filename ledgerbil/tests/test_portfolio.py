import json
from unittest import mock

import pytest

from .. import portfolio, settings, settings_getter
from ..colorable import Colorable
from ..ledgerbilexceptions import LdgPortfolioError
from .helpers import OutputFileTester


class MockSettings:
    PORTFOLIO_FILE = 'abcd'


def setup_function():
    settings_getter.settings = MockSettings()


def teardown_function():
    settings_getter.settings = settings.Settings()


BIG_CO = 0
BONDS = 1
BIG_NAME = 2
BONDS_2 = 3
CLOSED = 4


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
            "contributions": 1500.79,
            "transfers": 900000,
            "note": "optional..."
          },
          "2019": {
            "symbol": "abcdx",
            "price": 83.11,
            "shares": 1700,
            "contributions": 500,
            "transfers": -100000
          },
          "2017": {
            "symbol": "abcdx",
            "price": 81.57,
            "shares": 999,
            "contributions": 11500
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
            "contributions": 750
          },
          "2015": {
            "symbol": "lmnop",
            "price": 20.31,
            "shares": 2000,
            "contributions": 0
          },
          "2014": {
            "symbol": "lmnop",
            "price": 20.78,
            "shares": 1800,
            "contributions": 750,
            "transfers": 15000
          }
        }
      },
      {
        "account": "assets: 401k: long account name that goes on...",
        "labels": ["401k", "flurb", "intl", "active", "smactive"],
        "years": {}
      },
      {
        "account": "assets: 401k: bonds idx 2",
        "labels": [],
        "years": {}
      },
      {
        "account": "assets: yog: mog",
        "labels": ["closed"],
        "years": {
          "2014": {
            "price": 10,
            "shares": 1000,
            "contributions": 0,
            "transfers": 9950
          },
          "2015": {
            "price": 0,
            "shares": 0,
            "contributions": 0,
            "transfers": -10025
          }
        }
      }
    ]
    '''
portfolio_data = json.loads(portfolio_json_data)


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_no_matches(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', 'qwertyable'])
    expected = 'No accounts matched "qwertyable"'
    assert portfolio.get_portfolio_report(args) == expected


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_no_matches_with_labels(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', 'big', '--labels', 'gah'])
    expected = 'No accounts matched "big", labels "gah"'
    assert portfolio.get_portfolio_report(args) == expected


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_performance_report_no_yearly_data(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', 'bonds idx 2'])
    expected = 'No yearly data found for accounts "bonds idx 2"'
    assert portfolio.get_portfolio_report(args) == expected


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_performance_report_no_yearly_data_with_labels(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', '401k', '--labels', 'smactive'])
    expected = 'No yearly data found for accounts "401k", labels "smactive"'
    assert portfolio.get_portfolio_report(args) == expected


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_compare_no_matches(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', 'qwertyable', '--compare'])
    expected = 'No accounts matched "qwertyable"'
    assert portfolio.get_portfolio_report(args) == expected


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_performance_report_compare_no_yearly_data(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', 'bonds idx 2', '--compare'])
    expected = 'No yearly data found for accounts "bonds idx 2"'
    assert portfolio.get_portfolio_report(args) == expected


@mock.patch(__name__ + '.portfolio.get_performance_report')
@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_performance(mock_get_data, mock_get_perf):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', 'big co 500 idx'])
    portfolio.get_portfolio_report(args)
    expected = [[portfolio_data[BIG_CO]], {'2016', '2017', '2019'}]
    mock_get_perf.assert_called_once_with(*expected)


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_history(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', 'idx', '--history'])
    report = portfolio.get_portfolio_report(args)
    helper = OutputFileTester('test_portfolio_report_history')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_list(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', '401k', '--list'])
    report = portfolio.get_portfolio_report(args)
    helper = OutputFileTester('test_portfolio_report_list')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_list_account_limited(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', 'idx$', '--list'])
    report = portfolio.get_portfolio_report(args)
    helper = OutputFileTester('test_portfolio_report_list_accounts')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_compare_accounts(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--accounts', '401k', '--compare'])
    report = portfolio.get_portfolio_report(args)
    helper = OutputFileTester('test_portfolio_report_compare_accounts')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_compare_accounts_no_current_value(mock_get_data):
    mock_get_data.return_value = portfolio_data
    accounts = [portfolio_data[CLOSED]]
    labels = {'closed'}
    accounts_regex = '.*'
    included_years = {'2014', '2015'}
    sort = 'v'
    accounts_only = False
    comparison_report = portfolio.get_comparison_report(
        accounts,
        labels,
        accounts_regex,
        included_years,
        sort,
        accounts_only
    )
    space = '              '
    expected = (
        f'labels{space}value    %     gain val  yr    all %    1yr %      \n'
        f'closed{space}                   $ 75   2     0.75     0.50      \n'
    )
    assert Colorable.get_plain_string(comparison_report) == expected


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_compare_labels(mock_get_data):
    """this also tests that if a label has no years, it will be ignored"""
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(['--labels', '401k smactive', '--compare'])
    report = portfolio.get_portfolio_report(args)
    helper = OutputFileTester('test_portfolio_report_compare_labels')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_get_portfolio_report_compare_labels_account_only(mock_get_data):
    mock_get_data.return_value = portfolio_data
    args = portfolio.get_args(
        ['--labels', '401k smactive', '--compare-accounts']
    )
    report = portfolio.get_portfolio_report(args)
    helper = OutputFileTester(
        'test_portfolio_report_compare_labels_account_only'
    )
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_account_matching_all(mock_get_data):
    mock_get_data.return_value = portfolio_data
    matched_accounts, _, included_years = portfolio.get_matching_accounts('')
    expected_included_years = {'2014', '2015', '2016', '2017', '2019'}
    assert included_years == expected_included_years
    expected_matched = sorted(portfolio_data, key=lambda k: k['account'])
    assert matched_accounts == expected_matched


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_account_matching_regex(mock_get_data):
    mock_get_data.return_value = portfolio_data
    matched_accounts, _, included_years = \
        portfolio.get_matching_accounts('idx$')
    expected_included_years = {'2014', '2015', '2016', '2017', '2019'}
    assert matched_accounts == portfolio_data[:BONDS + 1]
    assert included_years == expected_included_years


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_account_matching_labels(mock_get_data):
    mock_get_data.return_value = portfolio_data
    matched_accounts, matched_labels, _ = \
        portfolio.get_matching_accounts('.*', 'smactive')
    assert matched_accounts == [portfolio_data[BIG_NAME]]
    assert matched_labels == {'smactive'}


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_account_matching_multiple_labels(mock_get_data):
    mock_get_data.return_value = portfolio_data
    matched_accounts, matched_labels, _ = \
        portfolio.get_matching_accounts('.*', 'smactive,,  ,large')
    assert matched_accounts == [
        portfolio_data[BIG_CO],
        portfolio_data[BIG_NAME]
    ]
    assert matched_labels == {'smactive', 'large'}


@mock.patch(__name__ + '.portfolio.get_portfolio_data')
def test_account_matching_multiple_labels_space_and_comma_stuff(mock_get_data):
    mock_get_data.return_value = portfolio_data
    matched_accounts, _, _ = \
        portfolio.get_matching_accounts('.*', 'intl,  large  bonds')
    expected = [
        portfolio_data[BIG_CO],
        portfolio_data[BONDS],
        portfolio_data[BIG_NAME]
    ]
    assert matched_accounts == expected


def test_validate_json_year_keys_valid():
    year = {}
    for key in portfolio.VALID_YEAR_KEYS:
        year[key] = 'hi'
    portfolio.validate_json_year_keys(year)


def test_validate_json_year_keys_invalid():
    year = {'symbol': 'abcde', 'blah': 'blah'}
    with pytest.raises(LdgPortfolioError) as excinfo:
        portfolio.validate_json_year_keys(year)
    expected = f'Invalid key in {year.keys()}'
    assert str(excinfo.value) == expected


@pytest.mark.parametrize('test_input, expected', [
    ([[1.5], 1], 50),
    ([[1.5, 1.5], 2], 50),
    ([[0.5, 0.5], 2], -50),
    ([[1, 1.25, 1.75, .75], 4], 13.175476395946738),
    ([[1, -0.1], 2], (-100 + 31.622776601683793j)),  # gains should be positive
])
def test_get_annualized_total_return(test_input, expected):
    assert portfolio.get_annualized_total_return(*test_input) == expected


@pytest.mark.parametrize('test_input, expected', [
    ([[], 2], ''),
    ([[1.5], 1], f'{50:{portfolio.COL_GAIN}.2f}'),
    ([[2, 2, 2, 2, 2, 2, 1.5], 1], f'{50:{portfolio.COL_GAIN}.2f}'),
    ([[1, 1.25, 1.75, .75], 4], f'{13.18:{portfolio.COL_GAIN}.2f}'),
    (
        [[3, 3, 3, 3, 3, 3, 1, 1.25, 1.75, .75], 4],
        f'{13.18:{portfolio.COL_GAIN}.2f}'
    ),
])
def test_get_formatted_gain(test_input, expected):
    assert Colorable.get_plain_string(
        portfolio.get_formatted_gain(*test_input)
    ) == expected


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


def test_get_account_history_one_year():
    account = {
        'account': 'assets: 401k: bonds idx',
        'labels': [],
        'years': {
            '2016': {'price': 119.76, 'shares': 3750.9, 'contributions': 750}
        }
    }
    history = portfolio.get_account_history(account)
    helper = OutputFileTester('test_portfolio_account_history_one_year')
    helper.save_out_file(history)
    helper.assert_out_equals_expected()


def test_get_yearly_combined_accounts_single_account():
    accounts = [{
        'account': 'the account name',
        'years': {
            '2014': {'price': 100, 'shares': 10,
                     'contributions': 50, 'transfers': 50},
            '2015': {'price': 110, 'shares': 20, 'contributions': 200},
        }
    }]
    expected = {
        2014: {'contributions': 50, 'transfers': 50, 'value': 1000.0},
        2015: {'contributions': 200, 'transfers': 0, 'value': 2200.0},
    }
    actual = portfolio.get_yearly_combined_accounts(accounts, {'2014', '2015'})
    assert actual == expected


def test_get_yearly_combined_accounts_two_accounts_same_years():
    accounts = [
        {
            'account': 'the account name',
            'years': {
                '2014': {'price': 100, 'shares': 10, 'contributions': 100},
                '2015': {'price': 110, 'shares': 20, 'contributions': 200},
            }
        },
        {
            'account': 'another account name',
            'years': {
                '2014': {'price': 300, 'shares': 50, 'contributions': 500},
                '2015': {'price': 330, 'shares': 100,
                         'contributions': 1250, 'transfers': -250},
            }
        }
    ]
    expected = {
        2014: {'contributions': 600.0, 'transfers': 0, 'value': 16000.0},
        2015: {'contributions': 1450.0, 'transfers': -250, 'value': 35200.0},
    }
    actual = portfolio.get_yearly_combined_accounts(accounts, {'2014', '2015'})
    assert actual == expected


def test_get_yearly_combined_accounts_single_account_missing_years():
    accounts = [{
        'account': 'the account name',
        'years': {
            '2013': {'price': 100, 'shares': 10,
                     'contributions': 50, 'transfers': 50},
            '2015': {'price': 110, 'shares': 20, 'contributions': 200},
        }
    }]
    expected = {
        2013: {'contributions': 50.0, 'transfers': 50, 'value': 1000.0},
        2014: {'contributions': 0, 'transfers': 0, 'value': 1000},
        2015: {'contributions': 200.0, 'transfers': 0, 'value': 2200.0},
        2016: {'contributions': 0, 'transfers': 0, 'value': 2200},
        2017: {'contributions': 0, 'transfers': 0, 'value': 2200},
    }
    actual = portfolio.get_yearly_combined_accounts(
        accounts,
        {'2014', '2013', '2015', '2017', '2016'}
    )
    assert actual == expected


def test_get_yearly_combined_accounts_multiple_accounts_missing_years():
    accounts = [
        {
            'account': 'the account name',
            'years': {
                '2013': {'price': 100, 'shares': 10, 'contributions': 100},
                '2015': {'price': 110, 'shares': 20,
                         'contributions': 300, 'transfers': -100},
            },
        },
        {
            'account': 'another account name',
            'years': {
                '2015': {'price': 330, 'shares': 100,
                         'contributions': 500, 'transfers': 500},
                '2014': {'price': 300, 'shares': 50, 'contributions': 500},
                '2018': {'price': 250, 'shares': 110, 'contributions': 800},
            }
        }
    ]
    expected = {
        2013: {'contributions': 100, 'transfers': 0, 'value': 1000.0},
        2014: {'contributions': 500, 'transfers': 0, 'value': 16000},
        2015: {'contributions': 800, 'transfers': 400, 'value': 35200.0},
        2016: {'contributions': 0, 'transfers': 0, 'value': 35200},
        2017: {'contributions': 0, 'transfers': 0, 'value': 35200},
        2018: {'contributions': 800, 'transfers': 0, 'value': 29700},
    }
    actual = portfolio.get_yearly_combined_accounts(
        accounts,
        {'2014', '2013', '2015', '2017', '2016', '2018'}
    )
    assert actual == expected


def test_get_yearly_with_gains():
    """get_yearly_with_gains should produce a sorted list of Years"""
    totals = {
        2014: {'contributions': 1000, 'transfers': 0, 'value': 5000.0},
        2013: {'contributions': 500, 'transfers': 500, 'value': 1000.0},
        2015: {'contributions': 0, 'transfers': 0, 'value': 5000.0},
        2016: {'contributions': 3000.0, 'transfers': -1000, 'value': 4000},
    }
    expected = [
        portfolio.Year(2013, 500, 500, 1000.0, 1, 0),
        portfolio.Year(2014, 1000, 0, 5000.0, 3, 3000),
        portfolio.Year(2015, 0, 0, 5000.0, 1, 0),
        portfolio.Year(2016, 3000.0, -1000, 4000.0, 0.5, -3000.0),
    ]
    actual = portfolio.get_yearly_with_gains(totals)
    assert actual == expected


def test_get_yearly_with_gains_first_year_gain():
    """get_yearly_with_gains should provide a gain value in first year"""
    totals = {
        2013: {'contributions': 1000, 'transfers': 0, 'value': 2000.0},
        2014: {'contributions': 500, 'transfers': 500, 'value': 5000.0},
    }
    expected = [
        portfolio.Year(2013, 1000, 0, 2000.0, 3.0, 1000.0),
        portfolio.Year(2014, 500, 500, 5000.0, 1.8, 2000.0),
    ]
    actual = portfolio.get_yearly_with_gains(totals)
    assert actual == expected


def test_get_yearly_assert_gain_less_than_zero():
    """get_yearly_with_gains raise an assertion error if a gain is < 0"""
    totals = {
        2013: {'contributions': 10, 'transfers': -20, 'value': 30},
    }
    with pytest.raises(AssertionError) as excinfo:
        portfolio.get_yearly_with_gains(totals)
    expected = 'Gain < 0 in 2013: -7.0'
    assert str(excinfo.value) == expected


def test_get_performance_report_header_one_account():
    accounts = [{'account': 'assets: abc'}]
    expected = '1 year, 1 account: abc'
    actual = portfolio.get_performance_report_header(accounts, 1)
    assert actual == expected


def test_get_performance_report_header_three_accounts():
    accounts = [
        {'account': 'assets: abc'},
        {'account': 'assets:xyz'},
        {'account': 'lmnop'},
    ]
    expected = '3 years, 3 accounts: abc, xyz, ...'
    actual = portfolio.get_performance_report_header(accounts, 3)
    assert actual == expected


col_headers = 'year    contrib   transfers        value   gain %     gain val'


@pytest.mark.parametrize('test_input, expected', [
    (2, f'{col_headers}    all %      '),
    (3, f'{col_headers}    all %    3yr %    '),
    (4, f'{col_headers}    all %    3yr %    '),
    (5, f'{col_headers}    all %    3yr %    5yr %  '),
    (6, f'{col_headers}    all %    3yr %    5yr %  '),
    (10, f'{col_headers}    all %    3yr %    5yr %   10yr %'),
])
def test_get_performance_report_column_headers(test_input, expected):
    actual = portfolio.get_performance_report_column_headers(test_input)
    assert Colorable.get_plain_string(actual) == expected


def test_get_performance_report_years_eleven_years():
    totals = {
        2013: {'contributions': 100, 'transfers': 500, 'value': 625},
        2014: {'contributions': 200, 'transfers': 0.50, 'value': 875},
        2015: {'contributions': 300, 'transfers': -0.50, 'value': 1225},
        2016: {'contributions': 0, 'transfers': -500, 'value': 775},
        2017: {'contributions': 200, 'transfers': 0, 'value': 950},
        2018: {'contributions': 100, 'transfers': 0, 'value': 1000},
        2019: {'contributions': 250, 'transfers': 0, 'value': 1225},
        2020: {'contributions': 250, 'transfers': 0, 'value': 1600},
        2021: {'contributions': 150, 'transfers': 0, 'value': 1875},
        2022: {'contributions': 50, 'transfers': 0, 'value': 2112},
        2023: {'contributions': 100, 'transfers': 200, 'value': 2500},
    }
    years = portfolio.get_yearly_with_gains(totals)
    report = portfolio.get_performance_report_years(years)
    helper = OutputFileTester('test_portfolio_perf_report_years_eleven_years')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_performance_report():
    accounts = [{
        'account': 'the account name',
        'labels': ['cantaloupe'],
        'years': {
            '2015': {'price': 100, 'shares': 20,
                     'contributions': 300, 'transfers': 1200},
        },
    }]
    included_years = {2015}
    report = portfolio.get_performance_report(accounts, included_years)
    helper = OutputFileTester('test_portfolio_performance_report')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


comp_headers = '        value    %     gain val  yr    all %    1yr %'
account_header = f"{'accounts':{portfolio.COL_ACCOUNT}}"
label_header = f"{'labels':{portfolio.COL_LABEL}}"


@pytest.mark.parametrize('test_input, expected', [
    ([1], f'{label_header}{comp_headers}      '),
    ([2], f'{label_header}{comp_headers}      '),
    ([3, False], f'{account_header}{comp_headers}    3yr %    '),
    ([4], f'{label_header}{comp_headers}    3yr %    '),
    ([5, False], f'{account_header}{comp_headers}    3yr %    5yr %  '),
    ([6, False], f'{account_header}{comp_headers}    3yr %    5yr %  '),
    ([10], f'{label_header}{comp_headers}    3yr %    5yr %   10yr %'),
])
def test_get_comparison_report_column_headers(test_input, expected):
    actual = portfolio.get_comparison_report_column_headers(*test_input)
    assert Colorable.get_plain_string(actual) == expected


def test_get_comparison_summary():
    totals = {
        2013: {'contributions': 100, 'transfers': 500, 'value': 625},
        2014: {'contributions': 200, 'transfers': 0.50, 'value': 875},
        2015: {'contributions': 300, 'transfers': -0.50, 'value': 1225},
        2016: {'contributions': 0, 'transfers': -500, 'value': 775},
        2017: {'contributions': 200, 'transfers': 0, 'value': 950},
        2018: {'contributions': 100, 'transfers': 0, 'value': 1000},
        2019: {'contributions': 250, 'transfers': 0, 'value': 1225},
        2020: {'contributions': 250, 'transfers': 0, 'value': 1600},
        2021: {'contributions': 150, 'transfers': 0, 'value': 1875},
        2022: {'contributions': 50, 'transfers': 0, 'value': 2112},
        2023: {'contributions': 100, 'transfers': 200, 'value': 2500},
    }
    years = portfolio.get_yearly_with_gains(totals)
    summary = portfolio.get_comparison_summary(years, 'blarg')
    assert summary.col1 == 'blarg'
    assert summary.value == 2500
    assert summary.gain_value == 600.0
    assert summary.num_years == 11
    assert f'{summary.all:.2f}' == '4.02'
    assert f'{summary.y3:.2f}' == '7.04'
    assert f'{summary.y5:.2f}' == '5.55'
    assert f'{summary.y10:.2f}' == '3.60'


@pytest.mark.parametrize('sort, first_row', [
    ('v', portfolio.Summary('x', 0, 1, 1, 1, 1, 1, 1, 1)),
    ('g', portfolio.Summary('x', 1, 0, 1, 1, 1, 1, 1, 1)),
    ('y', portfolio.Summary('x', 1, 1, 0, 1, 1, 1, 1, 1)),
    ('a', portfolio.Summary('x', 1, 1, 1, 0, 1, 1, 1, 1)),
    ('1', portfolio.Summary('x', 1, 1, 1, 1, 0, 1, 1, 1)),
    ('3', portfolio.Summary('x', 1, 1, 1, 1, 1, 0, 1, 1)),
    ('5', portfolio.Summary('x', 1, 1, 1, 1, 1, 1, 0, 1)),
    ('10', portfolio.Summary('x', 1, 1, 1, 1, 1, 1, 1, 0)),
])
def test_get_sorted_comparison_items(sort, first_row):
    items = [
        first_row,
        portfolio.Summary('x', 1, 1, 1, 1, 1, 1, 1, 1)
    ]
    sorted_items = portfolio.get_sorted_comparison_items(items, sort)
    assert sorted_items == list(reversed(items))


def test_get_sorted_comparison_items_bad_key():
    comparison_items = [portfolio.Summary('x', 1, 2, 3, 4, 5, 6, 7, 8)]
    with pytest.raises(KeyError):
        portfolio.get_sorted_comparison_items(comparison_items, 'blart')


def test_get_gain_not_enough_years():
    assert portfolio.get_gain([], 1) == portfolio.NULL_GAIN


def test_get_comparison_report_line():
    comparison_item = portfolio.Summary('gargle', 2500, 600.0, 11,
                                        4.02, 5.55, 7.04, 5.55, 3.6)
    line = portfolio.get_comparison_report_line(comparison_item, 50, True)
    expected = ('gargle            $ 2,500   50        $ 600  11     '
                '4.02     5.55     7.04     5.55     3.60\n')
    assert Colorable.get_plain_string(line) == expected


def test_get_comparison_report_line_no_value():
    comparison_item = portfolio.Summary('gargle', 0, 600.0, 11,
                                        4.02, 5.55, 7.04, 5.55, 3.6)
    line = portfolio.get_comparison_report_line(comparison_item, 0, False)
    expected = (
        'gargle                                                   '
        '         $ 600  11     4.02     5.55     7.04     5.55     3.60\n'
    )
    assert Colorable.get_plain_string(line) == expected


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
    (['-L', 'small large'], 'small large'),
    (['--labels', 'mid, large'], 'mid, large'),
    ([], ''),  # default
])
def test_args_labels(test_input, expected):
    args = portfolio.get_args(test_input)
    assert args.labels == expected


@pytest.mark.parametrize('test_input, expected', [
    (['-H'], True),
    (['--history'], True),
    ([], False),
])
def test_args_command(test_input, expected):
    args = portfolio.get_args(test_input)
    assert args.history is expected


@pytest.mark.parametrize('test_input, expected', [
    (['-l'], True),
    (['--list'], True),
    ([], False),
])
def test_args_list(test_input, expected):
    args = portfolio.get_args(test_input)
    assert args.list is expected


@pytest.mark.parametrize('test_input, expected', [
    (['-c'], True),
    (['--compare'], True),
    ([], False),
])
def test_args_compare(test_input, expected):
    args = portfolio.get_args(test_input)
    assert args.compare is expected


@pytest.mark.parametrize('test_input, expected', [
    (['-C'], True),
    (['--compare-accounts'], True),
    ([], False),
])
def test_args_compare_accounts_only(test_input, expected):
    args = portfolio.get_args(test_input)
    assert args.compare_accounts is expected


@pytest.mark.parametrize('test_input, expected', [
    (['-s', 'value'], 'value'),
    (['--sort', '%'], '%'),
    ([], 'a'),  # default
])
def test_args_sort(test_input, expected):
    args = portfolio.get_args(test_input)
    assert args.sort == expected
