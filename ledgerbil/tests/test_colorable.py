import pytest

from ..colorable import Colorable, UnsupportedColorError


def test_init_default():
    colorable = Colorable()
    assert colorable.my_color == 'white'
    assert colorable.text == ''
    assert colorable.column_width == 1
    assert colorable.right_adjust is False
    assert colorable.bright is False


def test_default_str():
    """Colorable default string should be ansi white"""
    colorable = Colorable()
    assert str(colorable) == '\x1b[0;37m \x1b[0m'


def test_len():
    """Colorable len should equal plain text len  without ansi codes"""
    colorable = Colorable('red', 'glarg')
    assert len(colorable) == 5


def test_ansi_sequence_color_codes():
    """Color codes should equal expected start codes"""
    c = Colorable()
    for key, value in Colorable.COLORS.items():
        assert c.ansi_sequence(value) == '\033[0;{}m'.format(value)


def test_ansi_sequence_bright_colors():
    """Bright color codes should equal expected start codes"""
    c = Colorable()
    for key, value in Colorable.COLORS.items():
        assert c.ansi_sequence(value, bright=True) == '\033[0;{}m'.format(
            value + c.BRIGHT_OFFSET
        )


def test_color():
    """Colorable ansi sequences should equal expected sequences"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 'blarg')
        assert str(c) == '\x1b[0;{}mblarg\x1b[0m'.format(value)


def test_color_bright():
    """Colorable bright ansi sequences should equal expected sequences"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 'blarg', bright=True)
        assert str(c) == '\x1b[0;{}mblarg\x1b[0m'.format(value + 60)


def test_color_column_width_ten():
    """Colorable column width should pad appropriately"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 'blarg', column_width=10)
        assert str(c) == '\x1b[0;{}mblarg     \x1b[0m'.format(value)


def test_color_column_width_ten_right_adjusted():
    """Colorable column width right adjusted should pad appropriately"""
    for key, value in Colorable.COLORS.items():
        c = Colorable(key, 'blarg', column_width=10, right_adjust=True)
        assert str(c) == '\x1b[0;{}m     blarg\x1b[0m'.format(value)


def test_plain():
    """Plain should return text without ansi escape sequences"""
    c = Colorable('red', 'blah')
    assert str(c) == '\x1b[0;31mblah\x1b[0m'
    assert c.plain() == 'blah'


def test_get_plain_text():
    """get_plain_text should return text without ansi sequences"""
    assert Colorable.get_plain_text('\x1b[0;31mblah\x1b[0m') == 'blah'


def test_unsupported_color_error():
    """A color string that doesn't exist in COLORS dict should error"""
    with pytest.raises(UnsupportedColorError) as excinfo:
        Colorable('badcolor')
    expected = "I don't know what to do with this color: badcolor"
    assert str(excinfo.value) == expected
