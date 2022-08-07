from jinja2 import Template

specifications = [
    ["Join", "iterable", "Str", False],
    ["Partition", "sep", "Tuple", False],
    ["Rpartition", "sep", "Tuple", False],
    ["Strip2Base", "chars", "Str", True],
]


def main():
    with open(
        "nuitka/tools/specialize/templates_python/StrNodes.py.j2"
    ) as template_file:
        template = Template(template_file.read())

    with open("StrNodes.py", "w", encoding="utf-8") as output_python:
        code = template.render(specifications=specifications)
        output_python.write(code)


main()
