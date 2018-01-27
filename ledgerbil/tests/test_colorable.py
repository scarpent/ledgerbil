import pytest

from ..colorable import Colorable, UnsupportedColorError


def test_len():
    """Colorable len should equal plain value len without ansi codes"""
    colorable = Colorable('red', 'glarg')
    assert len(colorable) == 5


def test_ansi_sequence_color_codes():
    """Color codes should equal expected start codes"""
    c = Colorable('white', None)
    for key, value in Colorable.COLORS.items():
        assert c.ansi_sequence(value) == f'\033[0;{value}m'


def test_ansi_sequence_bright_colors():
    """Bright color codes should equal expected start codes"""
    c = Colorable('white', None)
    for key, value in Colorable.COLORS.items():
        assert c.ansi_sequence(value, bright=True) == '\033[0;{}m'.format(
            value + c.BRIGHT_OFFSET
        )


def test_color():
    """Colorable ansi sequences should equal expected sequences"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 'blarg')
        assert str(c) == f'\x1b[0;{value}mblarg\x1b[0m'


def test_color_bright():
    """Colorable bright ansi sequences should equal expected sequences"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 'blarg', bright=True)
        assert str(c) == f'\x1b[0;{value + 60}mblarg\x1b[0m'


def test_color_colwidth_ten_as_string():
    """Colorable column width should pad appropriately"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 'blarg', fmt='10')
        assert str(c) == f'\x1b[0;{value}mblarg     \x1b[0m'


def test_color_colwidth_ten_as_number():
    """Colorable column width should pad appropriately"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 'blarg', fmt=10)
        assert str(c) == f'\x1b[0;{value}mblarg     \x1b[0m'


def test_color_colwidth_ten_right_adjusted():
    """Colorable column width right adjusted should pad appropriately"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 'blarg', fmt='>10')
        assert str(c) == f'\x1b[0;{value}m     blarg\x1b[0m'


def test_color_with_commas():
    """Colorable should add commas for thousands if specified in format"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 5000, fmt=',')
        assert str(c) == f'\x1b[0;{value}m5,000\x1b[0m'


def test_color_with_floats():
    """Colorable should apply float formatting if specified"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 5000.127, fmt='9.2f')
        assert str(c) == f'\x1b[0;{value}m  5000.13\x1b[0m'


def test_plain():
    """Plain should return string without ansi escape sequences"""
    c = Colorable('red', 'blah')
    assert str(c) == '\x1b[0;31mblah\x1b[0m'
    assert c.plain() == 'blah'


def test_get_plain_string():
    """get_plain_string should return string without ansi sequences"""
    assert Colorable.get_plain_string('\x1b[0;31mblah\x1b[0m') == 'blah'


def test_unsupported_color_error():
    """A color string that doesn't exist in COLORS dict should error"""
    with pytest.raises(UnsupportedColorError) as excinfo:
        Colorable('badcolor', None)
    expected = "I don't know what to do with this color: badcolor"
    assert str(excinfo.value) == expected
