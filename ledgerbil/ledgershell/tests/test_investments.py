import os
import shlex
from unittest import mock

import pytest

from ... import settings, settings_getter
from .. import investments


class MockSettings:
    LEDGER_DIR = "lmn"
    LEDGER_FILES = ["blarg.ldg", "glurg.ldg"]
    PRICES_FILE = os.path.join(LEDGER_DIR, "ijk")
    LEDGER_COMMAND = ("ledger", "--market", "--price-db", PRICES_FILE)
    INVESTMENT_DEFAULT_ACCOUNTS = "abc or cba"
    INVESTMENT_DEFAULT_END_DATE = "xyz"


class MockSettingsAltDefaults(MockSettings):
    INVESTMENT_DEFAULT_ACCOUNTS = "fu or bar"
    INVESTMENT_DEFAULT_END_DATE = "blarg"


def setup_function():
    settings_getter.settings = MockSettings()


def teardown_function():
    settings_getter.settings = settings.Settings()


@mock.patch(__name__ + ".investments.print")
def test_warn_negative_dollars(mock_print):
    expected = 'Negative dollar amount -10 for "blah".'
    investments.warn_negative_dollars("-10", "blah")
    output = investments.Colorable.get_plain_string(mock_print.call_args[0][0])
    assert expected in output


def test_get_investment_command_options_defaults():
    expected = (
        ("bal",)
        + tuple(shlex.split(MockSettings.INVESTMENT_DEFAULT_ACCOUNTS))
        + ("--no-total",)
        + ("--end", MockSettings.INVESTMENT_DEFAULT_END_DATE)
    )
    actual = investments.get_investment_command_options(
        MockSettings.INVESTMENT_DEFAULT_ACCOUNTS,
        MockSettings.INVESTMENT_DEFAULT_END_DATE,
    )
    assert actual == expected


def test_get_investment_command_options_shares():
    expected = (
        ("bal",)
        + tuple(shlex.split(MockSettings.INVESTMENT_DEFAULT_ACCOUNTS))
        + ("--no-total", "--exchange", ".")
        + ("--end", MockSettings.INVESTMENT_DEFAULT_END_DATE)
    )
    actual = investments.get_investment_command_options(
        MockSettings.INVESTMENT_DEFAULT_ACCOUNTS,
        MockSettings.INVESTMENT_DEFAULT_END_DATE,
        shares=True,
    )
    assert actual == expected


def test_get_investment_command_options_account_with_spaces():
    expected = (
        "bal",
        "no_space",
        "with space",
        "also with spaces",
        "--no-total",
        "--exchange",
        ".",
        "--end",
        MockSettings.INVESTMENT_DEFAULT_END_DATE,
    )
    actual = investments.get_investment_command_options(
        """no_space "with space" 'also with spaces'""",
        MockSettings.INVESTMENT_DEFAULT_END_DATE,
        shares=True,
    )
    assert actual == expected


@mock.patch(__name__ + ".investments.print")
@mock.patch(__name__ + ".investments.get_ledger_output")
def test_get_lines_default_args(mock_get_ledger_output, mock_print):
    args = investments.get_args([])
    mock_get_ledger_output.return_value = "1\n2\n3"
    lines = investments.get_lines(args)
    assert lines == ["1", "2", "3"]
    mock_get_ledger_output.assert_called_once_with(
        ("bal",)
        + tuple(shlex.split(MockSettings.INVESTMENT_DEFAULT_ACCOUNTS))
        + ("--no-total",)
        + ("--end", MockSettings.INVESTMENT_DEFAULT_END_DATE)
    )
    assert not mock_print.called


