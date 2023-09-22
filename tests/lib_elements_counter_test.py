import ast
import pytest

from src.lib_elements_counter import get_imported_modules


@pytest.mark.parametrize("code,expected", [
    ('import os', {'os'}),
    ('import os, sys', {'os', 'sys'}),
    ('import os as operating_system', {'os'}),
    ('from os import path', {'os'}),
    ('from os import path as os_path', {'os'}),
    ('from os import path, environ', {'os'}),
    ('import xml.etree.ElementTree', {'xml.etree.ElementTree'}),
    ('import xml.etree.ElementTree as elementtree', {'xml.etree.ElementTree'}),
    ('from xml.etree import ElementTree', {'xml.etree'}),
    ('print("Hello, world!")', set())
])

def test_get_imported_modules(code, expected):
    tree = ast.parse(code)
    assert get_imported_modules(tree) == expected
