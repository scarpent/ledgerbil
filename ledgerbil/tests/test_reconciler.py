import os
import sys
from datetime import date
from textwrap import dedent
from unittest import TestCase, mock

import pytest
from dateutil.relativedelta import relativedelta

from .. import reconciler, settings, settings_getter, util
from ..ledgerbilexceptions import LdgReconcilerError
from ..ledgerfile import LedgerFile
from ..reconciler import Reconciler, run_reconciler
from . import filetester as FT
from .helpers import OutputFileTesterStdout, Redirector

next_week = util.get_date_string(date.today() + relativedelta(weeks=1))
testdata = dedent(
    f"""\
    2016/10/01 flibble
        e: smurg
        a: credit       $-11
        a: credit       $-22

    2016/10/26 one
        e: blurg
      * a: cash         $-10

    2016/10/26 one point five
        e: blurg
      * a: cash         $-5

    2016/10/27 two
        e: meep
        a: cash         $-20

    2016/10/27 two pt five
        e: meep 2
      ! a: cash         $-2.12

    2016/10/27 two point zwib
        i: jsdklfjsdlkjflksdjfklsd
        a: checking     $550

    {next_week} three
        e: fweep
      ! a: cash         $-30

    {next_week} four
        e: snurp
        a: cash         $-40
    """
)


class MockSettings:
    RECONCILER_CACHE_FILE = FT.CACHE_FILE_TEST
    ACCOUNT_ALIASES = {r"^sna:": "snafu:", r"^fu:": "fubar:"}

    def __init__(self):
        FT.delete_test_cache_file()


def setup_function():
    # Notice that this is used in class set ups as well...
    settings_getter.settings = MockSettings()


def teardown_function():
    settings_getter.settings = settings.Settings()


def assert_equal_floats(float1, float2, decimals=2):
    assert f"{float1:.{decimals}f}" == f"{float2:.{decimals}f}"


class SimpleOutputTests(Redirector):
    def test_syntax_error(self):
        with FT.temp_file(testdata) as tempfilename:
            interpreter = Reconciler([LedgerFile(tempfilename, "cash")])

        self.reset_redirect()
        bad_command = "cthulu"
        interpreter.onecmd(bad_command)
        expected = f"{Reconciler.UNKNOWN_SYNTAX}{bad_command}\n"
        assert self.redirect.getvalue() == expected

    def test_not_syntax_error(self):
        """ crudely verify basic commands """
        commands = [
            # 'statement', 'start', # do not test here (need input)
            "account",
            "aliases",
            "finish",
            "end",
            "help",
            "list",
            "l",
            "ll",
            "mark",
            "m",
            "quit",
            "q",
            "EOF",
            "reload",
            "r",
            "show",
            "s",
            "unmark",
            "u",
            "un",
        ]
        with FT.temp_file(testdata) as tempfilename:
            interpreter = Reconciler([LedgerFile(tempfilename, "cash")])

            for c in commands:
                self.reset_redirect()
                interpreter.onecmd(c)
                actual = self.redirect.getvalue().startswith(Reconciler.UNKNOWN_SYNTAX)
                assert actual is False

    def test_simple_help_check(self):
        commands = [
            "help account",
            "help aliases",
            "help help",
            "help list",
            "help l",
            "help ll",
            "help mark",
            "help m",
            "help quit",
            "help q",
            "help EOF",
            "help reload",
            "help r",
            "help show",
            "help s",
            "help start",
            "help finish",
            "help unmark",
            "help u",
        ]
        with FT.temp_file(testdata) as tempfilename:
            interpreter = Reconciler([LedgerFile(tempfilename, "cash")])

        for c in commands:
            self.reset_redirect()
            interpreter.onecmd(c)
            actual = self.redirect.getvalue().startswith(Reconciler.NO_HELP)
            assert actual is False


