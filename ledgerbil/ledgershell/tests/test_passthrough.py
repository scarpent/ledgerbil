from unittest import mock

import pytest

from .. import passthrough


@mock.patch(__name__ + '.passthrough.print')
@mock.patch(__name__ + '.passthrough.get_ledger_output')
def test_main(mock_ledger_output, mock_print):
    bill_the_cat_sayeth = 'ACKPHFT THBBFT!!'
    mock_ledger_output.return_value = bill_the_cat_sayeth
    expected = ('argle', 'bargle')
    passthrough.main(expected)
    mock_ledger_output.assert_called_once_with(expected)
    mock_print.assert_called_once_with(bill_the_cat_sayeth)


@mock.patch(__name__ + '.passthrough.print')
@mock.patch(__name__ + '.passthrough.get_ledger_command')
@mock.patch(__name__ + '.passthrough.get_ledger_output')
def test_main_with_command(mock_ledger_output, mock_ledger_cmd, mock_print):
    bill_the_cat_sayeth = 'ACKPHFT THBBFT!!'
    mock_ledger_output.return_value = bill_the_cat_sayeth
    mock_ledger_cmd.return_value = ['a', 'b']
    passthrough.main(['argle', 'bargle', '--command'])
    mock_ledger_cmd.assert_called_once_with(('argle', 'bargle'))
    mock_ledger_output.assert_called_once_with(('argle', 'bargle'))
    mock_print.assert_has_calls([
        mock.call('a b'),
        mock.call(bill_the_cat_sayeth)
    ])


@mock.patch(__name__ + '.passthrough.print')
@mock.patch(__name__ + '.passthrough.get_ledger_command')
@mock.patch(__name__ + '.passthrough.get_ledger_output')
def test_main_no_args(mock_ledger_output, mock_ledger_cmd, mock_print):
    passthrough.main(['--command'])
    mock_ledger_cmd.assert_not_called()
    mock_ledger_output.assert_not_called()
    mock_print.assert_not_called()


@pytest.mark.parametrize('test_input, expected', [
    (['--command'], True),
    ([], False),
])
def test_args_command(test_input, expected):
    args, _ = passthrough.get_args(test_input)
    assert args.command is expected
