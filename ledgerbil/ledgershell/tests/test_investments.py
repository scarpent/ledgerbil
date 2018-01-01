import os
from unittest import mock

from .. import investments, runner


class TestSettings(object):
    LEDGER_COMMAND = 'ledger'
    LEDGER_FILES = [
        'blarg.ldg',
        'glurg.ldg',
    ]
    INVESTMENT_DEFAULT_ACCOUNTS = 'abc'
    INVESTMENT_DEFAULT_END_DATE = 'xyz'
    LEDGER_DIR = 'lmn'
    PRICES_FILE = 'ijk'


@mock.patch(__name__ + '.investments.print')
def test_check_for_negative_dollars_no_warning(mock_print):
    investments.check_for_negative_dollars('$ 10', 'blah')
    assert not mock_print.called


@mock.patch(__name__ + '.investments.print')
def test_check_for_negative_dollars_warning(mock_print):
    expected = 'Negative dollar amount $ -10 for "blah."'
    investments.check_for_negative_dollars('$ -10', 'blah')
    output = investments.Colorable.get_plain_text(mock_print.call_args[0][0])
    assert expected in output


def test_get_investment_command_options_defaults():
    investments.settings = TestSettings()
    expected = '--market --price-db {prices} bal abc --end xyz'.format(
        prices=os.path.join(
            TestSettings.LEDGER_DIR,
            TestSettings.PRICES_FILE
        )
    )
    # It would be nice to test with actual defaults but they appear
    # to be set at import time so we'll do this
    actual = investments.get_investment_command_options(
        accounts=TestSettings.INVESTMENT_DEFAULT_ACCOUNTS,
        end_date=TestSettings.INVESTMENT_DEFAULT_END_DATE
    )
    assert actual == expected


def test_get_investment_command_options_defaults_plus_begin_date():
    investments.settings = TestSettings()
    expected = '--market --price-db {p} bal abc --begin qrt --end xyz'.format(
        p=os.path.join(
            TestSettings.LEDGER_DIR,
            TestSettings.PRICES_FILE
        )
    )
    actual = investments.get_investment_command_options(
        accounts=TestSettings.INVESTMENT_DEFAULT_ACCOUNTS,
        begin_date='qrt',
        end_date=TestSettings.INVESTMENT_DEFAULT_END_DATE
    )
    assert actual == expected


@mock.patch(__name__ + '.investments.print')
@mock.patch(__name__ + '.investments.get_ledger_output')
def test_get_lines_default_args(mock_get_ledger_output, mock_print):
    investments.settings = TestSettings()
    args = investments.ArgHandler.get_args([])
    mock_get_ledger_output.return_value = '1\n2\n3\n'
    lines = investments.get_lines('XYZ', args)
    assert lines == ['1', '2', '3', '']
    mock_get_ledger_output.assert_called_once_with(
        'XYZ --market --price-db lmn/ijk bal abc --end xyz'
    )
    assert not mock_print.called


@mock.patch(__name__ + '.investments.print')
@mock.patch(__name__ + '.investments.get_ledger_output')
def test_get_lines_print_command(mock_get_ledger_output, mock_print):
    investments.settings = TestSettings()
    runner.settings = TestSettings()
    args = investments.ArgHandler.get_args(['--command'])
    mock_get_ledger_output.return_value = '1\n2\n3\n'
    lines = investments.get_lines('XYZ', args)
    assert lines == ['1', '2', '3', '']
    mock_get_ledger_output.assert_called_once_with(
        'XYZ --market --price-db lmn/ijk bal abc --end xyz'
    )
    expected_print = ('ledger -f lmn/blarg.ldg -f lmn/glurg.ldg XYZ '
                      '--market --price-db lmn/ijk bal abc --end xyz ')
    mock_print.assert_called_once_with(expected_print)


@mock.patch(__name__ + '.investments.get_lines')
def test_get_investment_report(mock_lines):
    shares = [
        '            $ 189.00',
        '         9.897 abcdx',
        '        20.000 lmnop',
        '        15.000 qwrty',
        '         5.000 yyzxx  assets',
        '            $ 189.00',
        '         9.897 abcdx',
        '        20.000 lmnop     401k',
        '         9.897 abcdx       big co 500 idx',
        '        20.000 lmnop       bonds idx',
        '            $ 189.00       cash',
        '        15.000 qwrty     ira: glass idx',
        '         5.000 yyzxx     mutual: total idx',
        '--------------------',
        '            $ 189.00',
        '         9.897 abcdx',
        '        20.000 lmnop',
        '        15.000 qwrty',
        '         5.000 yyzxx',
        ''
    ]
    dollars = [
        '          $ 1,737.19  assets',
        '          $ 1,387.19     401k',
        '            $ 798.19       big co 500 idx',
        '            $ 400.00       bonds idx',
        '            $ 189.00       cash',
        '            $ 150.00     ira: glass idx',
        '            $ 200.00     mutual: total idx',
        '--------------------',
        '          $ 1,737.19',
        ''
    ]
    mock_lines.side_effect = [shares, dollars]
    args = investments.ArgHandler.get_args([])
    report = investments.Colorable.get_plain_text(
        investments.get_investment_report(args)
    )
    expected = '''$ 1,737.19   assets
                         $ 1,387.19      401k
       9.897 abcdx         $ 798.19        big co 500 idx
      20.000 lmnop         $ 400.00        bonds idx
                           $ 189.00        cash
      15.000 qwrty         $ 150.00      ira: glass idx
       5.000 yyzxx         $ 200.00      mutual: total idx'''
    assert report.strip() == expected


@mock.patch(__name__ + '.investments.get_lines')
def test_get_investment_report_single_line(mock_lines):
    shares = ['        15.000 qwrty  assets: ira: glass idx', '']
    dollars = ['            $ 150.00  assets: ira: glass idx', '']
    mock_lines.side_effect = [shares, dollars]
    args = investments.ArgHandler.get_args(['-a ira'])
    report = investments.Colorable.get_plain_text(
        investments.get_investment_report(args)
    )
    expected = '15.000 qwrty         $ 150.00   assets: ira: glass idx'
    assert report.strip() == expected