class OutputTests(Redirector):
    def setUp(self):
        super().setUp()
        settings_getter.settings = MockSettings()

    def tearDown(self):
        super().setUp()
        settings_getter.settings = settings.Settings()

    def test_mark_and_unmark_errors(self):

        multiple_matches = dedent(
            f"""

            2019/10/23 two
                e: beep
                a: cash         $-20
            """
        )

        with FT.temp_file(testdata + multiple_matches) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        self.reset_redirect()

        # none of these should result in a file write; we'll get out of
        # the context manager as an additional confirmation of this

        for command in [recon.do_mark, recon.do_unmark]:
            command("")
            expected = "*** Transaction numbers or amounts required\n"
            assert self.redirect.getvalue() == expected
            self.reset_redirect()
            command("ahchew")
            expected = "Transaction not found: ahchew\n"
            assert self.redirect.getvalue() == expected
            self.reset_redirect()
            command("1234.")
            expected = "Amount not found: 1234.\n"
            assert self.redirect.getvalue() == expected
            self.reset_redirect()
            command("twillig.")
            expected = "Amount not found: twillig.\n"
            assert self.redirect.getvalue() == expected
            self.reset_redirect()
            command("-20.")
            expected = (
                "More than one match for amount: -20. "
                "(Specify a line number instead.)\n"
            )
            assert self.redirect.getvalue() == expected
            self.reset_redirect()

        recon.do_list("")
        self.reset_redirect()

        recon.do_mark("2")
        assert self.redirect.getvalue() == "Already marked pending: 2\n"
        self.reset_redirect()
        recon.do_unmark("1")
        assert self.redirect.getvalue() == "Not marked; can't unmark: 1\n"

    def test_finish_balancing_errors(self):

        with FT.temp_file(testdata) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

            self.reset_redirect()
            recon.finish_balancing()
            expected = "*** Ending balance must be set in order to finish\n"
            assert self.redirect.getvalue() == expected

            self.reset_redirect()
            recon.ending_balance = -1234.56
            recon.finish_balancing()
            expected = '"To zero" must be zero in order to finish\n'
            assert self.redirect.getvalue() == expected
            # confirms it didn't revert to None as on success
            assert recon.ending_balance == -1234.56, recon.ending_balance

    def test_show_transaction_errors(self):

        with FT.temp_file(testdata) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "checking")])

        self.reset_redirect()
        recon.show_transaction("")
        expected = "*** Transaction number(s) required\n"
        assert self.redirect.getvalue() == expected
        self.reset_redirect()
        recon.show_transaction("blah")
        expected = "Transaction not found: blah\n"
        assert self.redirect.getvalue() == expected

    def test_show_one_transaction(self):
        expected = dedent(
            """\

            2016/10/27 two
                e: meep
                a: cash         $-20"""
        )

        with FT.temp_file(testdata) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        self.reset_redirect()
        recon.show_transaction("1")
        assert self.redirect.getvalue().rstrip() == expected

    def test_show_two_transactions(self):
        expected = dedent(
            """\

            2016/10/27 two
                e: meep
                a: cash         $-20

            2016/10/27 two pt five
                e: meep 2
              ! a: cash         $-2.12"""
        )

        with FT.temp_file(testdata) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        self.reset_redirect()
        recon.show_transaction("1 2")
        assert self.redirect.getvalue().rstrip() == expected


def test_mixed_shares_and_non_shares_raises_exception():
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment

        2017/11/28 zombie investments
            a: 401k: bonds idx
            i: investment: adjustment     $100,000
    """
    )

    with FT.temp_file(ledgerfile_data) as tempfilename:
        with pytest.raises(LdgReconcilerError) as excinfo:
            Reconciler([LedgerFile(tempfilename, "401k: bonds")])

    expected = 'Unhandled shares with non-shares: "a: 401k: bonds idx"'
    assert str(excinfo.value) == expected


def test_mixed_symbols_raises_exception():
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment

        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 abcde @   $20.05
            i: investment: adjustment
    """
    )

    with FT.temp_file(ledgerfile_data) as tempfilename:
        with pytest.raises(LdgReconcilerError) as excinfo:
            Reconciler([LedgerFile(tempfilename, "401k: bonds")])

    expected = 'Unhandled multiple symbols: "a: 401k: bonds idx": ' "['abcde', 'qwrty']"
    assert str(excinfo.value) == expected


def test_top_line_cleared_status_raises_exception_when_account_matched():
    ledgerfile_data = dedent(
        """
        2017/11/28 so
            fu: bar     $20
            credit card

        2017/11/28 * nar
            ra: dar     $30
            checking
    """
    )

    with FT.temp_file(ledgerfile_data) as tempfilename:
        with pytest.raises(LdgReconcilerError) as excinfo:
            Reconciler([LedgerFile(tempfilename, "checking")])

    expected = "Unhandled top line transaction status:\n2017/11/28 * nar"
    assert str(excinfo.value) == expected


def test_top_line_pending_status_raises_exception_when_account_matched():
    ledgerfile_data = dedent(
        """
        2017/11/28 so
            fu: bar     $20
            credit card

        2017/11/28 ! nar
            ra: dar     $30
            checking
    """
    )

    with FT.temp_file(ledgerfile_data) as tempfilename:
        with pytest.raises(LdgReconcilerError) as excinfo:
            Reconciler([LedgerFile(tempfilename, "checking")])

    expected = "Unhandled top line transaction status:\n2017/11/28 ! nar"
    assert str(excinfo.value) == expected


def test_top_line_status_does_not_raise_exception_when_account_not_matched():
    ledgerfile_data = dedent(
        """
        2017/11/28 so
            fu: bar     $20
            credit card

        2017/11/28 * nar
            ra: dar     $30
            checking
    """
    )

    with FT.temp_file(ledgerfile_data) as tempfilename:
        # should not raise LdgReconcilerError
        Reconciler([LedgerFile(tempfilename, "credit")])