@mock.patch(__name__ + ".investments.print")
@mock.patch(__name__ + ".investments.get_ledger_output")
def test_get_lines_with_args(mock_get_ledger_output, mock_print):
    args = investments.get_args(["--accounts", "fu bar", "--end", "ing"])
    mock_get_ledger_output.return_value = "1\n2\n3"
    lines = investments.get_lines(args)
    assert lines == ["1", "2", "3"]
    mock_get_ledger_output.assert_called_once_with(
        ("bal", "fu", "bar", "--no-total", "--end", "ing")
    )
    assert not mock_print.called


@mock.patch(__name__ + ".investments.print")
@mock.patch(__name__ + ".investments.get_ledger_output")
def test_get_lines_shares_and_alt_defaults(mock_get_ledger_output, mock_print):
    settings_getter.settings = MockSettingsAltDefaults()
    args = investments.get_args([])
    mock_get_ledger_output.return_value = "1\n2\n3"
    lines = investments.get_lines(args, shares=True)
    assert lines == ["1", "2", "3"]
    accounts = MockSettingsAltDefaults.INVESTMENT_DEFAULT_ACCOUNTS
    mock_get_ledger_output.assert_called_once_with(
        ("bal",)
        + tuple(shlex.split(accounts))
        + ("--no-total", "--exchange", ".")
        + ("--end", MockSettingsAltDefaults.INVESTMENT_DEFAULT_END_DATE)
    )
    assert not mock_print.called


@mock.patch(__name__ + ".investments.print")
@mock.patch(__name__ + ".investments.get_ledger_output")
def test_get_lines_print_command(mock_get_ledger_output, mock_print):
    args = investments.get_args(["--command"])
    mock_get_ledger_output.return_value = "1\n2\n3"
    lines = investments.get_lines(args)
    assert lines == ["1", "2", "3"]
    mock_get_ledger_output.assert_called_once_with(
        ("bal",)
        + tuple(shlex.split(MockSettings.INVESTMENT_DEFAULT_ACCOUNTS))
        + ("--no-total",)
        + ("--end", MockSettings.INVESTMENT_DEFAULT_END_DATE)
    )
    expected_print = (
        "ledger --market --price-db lmn/ijk -f lmn/blarg.ldg "
        "-f lmn/glurg.ldg bal abc or cba --no-total --end xyz"
    )
    mock_print.assert_called_once_with(expected_print)


@mock.patch(__name__ + ".investments.get_lines")
def test_get_investment_report(mock_ledger_output):
    shares = [
        "            $ 189.00",
        "     1,019.897 abcdx",
        "        20.000 lmnop",
        "        15.000 qwrty",
        "         5.000 yyzxx  assets",
        "            $ 189.00",
        "     1,019.897 abcdx",
        "        20.000 lmnop     401k",
        "     1,019.897 abcdx       big co 500 idx",
        "        20.000 lmnop       bonds idx",
        "            $ 189.00       cash",
        "        15.000 qwrty     ira: glass idx",
        "         5.000 yyzxx     mutual: total idx",
    ]
    dollars = [
        "          $ 1,737.19  assets",
        "          $ 1,387.19     401k",
        "             $798.19       big co 500 idx",
        "           $  400.00       bonds idx",
        "            $ 189.00       cash",
        "            $ 150.00     ira: glass idx",
        "            $ 200.00     mutual: total idx",
    ]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])
    report = investments.Colorable.get_plain_string(
        investments.get_investment_report(args)
    )
    expected = """$ 1,737.19   assets
                         $ 1,387.19      401k
   1,019.897 abcdx         $ 798.19        big co 500 idx
        20.0 lmnop         $ 400.00        bonds idx
                           $ 189.00        cash
        15.0 qwrty         $ 150.00      ira: glass idx
         5.0 yyzxx         $ 200.00      mutual: total idx"""
    assert report.strip() == expected


