""" Unit Test Helpers

Redirector: Capture streams

OutputFileTesterStdout: Redirect standard out to file for easier diffing
                        and maintenance of expected results. Generate
                        and look for files in a standard location with
                        standard suffixes.
"""

import filecmp
import os
import sys
from io import StringIO
from unittest import TestCase

from ..colorable import Colorable
from . import filetester as FT


class OutputFileTesterBase:
    OUT_SUFFIX = ".out"
    EXPECTED_SUFFIX = f"{OUT_SUFFIX}_expected"

    def get_filename(self, testfile, suffix):
        testfile = os.path.join(FT.testdir, testfile)
        return f"{testfile}{suffix}"

    def get_expected_filename(self, testfile):
        return self.get_filename(testfile, self.EXPECTED_SUFFIX)

    def get_out_filename(self, testfile):
        return self.get_filename(testfile, self.OUT_SUFFIX)

    @staticmethod
    def remove_color(text):
        return Colorable.get_plain_string(text)


class OutputFileTester(OutputFileTesterBase):
    def __init__(self, testfile):
        super().__init__()
        self.testfile = testfile

    def save_out_file(self, data):
        with open(self.get_out_filename(self.testfile), "w", encoding="utf-8") as afile:
            afile.write(self.remove_color(data))

    def assert_out_equals_expected(self):
        assert filecmp.cmp(
            self.get_out_filename(self.testfile),
            self.get_expected_filename(self.testfile),
        ), f"test filename out: {self.get_out_filename(self.testfile)}"


class OutputFileTesterStdout(TestCase, OutputFileTesterBase):
    def setUp(self):
        self.savestdout = sys.stdout

    def tearDown(self):
        sys.stdout = self.savestdout

    def init_test(self, testfile):
        testfile = os.path.join(FT.testdir, testfile)
        self.testfile = testfile
        self.expected = self.get_expected_filename(testfile)
        self.actual = self.get_out_filename(testfile)
        sys.stdout = open(self.actual, "w", encoding="utf-8")

    def conclude_test(self):
        sys.stdout.close()
        with open(self.actual, "r+", encoding="utf-8") as f:
            data = self.remove_color(f.read())
            f.seek(0)
            f.write(data)
            f.truncate()
        error = f"test filename root: {self.testfile}"
        assert filecmp.cmp(self.expected, self.actual), error


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