def test_non_matching_accounts_in_different_files():
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment
    """
    )
    ledgerfile2_data = dedent(
        """
        2017/12/28 zombie investments
            a: 401k: james bonds idx      45.678 qwrty @   $31.11
            i: investment: adjustment
    """
    )

    with FT.temp_file(ledgerfile_data) as tempfilename:
        with FT.temp_file(ledgerfile2_data) as tempfilename2:
            with pytest.raises(LdgReconcilerError) as excinfo:
                Reconciler(
                    [
                        LedgerFile(tempfilename, "bonds"),
                        LedgerFile(tempfilename2, "bonds"),
                    ]
                )
    expected = dedent(
        """\
        More than one matching account:
            a: 401k: bonds idx
            a: 401k: james bonds idx"""
    )
    assert str(excinfo.value) == expected


def test_get_rec_account_matched_when_match_in_either_file():
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: stock idx            12.357 qwrty @   $20.05
            i: investment: adjustment
    """
    )
    ledgerfile2_data = dedent(
        """
        2017/12/28 zombie investments
            a: 401k: james bonds idx      45.678 qwrty @   $31.11
            i: investment: adjustment
    """
    )

    with FT.temp_file(ledgerfile_data) as tempfilename:
        with FT.temp_file(ledgerfile2_data) as tempfilename2:
            reconciler = Reconciler(
                [
                    LedgerFile(tempfilename, "james bonds"),
                    LedgerFile(tempfilename2, "james bonds"),
                ]
            )

    assert reconciler.get_rec_account_matched() == "a: 401k: james bonds idx"

    # reverse order of reconciler files
    with FT.temp_file(ledgerfile_data) as tempfilename:
        with FT.temp_file(ledgerfile2_data) as tempfilename2:
            reconciler = Reconciler(
                [
                    LedgerFile(tempfilename2, "james bonds"),
                    LedgerFile(tempfilename, "james bonds"),
                ]
            )

    assert reconciler.get_rec_account_matched() == "a: 401k: james bonds idx"


