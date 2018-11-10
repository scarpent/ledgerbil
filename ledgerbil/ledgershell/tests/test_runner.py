import os
from unittest import mock

import pytest

from .. import runner
from ... import settings, settings_getter


class MockSettings:
    LEDGER_COMMAND = ('ledger', )
    LEDGER_DIR = 'xyz'
    LEDGER_FILES = [
        'blarg.ldg',
        'glurg.ldg',
    ]


def setup_function():
    settings_getter.settings = MockSettings()


def teardown_function():
    settings_getter.settings = settings.Settings()


class MockProcess:
    def __init__(self, output=b'process output...', error=None):
        self.output = output
        self.error = error

        if not isinstance(output, bytes):
            raise TypeError('output must be type bytes')

    def communicate(self):
        return self.output, self.error


def test_get_ledger_command():
    file1 = os.path.join(MockSettings.LEDGER_DIR, 'blarg.ldg')
    file2 = os.path.join(MockSettings.LEDGER_DIR, 'glurg.ldg')
    expected = ('ledger', '-f', file1, '-f', file2)
    actual = runner.get_ledger_command()
    assert actual == expected


def test_get_ledger_command_with_options():
    file1 = os.path.join(MockSettings.LEDGER_DIR, 'blarg.ldg')
    file2 = os.path.join(MockSettings.LEDGER_DIR, 'glurg.ldg')
    expected = ('ledger', '-f', file1, '-f', file2, 'booga booga')
    actual = runner.get_ledger_command(('booga booga', ))
    assert actual == expected


def test_mock_process_object():
    process = MockProcess(output=b'fu')
    assert process.output == b'fu'
    assert process.error is None

    with pytest.raises(TypeError) as excinfo:
        MockProcess(output='a string')
    assert str(excinfo.value) == 'output must be type bytes'


@mock.patch(__name__ + '.runner.subprocess.Popen')
def test_get_ledger_output(mock_popen):
    mock_popen.return_value = MockProcess(output=b'blargle')
    output = runner.get_ledger_output()
    assert output == 'blargle'


@mock.patch(__name__ + '.runner.subprocess.Popen')
def test_get_ledger_output_with_options(mock_popen):
    mock_popen.return_value = MockProcess(output=b'blargle')
    output = runner.get_ledger_output(('--arghh', 'hooey'))
    assert output == 'blargle'


@mock.patch(__name__ + '.runner.subprocess.Popen')
def test_get_ledger_output_stripping(mock_popen):
    mock_popen.return_value = MockProcess(output=b'   fubar   ')
    output = runner.get_ledger_output(('--arghh', 'hooey'))
    assert output == '   fubar'
