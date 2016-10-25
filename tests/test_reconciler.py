#!/usr/bin/python

from unittest import TestCase

from filetester import FileTester
from helpers import Redirector
from reconciler import Reconciler


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class SimpleOutputTests(Redirector):

    def test_syntax_error(self):
        interpreter = Reconciler(
            FileTester.testdir + 'reconcile.ledger',
            'cash'
        )
        bad_command = 'cthulu'
        interpreter.onecmd(bad_command)
        self.assertEqual(
            Reconciler.UNKNOWN_SYNTAX + bad_command,
            self.redirect.getvalue().rstrip()
        )

    def test_not_syntax_error(self):
        """ crudely verify basic commands """
        commands = [
            'help',
            'aliases',
            'quit', 'q', 'EOF',
            #'list', 'l', 'll',
        ]
        interpreter = Reconciler(
            FileTester.testdir + 'reconcile.ledger',
            'cash'
        )
        for c in commands:
            self.reset_redirect()
            interpreter.onecmd(c)
            self.assertFalse(
                self.redirect.getvalue().startswith(
                    Reconciler.UNKNOWN_SYNTAX
                )
            )

    def test_simple_help_check(self):
        commands = [
            'help help',
            'help aliases',
            #'help list', 'help l', 'help ll',
            'help quit', 'help q', 'help EOF',
        ]
        interpreter = Reconciler(
            FileTester.testdir + 'reconcile.ledger',
            'cash'
        )
        for c in commands:
            self.reset_redirect()
            interpreter.onecmd(c)
            self.assertFalse(
                self.redirect.getvalue().startswith(Reconciler.NO_HELP)
            )