def test_get_rec_account_matched_when_match_in_neither_file():
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: stock idx            12.357 qwrty @   $20.05
            i: investment: adjustment
    """
    )
    ledgerfile2_data = dedent(
        """
        2017/12/28 zombie investments
            a: 401k: james bonds idx      45.678 qwrty @   $31.11
            i: investment: adjustment
    """
    )

    with FT.temp_file(ledgerfile_data) as tempfilename:
        with FT.temp_file(ledgerfile2_data) as tempfilename2:
            with pytest.raises(StopIteration):
                Reconciler(
                    [
                        LedgerFile(tempfilename, "goldfinger"),
                        LedgerFile(tempfilename2, "goldfinger"),
                    ]
                )


def test_init_things():
    with FT.temp_file(testdata) as tempfilename:
        ledgerfile = LedgerFile(tempfilename, "cash")
        recon = Reconciler([ledgerfile])

    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-32.12, recon.total_pending)
    payees = {thing.payee for thing in recon.open_transactions}
    # all open transactions, including the future:
    assert payees == ({"two", "two pt five", "three", "four"})
    payees = {thing.payee for k, thing in recon.current_listing.items()}
    # future items included only if pending ('three')
    assert payees == ({"two", "two pt five", "three"})
    assert recon.ending_date == date.today()
    assert recon.ending_balance is None
    assert len(recon.current_listing) == 3
    assert ledgerfile.rec_account_matched == "a: cash"


def test_list_all():
    with FT.temp_file(testdata) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "cash")])

    recon.do_list("")
    payees = {thing.payee for k, thing in recon.current_listing.items()}
    # future items included only if pending ('three')
    assert payees == ({"two", "two pt five", "three"})
    recon.do_list("aLL")
    payees = {thing.payee for k, thing in recon.current_listing.items()}
    assert payees == ({"two", "two pt five", "three", "four"})


def test_list():
    with FT.temp_file(testdata) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "cash")])

    recon.do_list("")
    payees = {thing.payee for k, thing in recon.current_listing.items()}
    # future items included only if pending ('three')
    assert payees == ({"two", "two pt five", "three"})
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-32.12, recon.total_pending)


def test_list_shares():
    ledgerfile_data = dedent(
        """
        2017/11/05 zombie investments
          ! a: 401k: big co 500 idx       1.555555 abcdx @   $81.02
            i: investment: adjustment

        2017/11/06 zombie investments
          ! a: 401k: big co 500 idx       1.666666 abcdx @   $82.50
            i: investment: adjustment

        2017/11/07 zombie investments
          * a: 401k: big co 500 idx       1.777777 abcdx @   $87.78
            i: investment: adjustment

        2017/11/09 zombie investments
          * a: 401k: big co 500 idx       2.123456 abcdx @   $88.98
            i: investment: adjustment

        2017/11/11 zombie investments
            a: 401k: big co 500 idx       2.181818 abcdx @   $89.29
            i: investment: adjustment

        2017/11/13 zombie investments
            a: 401k: big co 500 idx       3.123321 abcdx @   $90.11
            i: investment: adjustment
    """
    )

    with FT.temp_file(ledgerfile_data) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "401k: big co")])

    recon.do_list("")
    assert_equal_floats(3.901233, recon.total_cleared, decimals=6)
    assert_equal_floats(3.222221, recon.total_pending, decimals=6)


def test_list_and_modify():

    with FT.temp_file(testdata) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "cash")])

    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-32.12, recon.total_pending)
    recon.do_list("")
    payees = {thing.payee for k, thing in recon.current_listing.items()}
    assert payees == ({"two", "two pt five", "three"})
    recon.do_unmark("3")

    # 3 was a pending future transaction, so:
    # pending total is adjusted and one less current listing
    # (also, the mark should have triggered a new listing...)
    payees = {thing.payee for k, thing in recon.current_listing.items()}
    assert payees == ({"two", "two pt five"})
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-2.12, recon.total_pending)

    # open transactions shouldn't change
    payees = {thing.payee for thing in recon.open_transactions}
    assert payees == ({"two", "two pt five", "three", "four"})


def test_mark_and_unmark():

    with FT.temp_file(testdata) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "cash")])

    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-32.12, recon.total_pending)
    recon.do_mark("1")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-52.12, recon.total_pending)
    recon.do_unmark("1 2")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-30, recon.total_pending)
    recon.do_mark("1 2")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-52.12, recon.total_pending)
    recon.do_unmark("2")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-50, recon.total_pending)
    recon.do_mark("1 2 blurg")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-52.12, recon.total_pending)
    recon.do_unmark("blarg 2")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-50, recon.total_pending)
    recon.do_unmark("1 sdjfkljsdfkljsdl 2")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-30, recon.total_pending)
    recon.default("1")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-50, recon.total_pending)
    recon.do_unmark("-20.")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-30, recon.total_pending)
    recon.do_mark("-20. 2")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-52.12, recon.total_pending)

    # entry with account on multiple lines
    with FT.temp_file(testdata) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "credit")])

    assert_equal_floats(0, recon.total_cleared)
    assert_equal_floats(0, recon.total_pending)
    recon.do_mark("1")
    assert_equal_floats(0, recon.total_cleared)
    assert_equal_floats(-33, recon.total_pending)
    recon.do_unmark("1")
    assert_equal_floats(0, recon.total_cleared)
    assert_equal_floats(0, recon.total_pending)


def test_mark_and_unmark_all():

    with FT.temp_file(testdata) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "cash")])

    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-32.12, recon.total_pending)
    recon.do_unmark("all")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(0, recon.total_pending)
    recon.do_mark("all")
    assert_equal_floats(-15, recon.total_cleared)
    assert_equal_floats(-22.12, recon.total_pending)


def test_finish_balancing_with_errors():
    """Verify things don't change when there are errors"""
    with FT.temp_file(testdata) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "cash")])

    recon.finish_balancing()

    payees = {thing.payee for thing in recon.open_transactions}
    assert payees == ({"two", "two pt five", "three", "four"})
    payees = {thing.payee for k, thing in recon.current_listing.items()}
    # future items included only if pending ('three')
    assert payees == ({"two", "two pt five", "three"})

    recon.ending_balance = -1234.56
    recon.finish_balancing()
    assert recon.ending_balance == -1234.56
    payees = {thing.payee for thing in recon.open_transactions}
    assert payees == ({"two", "two pt five", "three", "four"})
    payees = {thing.payee for k, thing in recon.current_listing.items()}
    # future items included only if pending ('three')
    assert payees == ({"two", "two pt five", "three"})


class MockInput(TestCase):
    responses = []

    def mock_input(self, prompt):
        assert self.responses
        response = self.responses.pop(0)
        print((prompt + response))
        return response

    def setUp(self):
        super().setUp()
        self.save_input = input
        reconciler.input = self.mock_input

    def tearDown(self):
        super().tearDown()
        reconciler.input = self.save_input


