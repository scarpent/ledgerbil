from unittest import mock

import pytest

from .. import arghandler
from .helpers import Redirector

filename = 'dummy.ldg'


class Arguments(Redirector):

    def test_file_option(self):
        args = arghandler.get_args(['-f', filename])
        self.assertTrue(args.file)
        args = arghandler.get_args(['--file', filename])
        self.assertTrue(args.file)

    def test_file_option_and_filename_both_required(self):
        """should cause argparse error if file opt specified w/o file"""
        expected = 'error: argument -f/--file: expected one argument'
        try:
            arghandler.get_args(['--file'])
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def test_sort_option(self):
        args = arghandler.get_args(['-f', filename, '-s'])
        self.assertTrue(args.sort)
        args = arghandler.get_args(['--file', filename, '--sort'])
        self.assertTrue(args.sort)

    def test_no_sorting_option(self):
        """should not set parse args 'sort' var"""
        args = arghandler.get_args(['--file', filename])
        self.assertFalse(args.sort)

    def test_schedule_file_option(self):
        args = arghandler.get_args(['-f', filename, '-S', filename])
        self.assertTrue(args.schedule_file)
        args = arghandler.get_args([
            '--file', filename,
            '--schedule-file', filename,
        ])
        self.assertTrue(args.schedule_file)

    def test_schedule_filename_required_with_schedule_option(self):
        """argparse error if sched file opt specified w/o file"""
        expected = (
            'error: argument -S/--schedule-file: expected one argument'
        )
        try:
            arghandler.get_args(['--file', filename, '--schedule-file'])
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)


@pytest.mark.parametrize('test_input, expected', [
    ('-n', True),
    ('--next-scheduled-date', True),
    ('', False),
])
def test_next_scheduled_date(test_input, expected):
    options = ['-f', filename]
    if test_input:
        options.append(test_input)
    args = arghandler.get_args(options)
    assert args.next_scheduled_date == expected


@mock.patch(__name__ + '.arghandler.argparse.ArgumentParser.print_help')
def test_no_parameters(mock_print_help):
    arghandler.get_args([])
    mock_print_help.assert_called_once()