@mock.patch(__name__ + ".investments.get_lines")
def test_get_investment_report_matching_shares_and_symbol(mock_ledger_output):
    shares = [
        "            $ 189.00",
        "        19.796 abcdx",
        "        40.000 lmnop  assets",
        "            $ 189.00",
        "         9.898 abcdx",
        "        20.000 lmnop     401k",
        "         9.898 abcdx       big co 500 idx",
        "        20.000 lmnop       bonds idx",
        "            $ 189.00       cash",
        "         9.898 abcdx",
        "        20.000 lmnop     abc: xyz",
        "         9.898 abcdx       big co 500 idx",
        "        20.000 lmnop       bonds idx",
    ]
    dollars = [
        "          $ 2,592.87  assets",
        "          $ 1,390.94     401k",
        "            $ 801.94       big co 500 idx",
        "            $ 400.00       bonds idx",
        "            $ 189.00       cash",
        "          $ 1,201.94     abc: xyz",
        "            $ 801.94       big co 500 idx",
        "            $ 400.00       bonds idx",
    ]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])
    report = investments.Colorable.get_plain_string(
        investments.get_investment_report(args)
    )
    expected = """$ 2,592.87   assets
                         $ 1,390.94      401k
       9.898 abcdx         $ 801.94        big co 500 idx
        20.0 lmnop         $ 400.00        bonds idx
                           $ 189.00        cash
                         $ 1,201.94      abc: xyz
       9.898 abcdx         $ 801.94        big co 500 idx
        20.0 lmnop         $ 400.00        bonds idx"""
    assert report.strip() == expected


@mock.patch(__name__ + ".investments.get_lines")
def test_zero_dollar_amount(mock_ledger_output):
    shares = [
        "        10.000 abcdx",
        "       -40.000 lmnop  assets: 401k",
        "        10.000 abcdx     big co 500 idx",
        "       -40.000 lmnop     bonds idx",
    ]
    dollars = [
        "                   0  assets: 401k",
        "            $ 800.00     big co 500 idx",
        "           $ -800.00     bonds idx",
    ]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])
    report = investments.Colorable.get_plain_string(
        investments.get_investment_report(args)
    )
    expected = """0   assets: 401k
        10.0 abcdx         $ 800.00      big co 500 idx
       -40.0 lmnop        $ -800.00      bonds idx"""
    assert report.strip() == expected


@mock.patch(__name__ + ".investments.get_lines")
def test_get_investment_report_single_line(mock_ledger_output):
    shares = ["        15.000 qwrty  assets: ira: glass idx"]
    dollars = ["            $ 150.00  assets: ira: glass idx"]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])
    report = investments.Colorable.get_plain_string(
        investments.get_investment_report(args)
    )
    expected = "15.0 qwrty         $ 150.00   assets: ira: glass idx"
    assert report.strip() == expected


@mock.patch(__name__ + ".investments.print")
@mock.patch(__name__ + ".investments.get_lines")
def test_less_than_zero(mock_ledger_output, mock_print):
    shares = ["        -0.103 abcdx  assets: 401k: big co 500 idx"]
    dollars = ["             $ -8.31  assets: 401k: big co 500 idx"]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])

    expected_report = "-0.103 abcdx          $ -8.31   assets: 401k: big co 500 idx"
    expected_print = 'Negative dollar amount -8.31 for "assets: 401k: big co 500 idx".'
    actual_report = investments.Colorable.get_plain_string(
        investments.get_investment_report(args)
    )
    actual_print = investments.Colorable.get_plain_string(mock_print.call_args[0][0])

    assert actual_report.strip() == expected_report
    assert expected_print in actual_print


@mock.patch(__name__ + ".investments.print")
@mock.patch(__name__ + ".investments.get_lines")
def test_less_than_zero_cash(mock_ledger_output, mock_print):
    shares = ["        $ -10.00  cash"]
    dollars = ["             $ -10.00  cash"]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])

    expected_report = "$ -10.00   cash"
    expected_print = 'Negative dollar amount -10.0 for "cash".'
    actual_report = investments.Colorable.get_plain_string(
        investments.get_investment_report(args)
    )
    actual_print = investments.Colorable.get_plain_string(mock_print.call_args[0][0])

    assert actual_report.strip() == expected_report
    assert expected_print in actual_print