class StatementAndFinishTests(MockInput, OutputFileTesterStdout):
    def setUp(self):
        super().setUp()

        class FixedDate(date):  # monkey patch date
            @classmethod
            def today(cls):
                return cls(2016, 10, 27)

        reconciler.date = FixedDate
        settings_getter.settings = MockSettings()

    def tearDown(self):
        super().tearDown()
        reconciler.date = date
        settings_getter.settings = settings.Settings()

    teststmt = dedent(
        """\
        2016/10/26 one
            e: blurg
            a: cash         $-10

        2016/10/29 two
            e: blurgerber
            a: cash         $-20
        """
    )

    testfinish = dedent(
        """
        2016/10/26 one
            e: blurg
          * a: cash         $-10

        2016/10/29 two
            e: blurgerber
          * a: cash         $-20
        """
    )

    teststmt_shares = dedent(
        """\
        2016/10/26 banana
            a: 401k: big co 500 idx     0.123456 abcdx @   $81.89
            i: investment: yargle

        2016/10/27 sweet potato
            a: 401k: big co 500 idx        2.111 abcdx @   $82.13
            i: investment: yargle
        """
    )

    teststmt_shares_finish = dedent(
        """\
        2016/10/26 banana
          * a: 401k: big co 500 idx     0.123456 abcdx @   $81.89
            i: investment: yargle

        2016/10/27 sweet potato
          * a: 401k: big co 500 idx        2.111 abcdx @   $82.13
            i: investment: yargle
        """
    )

    def test_setting_statement_date_and_balance(self):
        self.init_test("test_statement_stuff")

        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        # errors and no change
        self.responses = ["blurg", "", "abc", ""]
        recon.do_statement("")
        # new settings
        self.responses = ["2016/10/30", "1,234"]
        recon.do_statement("")
        # use $ symbol, no change
        self.responses = ["2016/10/30", "$1,234"]
        recon.do_statement("")

        self.conclude_test()

    def test_setting_statement_shares(self):
        self.init_test("test_statement_stuff_for_shares")

        with FT.temp_file(self.teststmt_shares) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "big co")])

        self.responses = ["2016/10/30", "0.1234567"]
        recon.do_statement("")
        # so we can verify rounding on the balance prompt
        self.responses = ["2016/10/30", "2.234456"]
        recon.do_statement("")

        self.conclude_test()

    def test_cancel_statement(self):
        self.init_test("test_cancel_statement_stuff")

        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        self.responses = ["2016/10/27", "50"]
        recon.do_statement("")
        self.responses = ["cAnCeL"]
        recon.do_statement("")
        assert recon.ending_balance is None
        print("<<< test: restart >>>")

        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        assert recon.ending_balance is None
        self.responses = ["2016/10/28", "40"]
        recon.do_statement("")
        self.responses = ["2016/10/28", "cancel"]
        recon.do_statement("")
        assert recon.ending_balance is None

    def test_cancel_statement_no_previous_ending(self):
        self.init_test("test_cancel_statement_stuff_no_previous")

        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        self.responses = ["cAnCeL"]
        recon.do_statement("")

    def test_finish(self):
        self.init_test("test_reconcile_finish")

        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

            self.responses = ["2016/10/30", "-30"]
            recon.do_statement("")
            recon.do_mark("1 2")
            recon.do_finish("")

        self.conclude_test()

    def test_finish_not_all_cleared(self):
        self.init_test("test_reconcile_finish_not_all_cleared")

        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

            self.responses = ["2016/10/30", "-20"]
            recon.do_statement("")
            recon.do_mark("2")
            recon.do_finish("")

        self.conclude_test()

    def test_finish_and_start_again(self):
        self.init_test("test_reconcile_finish_and_start_again")

        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

            self.responses = ["2016/10/30", "-30"]
            recon.do_statement("")
            recon.do_mark("1 2")
            recon.do_finish("")

        print("<<< test: reconcile again >>>")
        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

            self.responses = ["2016/10/30", "-30"]
            recon.do_statement("")
            recon.do_quit("")

        # To verify that previous_ entries remain
        print("<<< test: restart >>>")
        with FT.temp_file(self.testfinish) as tempfilename:
            Reconciler([LedgerFile(tempfilename, "cash")])

        self.conclude_test()

    def test_caching_with_quit(self):
        self.cache_test(do_quit=True)

    def test_caching_without_quit(self):
        """ same results if we don't quit """
        self.cache_test(do_quit=False)

    def cache_test(self, do_quit=True):
        self.init_test("test_reconciler_caching")

        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        self.responses = ["2030/03/30", "-30"]
        recon.do_statement("")
        if do_quit:
            recon.do_quit("")
        print("<<< test: restart >>>")

        with FT.temp_file(self.teststmt) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])
            recon.do_mark("1 2")
            recon.do_finish("")

        if do_quit:
            recon.do_quit("")
        print("<<< test: restart >>>")

        with FT.temp_file(self.testfinish) as tempfilename:
            Reconciler([LedgerFile(tempfilename, "cash")])

        self.conclude_test()

    def test_cache_with_shares(self):
        """The reconciler relies on open transactions to determine if we're
        reconciling dollars or shares. This test confirms that shares =
        true/false is stored in cache and that statement info is shown
        correctly when there are no open transactions. (Both when first
        finishing and when next reconciling this account.)"""
        self.init_test("test_reconciler_caching_with_shares")

        with FT.temp_file(self.teststmt_shares) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "big")])

            self.responses = ["2030/03/30", "2.234456"]
            recon.do_statement("")
            recon.do_mark("1 2")
            recon.do_finish("")

        print("<<< test: restart >>>")
        with FT.temp_file(self.teststmt_shares_finish) as tempfile:
            recon = Reconciler([LedgerFile(tempfile, "big")])

        self.conclude_test()


