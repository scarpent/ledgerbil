import os
import sys
from unittest import mock

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + "/../.."))

import main  # noqa


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


@mock.patch('main.portfolio.main')
def test_main_portfolio(mock_portfolio_main):
    main.main(['port'])
    mock_portfolio_main.assert_called_once_with([])
    main.main(['portfolio', '-a', 'argh'])
    mock_portfolio_main.assert_called_with(['-a', 'argh'])


@mock.patch('main.prices.main')
def test_main_prices(mock_prices_main):
    main.main(['prices'])
    mock_prices_main.assert_called_once_with([])
    main.main(['prices', '-f', 'blah'])
    mock_prices_main.assert_called_with(['-f', 'blah'])
