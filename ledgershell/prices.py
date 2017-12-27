import argparse
import re
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta

from ledgerbil.colorable import Colorable

from .settings import Settings

# This appears to work for mutual funds, and not indivudal stocks.

quote_url = 'https://finance.google.com/finance?q={}&output=json'

field_regex_pattern = r'"{}"\s*:\s*"([^"]+)"'
price_field_regex = re.compile(field_regex_pattern.format('nav_prior'))
date_field_regex = re.compile(field_regex_pattern.format('nav_time'))

date_regex_pattern = r'([A-Za-z]+)\s*([0-9]+),'
date_parts_regex = re.compile(date_regex_pattern)

PRICE_FILE_FORMAT = 'P {date} {inv:10} ${price}\n'

s = Settings()


def download(price_file=None):

    for symbol in s.SYMBOLS:
        response = requests.get(quote_url.format(symbol))
        if response.status_code == 200:
            try:
                the_date, the_price = get_quote_data(response)
            except Exception as e:
                print('Error loading {}: {}'.format(symbol, e))
                continue
        else:
            print('Error downloading {symbol}. Received code {code}.'.format(
                symbol=symbol,
                code=response.status_code
            ))
            continue

        print('{date} {inv}   ${price}'.format(
            date=Colorable('blue', the_date, column_width=12, bright=True),
            inv=Colorable('purple', symbol, column_width=8),
            price=the_price
        ))

        if price_file:
            with open(price_file, 'a') as the_file:
                the_file.write(PRICE_FILE_FORMAT.format(
                    date=the_date,
                    inv=symbol,
                    price=the_price
                ))


def get_quote_data(response):
    data = response.content[6:-2].decode('unicode_escape')
    the_price = regex_search(data, price_field_regex, 'price')
    the_date = regex_search(data, date_field_regex, 'date')
    return get_date(the_date), the_price


def regex_search(data, regex, label):
    match = regex.search(data)
    if match:
        return match.groups()[0]
    else:
        raise Exception("Couldn't find {}.".format(label))


def get_date(quote_date):
    last_month_abbreviated = (
        datetime.now() + relativedelta(months=-1)
    ).strftime('%b')

    date_parts_match = date_parts_regex.search(quote_date)
    if date_parts_match:
        quote_month_abbreviated = date_parts_match.groups()[0]
        quote_day = date_parts_match.groups()[1]
    else:
        raise Exception("Couldn't parse date parts.")

    if (quote_month_abbreviated == last_month_abbreviated
            and last_month_abbreviated == 'Dec'):
        quote_year = (datetime.now() + relativedelta(years=-1)).strftime('%Y')
    else:
        quote_year = datetime.now().strftime('%Y')

    the_date = datetime.strptime(
        '{} {} {}'.format(quote_month_abbreviated, quote_day, quote_year),
        '%b %d %Y'
    ) + relativedelta(days=1)
    return the_date.strftime('%Y/%m/%d')


class ArgHandler(object):

    @staticmethod
    def get_args(args):
        parser = argparse.ArgumentParser()

        parser.add_argument(
            '-f', '--file',
            type=str,
            help='save to this prices db file',
        )
        return parser.parse_args(args)


def main(argv):
    args = ArgHandler.get_args(argv)
    download(args.file)
