#!/usr/bin/python

"""unit test for ledgerbil.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest
import sys

from redirector import Redirector
from arghandler import ArgHandler

mainfile = 'dummy.py'
filename = 'dummy.ldg'


# consider alternatives for command line tests: TextTestRunner,
# if name == 'main': unittest.main(exit=False)
# see: http://stackoverflow.com/questions/79754/unittest-causing-sys-exit
class Arguments(Redirector):

    def testFileShortOption(self):
        """should set parse args 'file' var"""
        sys.argv = [mainfile, '-f', filename]
        args = ArgHandler.getArgs()
        self.assertTrue(args.file)

    def testFileLongOption(self):
        """should set parse args 'file' var"""
        sys.argv = [mainfile, '--file', filename]
        args = ArgHandler.getArgs()
        self.assertTrue(args.file)

    def testFileOptionIsRequired(self):
        """should cause argparse error if file option not specified"""
        expected = 'error: argument -f/--file is required'
        sys.argv = [mainfile]
        try:
            ArgHandler.getArgs()
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testFileOptionAndFilenameBothRequired(self):
        """should cause argparse error if file opt specified w/o file"""
        expected = 'error: argument -f/--file: expected one argument'
        sys.argv = [mainfile, '--file']
        try:
            ArgHandler.getArgs()
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testSortShortOption(self):
        """should set parse args 'sort' var"""
        sys.argv = [mainfile, '-f', filename, '-s']
        args = ArgHandler.getArgs()
        self.assertTrue(args.sort)

    def testSortLongOption(self):
        """should set parse args 'sort' var"""
        sys.argv = [mainfile, '--file', filename, '--sort']
        args = ArgHandler.getArgs()
        self.assertTrue(args.sort)

    def testNoSortingOption(self):
        """should not set parse args 'sort' var"""
        sys.argv = [mainfile, '--file', filename]
        args = ArgHandler.getArgs()
        self.assertFalse(args.sort)

    def testScheduleFileShortOption(self):
        """should set parse args 'schedule-file' var"""
        sys.argv = [mainfile, '-f', filename, '-S', filename]
        args = ArgHandler.getArgs()
        self.assertTrue(args.schedule_file)

    def testScheduleFileLongOption(self):
        """should set parse args 'schedule-file' var"""
        sys.argv = [mainfile, '--file', filename, '--schedule-file', filename]
        args = ArgHandler.getArgs()
        self.assertTrue(args.schedule_file)

    def testScheduleFilenameRequiredWithScheduleOption(self):
        """should cause argparse error if sched file opt specified w/o file"""
        expected = 'error: argument -S/--schedule-file: expected one argument'
        sys.argv = [mainfile, '--file', filename, '--schedule-file']
        try:
            ArgHandler.getArgs()
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testPreviewFileShortOption(self):
        """should set parse args 'schedule-file' var"""
        sys.argv = [mainfile, '-f', filename, '-p', filename]
        args = ArgHandler.getArgs()
        self.assertTrue(args.preview_file)

    def testPreviewFileLongOption(self):
        """should set parse args 'schedule-file' var"""
        sys.argv = [mainfile, '--file', filename, '--preview-file', filename]
        args = ArgHandler.getArgs()
        self.assertTrue(args.preview_file)

    def testPreviewFilenameRequiredWithPreviewOption(self):
        """should cause argparse error if sched file opt specified w/o file"""
        expected = 'error: argument -p/--preview-file: expected one argument'
        sys.argv = [mainfile, '--file', filename, '--preview-file']
        try:
            ArgHandler.getArgs()
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

if __name__ == "__main__":
    unittest.main()         # pragma: no cover