class ResponseTests(MockInput, Redirector):
    def test_get_response_with_none(self):
        """None should be preserved for no response"""
        self.responses = [""]
        assert Reconciler.get_response("prompt", None) is None
        self.responses = [""]
        assert Reconciler.get_response("prompt", "") == ""

    def test_get_response(self):
        self.responses = [""]
        actual = Reconciler.get_response("prompt", "preserve old value")
        assert actual == "preserve old value"
        self.responses = ["new value"]
        actual = Reconciler.get_response("prompt", "old value")
        assert actual == "new value"


testcache = dedent(
    """\
    2016/10/26 one
        e: blurg
        a: cash         $-10
    """
)


def test_get_key_and_cache_no_cache():
    assert not os.path.exists(settings_getter.get_setting("RECONCILER_CACHE_FILE"))

    with FT.temp_file(testcache) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "cash")])

    assert not os.path.exists(settings_getter.get_setting("RECONCILER_CACHE_FILE"))

    key, cache = recon.get_key_and_cache()
    assert key == "a: cash"
    assert cache == {}


@mock.patch(__name__ + ".reconciler.print")
def test_get_key_and_cache_error(mock_print):
    with FT.temp_file(testcache) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "cash")])

    with mock.patch(__name__ + ".reconciler.os.path.exists") as mock_exists:
        mock_exists.return_value = True
        with mock.patch("builtins.open") as mock_open:
            mock_open.side_effect = IOError("BLAH!")
            key, cache = recon.get_key_and_cache()
    expected = "Error getting reconciler cache: BLAH!"
    mock_print.assert_called_with(expected, file=sys.stderr)
    assert key == "a: cash"
    assert cache == {}


@mock.patch(__name__ + ".reconciler.print")
@mock.patch(__name__ + ".reconciler.Reconciler.get_key_and_cache")
def test_save_cache_error(mock_get_key_and_cache, mock_print):
    mock_get_key_and_cache.return_value = ("cash", {})
    with FT.temp_file(testcache) as tempfilename:
        recon = Reconciler([LedgerFile(tempfilename, "cash")])

    with mock.patch("builtins.open") as mock_open:
        mock_open.side_effect = IOError("BOO!")
        recon.save_statement_info_to_cache()
    expected = "Error writing reconciler cache: BOO!"
    mock_print.assert_called_with(expected, file=sys.stderr)


@mock.patch(__name__ + ".reconciler.print")
@mock.patch(__name__ + ".reconciler.Reconciler.get_date_and_balance")
@mock.patch(__name__ + ".reconciler.Reconciler.get_key_and_cache")
def test_previous_balance_is_zero(mock_get_key, mock_get_date, mock_print):
    teststmt = dedent(
        """\
        2016/10/26 one
            e: blurg
            a: cash         $-10
        """
    )
    mock_get_key.return_value = ("a: cash", {"a: cash": {}})
    mock_get_date.return_value = (date.today(), 0)
    with FT.temp_file(teststmt) as tempfilename:
        Reconciler([LedgerFile(tempfilename, "cash")])

    output = reconciler.Colorable.get_plain_string(mock_print.call_args_list[2][0][0])
    assert "previous balance: $ 0.00" in output


class CacheTests(MockInput, Redirector):
    def setUp(self):
        super().setUp()
        settings_getter.settings = MockSettings()

    def tearDown(self):
        super().setUp()
        settings_getter.settings = settings.Settings()

    testcache = dedent(
        """\
        2016/10/26 one
            e: blurg
            a: cash         $-10

        2016/10/26 two
            e: blurg
            a: credit       $-10
        """
    )

    def test_cache(self):
        with FT.temp_file(self.testcache) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        # saving cache with ending balance "None" causes cache "ending_"
        # entries to be removed; first let's make sure it works w/o
        # existing entry
        assert not os.path.exists(settings_getter.get_setting("RECONCILER_CACHE_FILE"))
        assert recon.ending_balance is None
        recon.save_statement_info_to_cache()
        _, cache = recon.get_key_and_cache()
        assert cache == {}

        # add entry
        recon.ending_balance = 100
        recon.ending_date = date(2020, 10, 20)
        recon.save_statement_info_to_cache()
        _, cache = recon.get_key_and_cache()
        expected = {"a: cash": {"ending_balance": 100, "ending_date": "2020/10/20"}}
        assert cache == expected

        # remove entry
        recon.ending_balance = None
        recon.save_statement_info_to_cache()
        _, cache = recon.get_key_and_cache()
        assert cache == {"a: cash": {}}

        # multiple entries
        recon.ending_balance = 111
        recon.ending_date = date(2111, 11, 11)
        recon.save_statement_info_to_cache()

        with FT.temp_file(self.testcache) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "credit")])

        recon.ending_balance = 222
        recon.ending_date = date(2222, 2, 22)
        recon.save_statement_info_to_cache()
        _, cache = recon.get_key_and_cache()
        expected = {
            "a: credit": {"ending_balance": 222, "ending_date": "2222/02/22"},
            "a: cash": {"ending_balance": 111, "ending_date": "2111/11/11"},
        }
        assert cache == expected

        # remove credit
        recon.ending_balance = None
        recon.save_statement_info_to_cache()
        _, cache = recon.get_key_and_cache()
        expected = {
            "a: cash": {"ending_balance": 111, "ending_date": "2111/11/11"},
            "a: credit": {},
        }
        assert cache == expected

        # indirectly verify get_statement_info_from_cache
        with FT.temp_file(self.testcache) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])

        # get_statement_info_from_cache will have been called in init
        assert recon.ending_balance == 111
        assert recon.ending_date == date(2111, 11, 11)


