#!/usr/bin/env python3

import re


class Colorable(object):

    START_CODE = '\033'
    END_CODE = '{}[0m'.format(START_CODE)

    BRIGHT_OFFSET = 60

    COLORS = {
        'black': 30,
        'gray': 30,
        'grey': 30,
        'red': 31,
        'green': 32,
        'yellow': 33,
        'blue': 34,
        'magenta': 35,
        'purple': 35,
        'cyan': 36,
        'white': 37
    }

    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

    def __init__(self,
                 color='white',
                 text='',
                 column_width=1,
                 right_adjust=False,
                 bright=False):

        try:
            self.COLORS[color]
        except KeyError:
            raise UnsupportedColorError(
                "I don't know what to do with this color: {}".format(color)
            )

        self.my_color = color
        self.text = text
        self.column_width = column_width
        self.right_adjust = right_adjust
        self.bright = bright

    def __str__(self):
        adjust = '>' if self.right_adjust else ''

        ansi_str = '{start}{text:{adjust}{width}}{end}'.format(
            width=self.column_width,
            start=self.ansi_sequence(
                self.COLORS[self.my_color],
                bright=self.bright
            ),
            text=self.text,
            adjust=adjust,
            end=self.END_CODE
        )

        return ansi_str

    def __len__(self):
        return len(self.text)

    def ansi_sequence(self, code, bright=False):
        offset = 60 if bright else 0
        return '{start}[0;{color}m'.format(
            start=self.START_CODE,
            color=code + offset
        )

    def plain(self):
        return self.text

    @staticmethod
    def get_plain_text(ansi_text):
        return Colorable.ansi_escape.sub('', ansi_text)


class UnsupportedColorError(Exception):
    pass
