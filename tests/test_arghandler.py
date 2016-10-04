#!/usr/bin/python

"""unit test for ledgerbil.py"""

import unittest

from redirector import Redirector
from arghandler import ArgHandler


__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

filename = 'dummy.ldg'


class Arguments(Redirector):

    def testFileShortOption(self):
        """should set parse args 'file' var"""
        args = ArgHandler.get_args(['-f', filename])
        self.assertTrue(args.file)

    def testFileLongOption(self):
        """should set parse args 'file' var"""
        args = ArgHandler.get_args(['--file', filename])
        self.assertTrue(args.file)

    def testFileOptionIsRequired(self):
        """should cause argparse error if file option not specified"""
        expected = 'error: argument -f/--file is required'
        try:
            ArgHandler.get_args([])
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testFileOptionAndFilenameBothRequired(self):
        """should cause argparse error if file opt specified w/o file"""
        expected = 'error: argument -f/--file: expected one argument'
        try:
            ArgHandler.get_args(['--file'])
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testSortShortOption(self):
        """should set parse args 'sort' var"""
        args = ArgHandler.get_args(['-f', filename, '-s'])
        self.assertTrue(args.sort)

    def testSortLongOption(self):
        """should set parse args 'sort' var"""
        args = ArgHandler.get_args(['--file', filename, '--sort'])
        self.assertTrue(args.sort)

    def testNoSortingOption(self):
        """should not set parse args 'sort' var"""
        args = ArgHandler.get_args(['--file', filename])
        self.assertFalse(args.sort)

    def testScheduleFileShortOption(self):
        """should set parse args 'schedule-file' var"""
        args = ArgHandler.get_args(['-f', filename, '-S', filename])
        self.assertTrue(args.schedule_file)

    def testScheduleFileLongOption(self):
        """should set parse args 'schedule-file' var"""
        args = ArgHandler.get_args([
            '--file', filename,
            '--schedule-file', filename,
        ])
        self.assertTrue(args.schedule_file)

    def testScheduleFilenameRequiredWithScheduleOption(self):
        """should cause argparse error if sched file opt specified w/o file"""
        expected = 'error: argument -S/--schedule-file: expected one argument'
        try:
            ArgHandler.get_args(['--file', filename, '--schedule-file'])
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)
