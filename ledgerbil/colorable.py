import re


class Colorable:

    START_CODE = "\033"
    END_CODE = f"{START_CODE}[0m"

    BRIGHT_OFFSET = 60

    COLORS = {
        "black": 30,
        "gray": 30,
        "grey": 30,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "blue": 34,
        "magenta": 35,
        "purple": 35,
        "cyan": 36,
        "white": 37,
    }

    # https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python  # noqa E501
    # 7-bit C1 ANSI sequences
    ansi_escape = re.compile(
        r"""
        \x1B            # ESC
        (?:             # 7-bit C1 Fe (except CSI)
            [@-Z\\-_]
        |               # or [ for CSI, followed by a control sequence
            \[
            [0-?]*      # Parameter bytes
            [ -/]*      # Intermediate bytes
            [@-~]       # Final byte
        )""",
        re.VERBOSE,
    )

    def __init__(self, color, value, fmt="", bright=False):

        if color not in self.COLORS:
            raise UnsupportedColorError(
                f"I don't know what to do with this color: {color}"
            )

        self.my_color = color
        self.value = value
        self.bright = bright
        self.format_string = fmt

    def __repr__(self):
        return (
            f"Colorable('{self.my_color}', '{self.value}', "
            f"fmt='{self.format_string}', bright={self.bright})"
        )

    def __str__(self):
        start = self.ansi_sequence(self.COLORS[self.my_color], bright=self.bright)
        ansi_str = f"{start}{self.value:{self.format_string}}{self.END_CODE}"
        return ansi_str

    def __len__(self):
        return len(self.value)

    def __eq__(self, other):
        return str(self) == str(other)

    def ansi_sequence(self, code, bright=False):
        offset = 60 if bright else 0
        color = code + offset
        return f"{self.START_CODE}[0;{color}m"

    def plain(self):
        return self.value

    @staticmethod
    def get_plain_string(ansi_string):
        return Colorable.ansi_escape.sub("", ansi_string)


class UnsupportedColorError(Exception):
    pass
