import argparse
import re
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta

from ..colorable import Colorable
from .settings import Settings

# This appears to work for mutual funds, and not indivudal stocks.

quote_url = 'https://finance.google.com/finance?q={}&output=json'

field_regex_pattern = r'"{}"\s*:\s*"([^"]+)"'
price_field_regex = re.compile(field_regex_pattern.format('nav_prior'))
date_field_regex = re.compile(field_regex_pattern.format('nav_time'))

date_regex_pattern = r'([A-Za-z]+)\s*([0-9]+),'
date_parts_regex = re.compile(date_regex_pattern)

settings = Settings()


def get_prices(price_file=None):

    for symbol in settings.SYMBOLS:
        the_date, the_price = get_quote_data(symbol)
        if the_date is None:
            continue

        print('{date} {symbol}   ${price}'.format(
            date=Colorable('blue', the_date, column_width=12, bright=True),
            symbol=Colorable('purple', symbol, column_width=8),
            price=the_price
        ))

        if price_file:
            with open(price_file, 'a') as the_file:
                the_file.write(settings.PRICE_FILE_FORMAT.format(
                    date=the_date,
                    symbol=symbol,
                    price=the_price
                ))


def get_quote_data(symbol):
    response = requests.get(quote_url.format(symbol))

    if response.status_code == 200:
        try:
            data = response.content.decode('unicode_escape')
            the_price = regex_search(data, price_field_regex, 'price')
            the_date = regex_search(data, date_field_regex, 'date')

            return get_date(the_date), the_price

        except Exception as e:
            print('Error loading {}: {}'.format(symbol, e))
    else:
        print('Error downloading {symbol}. Received code {code}.'.format(
            symbol=symbol,
            code=response.status_code
        ))

    return None, None


def regex_search(data, regex, label):
    match = regex.search(data)
    if match:
        return match.groups()[0]
    else:
        raise Exception("Couldn't find {}.".format(label))


def get_date(quote_date):
    date_parts_match = date_parts_regex.search(quote_date)
    if not date_parts_match:
        raise Exception("Couldn't parse date parts for {}.".format(quote_date))

    the_date = datetime.strptime(
        '{} {} {}'.format(
            date_parts_match.groups()[0],
            date_parts_match.groups()[1],
            datetime.now().strftime('%Y')
        ),
        '%b %d %Y'
    ) + relativedelta(days=1)

    return the_date.strftime('%Y/%m/%d')


def get_args(args=[]):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-f', '--file',
        type=str,
        help='save to this prices db file',
    )
    return parser.parse_args(args)


def main(argv=[]):
    args = get_args(argv)
    get_prices(args.file)
