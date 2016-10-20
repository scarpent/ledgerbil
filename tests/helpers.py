#!/usr/bin/python

""" Unit Test Helpers

Redirector: Capture streams

OutputFileTester: Redirect standard out to file for easier diffing and
                  maintenance of expected results. Generate and look for
                  files in a standard location with standard suffixes.
"""

import filecmp
import sys

from unittest import TestCase

# noinspection PyCompatibility
from StringIO import StringIO


class OutputFileTester(TestCase):

    TEST_FILES_DIR = 'tests/files/'
    OUT_SUFFIX = '.out'
    EXPECTED_SUFFIX = OUT_SUFFIX + '_expected'

    def setUp(self):
        self.savestdout = sys.stdout

    def tearDown(self):
        sys.stdout = self.savestdout

    def init_test(self, testfile):
        testfile = self.TEST_FILES_DIR + testfile
        self.expected = testfile + self.EXPECTED_SUFFIX
        self.actual = testfile + self.OUT_SUFFIX
        sys.stdout = open(self.actual, 'w')

    def conclude_test(self):
        sys.stdout.close()
        self.assertTrue(filecmp.cmp(self.expected, self.actual))


class Redirector(TestCase):

    def setUp(self):
        self.savestdout = sys.stdout
        self.reset_redirect()

        self.savestderr = sys.stderr
        self.redirecterr = StringIO()
        sys.stderr = self.redirecterr

    def tearDown(self):
        self.redirect.close()
        sys.stdout = self.savestdout

        self.redirecterr.close()
        sys.stderr = self.savestderr

    def reset_redirect(self):
        self.redirect = StringIO()
        sys.stdout = self.redirect
