import os
import sys
from unittest import mock

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + "/../.."))

import main  # isort:skip # noqa: has to follow sys path hack


@mock.patch('main.ledgerbil.main')
def test_main_ledgerbil(mock_ledgerbil_main):
    main.main([])
    mock_ledgerbil_main.assert_called_once_with([])
    main.main(['-r', 'blah', '-f', 'fubar'])
    mock_ledgerbil_main.assert_called_with(['-r', 'blah', '-f', 'fubar'])


@mock.patch('main.grid.main')
def test_main_grid(mock_grid_main):
    main.main(['grid'])
    mock_grid_main.assert_called_once_with([])
    main.main(['grid', '-a', 'blah'])
    mock_grid_main.assert_called_with(['-a', 'blah'])


@mock.patch('main.investments.main')
def test_main_investments_with_argv_none(mock_investments_main):
    with mock.patch('sys.argv', ['/script', 'inv']):
        main.main()
    mock_investments_main.assert_called_once_with([])


@mock.patch('main.investments.main')
def test_main_investments(mock_investments_main):
    main.main(['inv'])
    mock_investments_main.assert_called_once_with([])
    main.main(['investments', '-a', 'blah', '-e', 'fubar'])
    mock_investments_main.assert_called_with(['-a', 'blah', '-e', 'fubar'])


@mock.patch('main.passthrough.main')
def test_main_passthrough(mock_passthrough_main):
    main.main(['pass'])
    mock_passthrough_main.assert_called_once_with([])
    main.main(['pass', 'argle', 'bargle'])
    mock_passthrough_main.assert_called_with(['argle', 'bargle'])


@mock.patch('main.portfolio.main')
def test_main_portfolio(mock_portfolio_main):
    main.main(['port'])
    mock_portfolio_main.assert_called_once_with([])
    main.main(['portfolio', '-a', 'argh'])
    mock_portfolio_main.assert_called_with(['-a', 'argh'])
