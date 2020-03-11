from setuptools import setup

setup(
    name="nested_namespaces",
    version="1.0.0",
    description=(
        "bdist_nuitka test-case that verifies that Nuitka correctly handles"
        " nested implicit namespaces"
    ),
    packages=["a.b.pkg"],
    entry_points={"console_scripts": ["runner = a.b.pkg:main"]},
)