@mock.patch(__name__ + ".investments.get_lines")
def test_less_than_one_share(mock_ledger_output):
    shares = ["         0.001 abcdx  assets: 401k: big co 500 idx"]
    dollars = ["              $ 0.08  assets: 401k: big co 500 idx"]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])
    report = investments.Colorable.get_plain_string(
        investments.get_investment_report(args)
    )
    expected = "0.001 abcdx           $ 0.08   assets: 401k: big co 500 idx"
    assert report.strip() == expected


@mock.patch(__name__ + ".investments.get_lines")
def test_assertion_for_non_matching_shares_regex(mock_ledger_output):
    shares = ["bad abcdx  assets: blah: blah"]
    dollars = ["              $ 0.08  assets: 401k: big co 500 idx"]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])
    with pytest.raises(AssertionError) as excinfo:
        investments.get_investment_report(args)
    expected = "Did not find expected account and shares: bad abcdx  assets: blah: blah"
    assert str(excinfo.value) == expected


@mock.patch(__name__ + ".investments.get_lines")
def test_assertion_for_non_matching_dollar_regex(mock_ledger_output):
    shares = ["         0.001 abcdx  assets: 401k: big co 500 idx"]
    dollars = ["bad assets: fu: bar"]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])
    with pytest.raises(AssertionError) as excinfo:
        investments.get_investment_report(args)
    expected = "Did not find expected account and dollars: bad assets: fu: bar"
    assert str(excinfo.value) == expected


@mock.patch(__name__ + ".investments.get_lines")
def test_assertion_for_non_matching_accounts(mock_ledger_output):
    shares = ["         0.001 abcdx  assets: fu"]
    dollars = ["              $ 0.08  assets: bar"]
    mock_ledger_output.side_effect = [shares, dollars]
    args = investments.get_args([])
    with pytest.raises(AssertionError) as excinfo:
        investments.get_investment_report(args)
    expected = "Non-matching accounts. Shares:   assets: fu, Dollars:   assets: bar"
    assert str(excinfo.value) == expected


@mock.patch(__name__ + ".investments.print")
@mock.patch(__name__ + ".investments.get_lines")
def test_main(mock_get_lines, mock_print):
    shares = ["        15.000 qwrty  assets: ira: glass idx"]
    dollars = ["            $ 150.00  assets: ira: glass idx"]
    mock_get_lines.side_effect = [shares, dollars]
    investments.main([])
    output = investments.Colorable.get_plain_string(mock_print.call_args[0][0])
    expected = "15.0 qwrty         $ 150.00   assets: ira: glass idx"
    assert output.strip() == expected
    assert mock_print.call_args[1] == {"end": ""}


@mock.patch(__name__ + ".investments.get_args")
@mock.patch(__name__ + ".investments.get_investment_report")
def test_main_no_params(mock_get_investment_report, mock_get_args):
    investments.main()
    mock_get_args.assert_called_once_with([])
    assert mock_get_investment_report.called


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (["-a", "blah or blarg"], "blah or blarg"),
        (["--accounts", "fu or bar"], "fu or bar"),
        ([], "abc or cba"),  # default in MockSettings
    ],
)
def test_args_accounts(test_input, expected):
    args = investments.get_args(test_input)
    assert args.accounts == expected


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (["-e", "yesterday"], "yesterday"),
        (["--end", "2017/10/05"], "2017/10/05"),
        ([], "xyz"),  # default in MockSettings
    ],
)
def test_args_end_date(test_input, expected):
    args = investments.get_args(test_input)
    assert args.end == expected


@pytest.mark.parametrize(
    "test_input, expected", [(["-c"], True), (["--command"], True), ([], False)]
)
def test_args_command(test_input, expected):
    args = investments.get_args(test_input)
    assert args.command is expected
