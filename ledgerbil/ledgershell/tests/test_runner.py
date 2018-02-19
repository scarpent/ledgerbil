import os
from unittest import mock

import pytest

from .. import runner


class TestSettings(object):
    LEDGER_COMMAND = 'ledger'
    LEDGER_DIR = 'xyz'
    LEDGER_FILES = [
        'blarg.ldg',
        'glurg.ldg',
    ]


class MockProcess(object):
    def __init__(self, output=b'process output...', error=None):
        self.output = output
        self.error = error

        if not isinstance(output, bytes):
            raise TypeError('output must be type bytes')

    def communicate(self):
        return self.output, self.error


def test_get_ledger_command():
    runner.settings = TestSettings()
    file1 = os.path.join(TestSettings.LEDGER_DIR, 'blarg.ldg')
    file2 = os.path.join(TestSettings.LEDGER_DIR, 'glurg.ldg')
    expected = ['ledger', '-f', file1, '-f', file2]
    actual = runner.get_ledger_command()
    assert actual == expected


def test_get_ledger_command_with_options():
    runner.settings = TestSettings()
    file1 = os.path.join(TestSettings.LEDGER_DIR, 'blarg.ldg')
    file2 = os.path.join(TestSettings.LEDGER_DIR, 'glurg.ldg')
    expected = ['ledger', '-f', file1, '-f', file2, 'booga booga']
    actual = runner.get_ledger_command(['booga booga'])
    assert actual == expected


def test_mock_process_object():
    with pytest.raises(TypeError) as excinfo:
        MockProcess(output='a string')
    assert str(excinfo.value) == 'output must be type bytes'


@mock.patch(__name__ + '.runner.subprocess.Popen')
def test_get_ledger_output(mock_popen):
    runner.settings = TestSettings()
    mock_popen.return_value = MockProcess(output=b'blargle')
    output = runner.get_ledger_output()
    assert output == 'blargle'


@mock.patch(__name__ + '.runner.subprocess.Popen')
def test_get_ledger_output_with_options(mock_popen):
    runner.settings = TestSettings()
    mock_popen.return_value = MockProcess(output=b'blargle')
    output = runner.get_ledger_output(['--arghh', 'hooey'])
    assert output == 'blargle'


@mock.patch(__name__ + '.runner.print')
@mock.patch(__name__ + '.runner.subprocess.Popen')
def test_get_ledger_output_error(mock_popen, mock_print):
    runner.settings = TestSettings()
    mock_popen.return_value = MockProcess(error='kaboom!')
    with pytest.raises(SystemExit):
        runner.get_ledger_output()
    mock_print.assert_called_once_with('kaboom!')
