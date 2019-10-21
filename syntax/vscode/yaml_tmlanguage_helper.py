import re
import sys

IN_FILE = "ledger-vars.YAML-tmLanguage"
OUT_FILE = "ledger.YAML-tmLanguage"


def do_the_things():
    out_file_data = ""
    variables = {}
    in_variables = False
    replacing = False
    with open(IN_FILE, "r") as file:
        for line in file:
            name, value = get_var_name_and_value(line)
            if replacing:
                out_file_data += get_text_with_replacements(line, variables)
            elif in_variables:
                out_file_data += line
                if (name, value) == ("end", "variables"):
                    replacing = True
                elif name and value:
                    # variables may contain other variables
                    variables[name] = get_text_with_replacements(value, variables)
            else:
                out_file_data += line
                if (name, value) == ("start", "variables"):
                    in_variables = True

    if not in_variables:
        raise RuntimeError("Start marker not found")
    elif not replacing:
        raise RuntimeError("End marker not found")

    write_yaml_tmlanguage_file(out_file_data)
    print(f"replaced {len(variables)} variables")


def write_yaml_tmlanguage_file(data):
    with open(OUT_FILE, "w") as file:
        file.write(data)


def get_text_with_replacements(text, variables):
    for placeholder, new_text in variables.items():
        text = text.replace("{{" + placeholder + "}}", new_text)
    return text


def get_var_name_and_value(line):
    m = re.match(r"^#\s*([^#\s]+)\s+(.*)$", line.strip())
    if m:
        name, value = m.groups()
        return name, value
    else:
        return None, None


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    do_the_things()


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
