from datetime import datetime
from unittest import mock

import pytest

from .. import prices

response_json = b'''
// [
{
"id": "239847258483691",
"t" : "POMIX",
"e" : "MUTF",
"name" : "T. Rowe Price Total Equity Market Index Fund"
, "nav_prior" : "30.13"
, "nav_c" : "-0.16"
, "nav_cp" : "-0.53"
, "nav_time" : "Feb 1, 7:00PM EST"
, "return_ytd" : "20.80"
, "yield_percent" : "1.34"
, "net_assets" : "1,715,021,764.00"
, "expense_ratio" : "0.30"
, "morningstar_rating" : "4"
, "summary" : "..."
<snipped>
'''


class MockSettings:
    PRICES_FILE = 'default_prices.blah'
    SYMBOLS = ['fu', 'bar']
    PRICE_FILE_FORMAT = 'P {date} {symbol:10} ${price}\n'


def setup_function(module):
    prices.settings = MockSettings()


@mock.patch(__name__ + '.prices.datetime')
@mock.patch(__name__ + '.prices.requests.get')
def test_get_quote_data(mock_response, mock_datetime):
    mock_datetime.now.return_value = datetime(2012, 2, 1)
    mock_datetime.strptime.return_value = datetime(2012, 2, 1)
    mock_response.return_value.status_code = 200
    mock_response.return_value.content = response_json
    the_date, the_price = prices.get_quote_data('fubar')
    assert (the_date, the_price) == ('2012/02/02', '30.13')


@mock.patch(__name__ + '.prices.print')
@mock.patch(__name__ + '.prices.requests.get')
def test_get_quote_data_regex_mismatch_date(mock_response, mock_print):
    mock_response.return_value.status_code = 200
    mock_response.return_value.content = b', "nav_time" : "Dec 28, 7:00PM EST"'
    the_date, the_price = prices.get_quote_data('fubar')
    expected = "Error loading fubar: Couldn't find price."
    mock_print.assert_called_once_with(expected)


@mock.patch(__name__ + '.prices.print')
@mock.patch(__name__ + '.prices.requests.get')
def test_get_quote_data_regex_mismatch_price(mock_response, mock_print):
    mock_response.return_value.status_code = 200
    mock_response.return_value.content = b', "nav_prior" : "30.13"'
    the_date, the_price = prices.get_quote_data('fubar')
    expected = "Error loading fubar: Couldn't find date."
    mock_print.assert_called_once_with(expected)


@mock.patch(__name__ + '.prices.print')
@mock.patch(__name__ + '.prices.requests.get')
def test_get_quote_data_status_code_error(mock_response, mock_print):
    mock_response.return_value.status_code = 400
    the_date, the_price = prices.get_quote_data('fubar')
    expected = 'Error downloading fubar. Received code 400.'
    mock_print.assert_called_once_with(expected)


def test_get_date_regex_mismatch():
    with pytest.raises(Exception) as excinfo:
        prices.get_date('zargle')
    expected = "Couldn't parse date parts for zargle."
    assert str(excinfo.value) == expected


@mock.patch(__name__ + '.prices.datetime')
def test_get_date(mock_datetime):
    mock_datetime.now.return_value = datetime(2015, 5, 5)
    mock_datetime.strptime.return_value = datetime(2015, 5, 5)
    assert prices.get_date('May 5,') == '2015/05/06'


@mock.patch(__name__ + '.prices.print')
@mock.patch(__name__ + '.prices.get_quote_data')
def test_get_prices_without_file(mock_quote_data, mock_print):
    mock_quote_data.side_effect = [
        ('2011/12/13', '67.89'),
        ('2009/10/11', '123.45')
    ]
    prices.get_prices()
    expected_first = '2011/12/13   fu         $67.89'
    expected_second = '2009/10/11   bar        $123.45'

    assert prices.Colorable.get_plain_string(
        mock_print.mock_calls[0][1][0]
    ) == expected_first

    assert prices.Colorable.get_plain_string(
        mock_print.mock_calls[1][1][0]
    ) == expected_second

    assert len(mock_print.mock_calls) == 2


@mock.patch(__name__ + '.prices.print')
@mock.patch(__name__ + '.prices.get_quote_data')
def test_get_prices_with_bad_data(mock_quote_data, mock_print):
    mock_quote_data.side_effect = [
        (None, None),
        ('2009/10/11', '123.45')
    ]
    prices.get_prices()
    expected = '2009/10/11   bar        $123.45'

    assert prices.Colorable.get_plain_string(
        mock_print.mock_calls[0][1][0]
    ) == expected

    assert len(mock_print.mock_calls) == 1


@mock.patch(__name__ + '.prices.print')
@mock.patch(__name__ + '.prices.get_quote_data')
def test_get_prices_with_file(mock_quote_data, mock_print):
    mock_quote_data.side_effect = [
        ('2011/12/13', '67.89'),
        ('2009/10/11', '123.45')
    ]
    expected_opens = [
        (('dummy_prices.db', 'a'), ),
        (('dummy_prices.db', 'a'), ),
    ]
    expected_writes = [
        (('P 2011/12/13 fu         $67.89\n', ), ),
        (('P 2009/10/11 bar        $123.45\n', ), ),
    ]
    m = mock.mock_open()
    with mock.patch(__name__ + '.prices.open', m):
        prices.get_prices(price_file='dummy_prices.db')
    assert m.call_args_list == expected_opens
    handle = m()
    assert handle.write.call_args_list == expected_writes
    assert mock_print.called


@mock.patch(__name__ + '.prices.get_prices')
def test_main_no_params(mock_get_prices):
    prices.main()
    mock_get_prices.assert_called_once_with(None)


@mock.patch(__name__ + '.prices.get_prices')
def test_main_with_file(mock_get_prices):
    prices.main(['--file', 'blah.db'])
    mock_get_prices.assert_called_once_with('blah.db')


@mock.patch(__name__ + '.prices.get_prices')
def test_main_with_save(mock_get_prices):
    prices.main(['--save'])
    mock_get_prices.assert_called_once_with('default_prices.blah')


@pytest.mark.parametrize('test_input, expected', [
    (['-f', 'blah'], 'blah'),
    (['--file', 'glarg'], 'glarg'),
    ([], None),
])
def test_args_prices(test_input, expected):
    args = prices.get_args(test_input)
    assert args.file == expected


@pytest.mark.parametrize('test_input, expected', [
    (['-s'], True),
    (['--save'], True),
    ([], False),
])
def test_args_save(test_input, expected):
    args = prices.get_args(test_input)
    assert args.save is expected
