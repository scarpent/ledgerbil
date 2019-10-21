from textwrap import dedent
from unittest import mock

import pytest

import yaml_tmlanguage_helper as ytl


@mock.patch(f"{__name__}.ytl.write_yaml_tmlanguage_file")
@mock.patch(f"{__name__}.ytl.print")
def test_do_the_things(mock_print, mock_write_yaml):
    input_data = dedent(
        """\
        ’Twas brillig, and the slithy toves
        # start variables
        # gyre gimble
        ## vorpal blade
        # mimsy borogoves
        # mome ({{gyre}}|outgrabe)

        # end variables
        # gyre snicker snack
        {{gyre}}-{{mimsy}}

        {{mome}}|{{gyre}}"""
    )
    expected_data = dedent(
        """\
        ’Twas brillig, and the slithy toves
        # start variables
        # gyre gimble
        ## vorpal blade
        # mimsy borogoves
        # mome ({{gyre}}|outgrabe)

        # end variables
        # gyre snicker snack
        gimble-borogoves

        (gimble|outgrabe)|gimble"""
    )

    with mock.patch(f"{__name__}.ytl.open", mock.mock_open(read_data=input_data)):
        ytl.do_the_things()

    mock_write_yaml.assert_called_once_with(expected_data)
    mock_print.assert_called_once_with("replaced 3 variables")


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("wabe", "Start"),
        ("wabe\n# start variables", "End"),
        ("wabe\n# start variables\n# shun", "End"),
        ("wabe\n# end variables", "Start"),
    ],
)
def test_do_the_things_marker_errors(test_input, expected):
    with mock.patch(f"{__name__}.ytl.open", mock.mock_open(read_data=test_input)):
        with pytest.raises(RuntimeError) as excinfo:
            ytl.do_the_things()
        assert str(excinfo.value) == f"{expected} marker not found"


def test_write_yaml_tmlanguage_file():
    m = mock.mock_open()
    with mock.patch(f"{__name__}.ytl.open", m):
        ytl.write_yaml_tmlanguage_file("And hast thou slain the Jabberwock?")
    m.assert_called_once_with("ledger.YAML-tmLanguage", "w")
    handle = m()
    handle.write.assert_called_once_with("And hast thou slain the Jabberwock?")


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("Jubjub", "Jubjub"),
        ("{{gyre}}", "gimble"),
        ("{{mimsy}}", "borogoves"),
        ("(vorpal|{{gyre}}|tumtum)", "(vorpal|gimble|tumtum)"),
    ],
)
def test_get_text_with_replacements(test_input, expected):
    variables = {"gyre": "gimble", "mimsy": "borogoves"}
    assert ytl.get_text_with_replacements(test_input, variables) == expected


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("name: Ledger", (None, None)),
        ("# regular comment", ("regular", "comment")),
        ("# start variables\n", ("start", "variables")),
        ("    # start variables      \n", ("start", "variables")),
        ("# end variables", ("end", "variables")),
        ("# start variables blarg\n", ("start", "variables blarg")),
        (
            "# name_terminator                   (?=  |\\t|$)",
            ("name_terminator", "(?=  |\\t|$)"),
        ),
        ("## not a var", (None, None)),
        ("# # also not a var", (None, None)),
    ],
)
def test_get_var_name_and_value(test_input, expected):
    assert ytl.get_var_name_and_value(test_input) == expected


@mock.patch(f"{__name__}.ytl.do_the_things")
def test_main(mock_do_it):
    ytl.main()
    mock_do_it.assert_called_once()
    ytl.main(["blarg"])
    assert mock_do_it.call_args_list == [mock.call(), mock.call()]
