""" Unit Test Helpers

Redirector: Capture streams

OutputFileTester: Redirect standard out to file for easier diffing and
                  maintenance of expected results. Generate and look for
                  files in a standard location with standard suffixes.
"""

import filecmp
import os
import re
import sys
from io import StringIO
from unittest import TestCase


class OutputFileTester(TestCase):

    path = os.path.dirname(__file__)
    TEST_FILES_DIR = os.path.join(path, 'files')
    OUT_SUFFIX = '.out'
    EXPECTED_SUFFIX = f'{OUT_SUFFIX}_expected'

    def setUp(self):
        self.savestdout = sys.stdout

    def tearDown(self):
        sys.stdout = self.savestdout

    def init_test(self, testfile):
        testfile = os.path.join(self.TEST_FILES_DIR, testfile)
        self.expected = f'{testfile}{self.EXPECTED_SUFFIX}'
        self.actual = f'{testfile}{self.OUT_SUFFIX}'
        sys.stdout = open(self.actual, 'w')

    def conclude_test(self, strip_ansi_color=False):
        sys.stdout.close()
        if strip_ansi_color:
            with open(self.actual, 'r+') as f:
                data = self.remove_color(f.read())
                f.seek(0)
                f.write(data)
                f.truncate()
        self.assertTrue(filecmp.cmp(self.expected, self.actual))

    @staticmethod
    def remove_color(text):
        # removes ansi color escape sequences
        return re.sub(r'(?:\x1b[^m]*m|\x0f)', '', text)


class Redirector(TestCase):

    def setUp(self):
        self.savestdout = sys.stdout
        self.reset_redirect()

        self.savestderr = sys.stderr
        self.reset_err_redirect()

    def tearDown(self):
        self.redirect.close()
        sys.stdout = self.savestdout

        self.redirecterr.close()
        sys.stderr = self.savestderr

    def reset_redirect(self):
        self.redirect = StringIO()
        sys.stdout = self.redirect

    def reset_err_redirect(self):
        self.redirecterr = StringIO()
        sys.stderr = self.redirecterr