class ReloadTests(TestCase):
    def setUp(self):
        super().setUp()
        settings_getter.settings = MockSettings()

    def tearDown(self):
        super().setUp()
        settings_getter.settings = settings.Settings()

    testdata = dedent(
        """\
        2016/10/26 one
            e: blurg
            a: cash         $-10

        2016/10/29 two
            e: glarg
          * a: cash         $-20
        """
    )

    testdata_modified = dedent(
        """\
        2016/10/26 one
            e: blurg
            a: cash         $-10

        2016/10/29 two
            e: blarg
          * a: cash         $-55
        """
    )

    def test_reload(self):
        with FT.temp_file(self.testdata) as tempfilename:
            recon = Reconciler([LedgerFile(tempfilename, "cash")])
            assert recon.total_cleared == -20

            with open(tempfilename, "w", encoding="utf-8") as the_file:
                the_file.write(self.testdata_modified)

            assert recon.total_cleared == -20
            recon.do_reload("")
            assert recon.total_cleared == -55


@mock.patch(__name__ + ".reconciler.Reconciler.cmdloop")
def test_reconciler_cmdloop_called(mock_cmdloop):
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment
    """
    )
    with FT.temp_file(ledgerfile_data) as tempfilename:
        ledgerfile = LedgerFile(tempfilename, reconcile_account="bonds")
        return_value = run_reconciler([ledgerfile])
    assert return_value is None
    mock_cmdloop.assert_called_once()


@mock.patch(__name__ + ".util.handle_error")
def test_reconciler_exception(mock_print):
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment

        2017/11/28 zombie investments
            a: 401k: bonds idx
            i: investment: adjustment     $100,000
    """
    )
    with FT.temp_file(ledgerfile_data) as tempfilename:
        ledgerfile = LedgerFile(tempfilename, reconcile_account="bonds")
        run_reconciler([ledgerfile])
    expected = 'Unhandled shares with non-shares: "a: 401k: bonds idx"'
    mock_print.assert_called_once_with(expected)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (("a", "b", "c", "d"), "         a             b             c  d"),
        (("a", 2.0, 0, "d"), "         a           2.0             0  d"),
    ],
)
@mock.patch(__name__ + ".reconciler.print")
def test_print_reconciled_status_line(mock_print, test_input, expected):
    reconciler.print_reconciled_status_line(*test_input)
    mock_print.assert_called_once_with(expected)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("fu: blah", "fubar: blah"),
        ("sna: glarg", "snafu: glarg"),
        ("ra: dar", "ra: dar"),
    ],
)
def test_get_expanded_account_name(test_input, expected):
    assert reconciler.get_expanded_account_name(test_input) == expected


def test_get_expanded_account_name_aliases_not_defined():
    class MockSettingsNoAliases:
        pass

    settings_getter.settings = MockSettingsNoAliases()
    assert reconciler.get_expanded_account_name("abc: def") == "abc: def"


@mock.patch(__name__ + ".reconciler.print")
def test_reconciled_status_report_no_mismatches(mock_print):
    accounts = {"a": reconciler.ReconData("fu: bar", "1997/01/01", 10.0, 10.0)}
    reconciler.reconciled_status_report(accounts)
    expected = (
        "Previous balances match cleared balances from ledger "
        "for 1 accounts found in reconciler cache."
    )
    mock_print.assert_called_once_with(expected)


@mock.patch(__name__ + ".reconciler.print")
def test_reconciled_status_report_no_accounts(mock_print):
    accounts = {}
    reconciler.reconciled_status_report(accounts)
    expected = (
        "Previous balances match cleared balances from ledger "
        "for 0 accounts found in reconciler cache."
    )
    mock_print.assert_called_once_with(expected)


@mock.patch(__name__ + ".reconciler.print_reconciled_status_line")
@mock.patch(__name__ + ".reconciler.print")
def test_reconciled_status_report_mismatch(mock_print, mock_print_status_line):
    accounts = {
        "fu: bar": reconciler.ReconData("f: bar", "1997/01/01", 10.0, 10.0),
        "abc: def": reconciler.ReconData("a: def", "2007/07/07", 15.0, 10.0),
    }
    reconciler.reconciled_status_report(accounts)

    mock_print_status_line.assert_has_calls(
        [
            mock.call("2007/07/07", 15.0, 10.0, "a: def"),
            mock.call("prev date", "prev balance", "ldg cleared", "account"),
        ]
    )

    expected = reconciler.Colorable(
        "red",
        "Accounts found in reconciler cache with differing amounts "
        "between previous balance and cleared balance from ledger.",
    )

    mock_print.assert_called_once_with(expected)


