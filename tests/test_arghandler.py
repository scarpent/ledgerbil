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
        args = ArgHandler.getArgs(['-f', filename])
        self.assertTrue(args.file)

    def testFileLongOption(self):
        """should set parse args 'file' var"""
        args = ArgHandler.getArgs(['--file', filename])
        self.assertTrue(args.file)

    def testFileOptionIsRequired(self):
        """should cause argparse error if file option not specified"""
        expected = 'error: argument -f/--file is required'
        try:
            ArgHandler.getArgs([])
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testFileOptionAndFilenameBothRequired(self):
        """should cause argparse error if file opt specified w/o file"""
        expected = 'error: argument -f/--file: expected one argument'
        try:
            ArgHandler.getArgs(['--file'])
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testSortShortOption(self):
        """should set parse args 'sort' var"""
        args = ArgHandler.getArgs(['-f', filename, '-s'])
        self.assertTrue(args.sort)

    def testSortLongOption(self):
        """should set parse args 'sort' var"""
        args = ArgHandler.getArgs(['--file', filename, '--sort'])
        self.assertTrue(args.sort)

    def testNoSortingOption(self):
        """should not set parse args 'sort' var"""
        args = ArgHandler.getArgs(['--file', filename])
        self.assertFalse(args.sort)

    def testScheduleFileShortOption(self):
        """should set parse args 'schedule-file' var"""
        args = ArgHandler.getArgs(['-f', filename, '-S', filename])
        self.assertTrue(args.schedule_file)

    def testScheduleFileLongOption(self):
        """should set parse args 'schedule-file' var"""
        args = ArgHandler.getArgs([
            '--file', filename,
            '--schedule-file', filename,
        ])
        self.assertTrue(args.schedule_file)

    def testScheduleFilenameRequiredWithScheduleOption(self):
        """should cause argparse error if sched file opt specified w/o file"""
        expected = 'error: argument -S/--schedule-file: expected one argument'
        try:
            ArgHandler.getArgs(['--file', filename, '--schedule-file'])
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testPreviewFileShortOption(self):
        """should set parse args 'schedule-file' var"""
        args = ArgHandler.getArgs(['-f', filename, '-p', filename])
        self.assertTrue(args.preview_file)

    def testPreviewFileLongOption(self):
        """should set parse args 'schedule-file' var"""
        args = ArgHandler.getArgs([
            '--file', filename,
            '--preview-file', filename,
        ])
        self.assertTrue(args.preview_file)

    def testPreviewFilenameRequiredWithPreviewOption(self):
        """should cause argparse error if sched file opt specified w/o file"""
        expected = 'error: argument -p/--preview-file: expected one argument'
        try:
            ArgHandler.getArgs(['--file', filename, '--preview-file'])
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)


if __name__ == "__main__":
    unittest.main()         # pragma: no cover