@mock.patch(__name__ + ".reconciler.get_reconciler_cache")
def test_get_accounts_reconciled_data(mock_get_cache):
    mock_get_cache.return_value = {
        "a: 401k: big co 500 idx": {},  # not sure if can happen
        "a: 401k: bonds idx": {  # account has been reconciled
            "ending_balance": -59.0,
            "ending_date": "2018/01/16",
            "previous_balance": 22.357,
            "previous_date": "2018/01/16",
        },
        # account reconciling in progress, never fully reconciled
        "fu: glurg": {  # alias fu: = expanded fubar:
            "ending_balance": 500.0,
            "ending_date": "2018/07/13",
        },
        # shares example although we don't care about this for recon status
        "a: ira: glass idx": {
            "previous_balance": 15.0,
            "previous_date": "2018/07/15",
            "shares": True,
        },
    }
    accounts = reconciler.get_accounts_reconciled_data()
    expected = {
        "a: 401k: big co 500 idx": reconciler.ReconData(
            account="a: 401k: big co 500 idx",
            previous_date="-",
            previous_balance=0,
            ledger_balance=0,
        ),
        "a: 401k: bonds idx": reconciler.ReconData(
            account="a: 401k: bonds idx",
            previous_date="2018/01/16",
            previous_balance=22.357,
            ledger_balance=0,
        ),
        "fubar: glurg": reconciler.ReconData(
            account="fu: glurg", previous_date="-", previous_balance=0, ledger_balance=0
        ),
        "a: ira: glass idx": reconciler.ReconData(
            account="a: ira: glass idx",
            previous_date="2018/07/15",
            previous_balance=15.0,
            ledger_balance=0,
        ),
    }
    assert accounts == expected


@mock.patch(__name__ + ".reconciler.get_ledger_output")
@mock.patch(__name__ + ".reconciler.reconciled_status_report")
@mock.patch(__name__ + ".reconciler.get_accounts_reconciled_data")
def test_reconciled_status(mock_get_accounts, mock_status_report, mock_ledger_output):
    # 'x: y' account with a 0 previous balance tests where ledger won't return
    # a balance line for it so that we need to check if the account is in the
    # ledger_balances dictionary.
    accounts = {
        "fu: bar": reconciler.ReconData("f: bar", "1997/01/01", 10.0, 0),
        "abc: def": reconciler.ReconData("a: def", "2007/07/07", 15.0, 0),
        "x: y": reconciler.ReconData("x: y", "2012/09/09", 0.0, 0),
    }
    mock_get_accounts.return_value = accounts
    mock_ledger_output.return_value = dedent(
        """\
        1.234 abc  fu: bar
        $ -98.76 abc: def"""
    )

    reconciler.reconciled_status()

    mock_ledger_output.assert_called_once_with(
        ("balance", "--cleared", "--no-total", "--flat", "--exchange", ".")
    )

    accounts["fu: bar"].ledger_balance = 1.234
    accounts["abc: def"].ledger_balance = -98.76
    mock_status_report.assert_called_once_with(accounts)


@mock.patch(__name__ + ".reconciler.get_ledger_output")
@mock.patch(__name__ + ".reconciler.print")
@mock.patch(__name__ + ".reconciler.get_accounts_reconciled_data")
def test_reconciled_status_no_previously_reconciled(
    mock_get_accounts_reconciled_data, mock_print, mock_get_ledger_output
):
    accounts = {"fu: bar": reconciler.ReconData("f: bar", "-", 0, 0)}
    mock_get_accounts_reconciled_data.return_value = accounts

    reconciler.reconciled_status()

    mock_print.assert_called_once_with("No previously reconciled accounts found")
    assert not mock_get_ledger_output.called


@mock.patch(__name__ + ".reconciler.reconciled_status_report")
@mock.patch(__name__ + ".reconciler.get_ledger_output")
@mock.patch(__name__ + ".reconciler.get_accounts_reconciled_data")
def test_reconciled_status_no_cleared_balance_for_previously_reconciled(
    mock_get_accounts_reconciled_data, mock_get_ledger_output, mock_status_report
):
    # This test covers the exceedingly unlikely event that we have a previous
    # balance in reconciler cache, but no --cleared balances. We don't want to
    # blow up accessing a None. We'll still accurately report a problem with
    # the balance in the report.
    accounts = {"fu: bar": reconciler.ReconData("f: bar", "1997/01/01", 10.0, 0.0)}
    mock_get_accounts_reconciled_data.return_value = accounts
    mock_get_ledger_output.return_value = ""

    reconciler.reconciled_status()

    mock_status_report.assert_called_once_with(accounts)
