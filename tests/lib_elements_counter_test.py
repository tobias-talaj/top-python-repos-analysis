import ast
import pytest
from collections import Counter
from typing import List, Dict

from src.lib_elements_counter import get_imported_modules, check_node


@pytest.mark.parametrize(
    "code,max_depth,expected",
    [
        ("import os", None, ({"os"}, {})),
        ("import os, sys", 2, ({"os", "sys"}, {})),
        ("import os as operating_system", 1, ({"os"}, {})),
        ("from os import path", None, ({"os"}, {"os": {"path"}})),
        ("from os import path as os_path", None, ({"os"}, {"os": {"path"}})),
        ("from os import path, environ", None, ({"os"}, {"os": {"path", "environ"}})),
        ("import xml.etree.ElementTree", None, ({"xml.etree.ElementTree"}, {})),
        ("import xml.etree.ElementTree as elementtree", None, ({"xml.etree.ElementTree"}, {})),
        ("from xml.etree import ElementTree", None, ({"xml.etree"}, {"xml.etree": {"ElementTree"}})),
        ('print("Hello, world!")', None, (set(), {})),
    ],
)
def test_get_imported_modules(code, max_depth, expected):
    tree = ast.parse(code)
    assert get_imported_modules(tree, max_depth) == expected


@pytest.fixture
def setup_data():
    components = {"math": {"function": ["sqrt", "pow"], "attribute": ["pi"], "method": [], "class": []}}
    component_counter = Counter()
    code_file = "test.py"
    module = "math"
    module_direct_imports = {"sqrt": "math", "pow": "math", "pi": "math"}

    yield components, component_counter, code_file, module, module_direct_imports


def test_check_node_import(setup_data):
    components, component_counter, code_file, module, module_direct_imports = setup_data
    node = ast.parse("import math").body[0]
    check_node(node, components, component_counter, code_file, module, module_direct_imports)
    assert component_counter == Counter()


def test_check_node_import_from(setup_data):
    components, component_counter, code_file, module, module_direct_imports = setup_data
    node = ast.parse("from math import sqrt").body[0]
    check_node(node, components, component_counter, code_file, module, module_direct_imports)
    assert component_counter == Counter()


def test_check_node_function_call(setup_data):
    components, component_counter, code_file, module, module_direct_imports = setup_data
    node = ast.parse("sqrt(9)").body[0].value
    check_node(node, components["math"], component_counter, code_file, module, module_direct_imports)


def test_check_node_attribute(setup_data):
    components, component_counter, code_file, module, module_direct_imports = setup_data
    node = ast.parse("math.pi").body[0].value
    check_node(node, components["math"], component_counter, code_file, module, module_direct_imports)


def test_check_node_alias(setup_data):
    components, component_counter, code_file, module, module_direct_imports = setup_data
    node = ast.parse("import math as m").body[0]
    module_direct_imports = {"m": "math"}
    node_call = ast.parse("m.sqrt(9)").body[0].value
    check_node(node_call, components["math"], component_counter, code_file, module, module_direct_imports)


def test_check_node_no_match(setup_data):
    components, component_counter, code_file, module, module_direct_imports = setup_data
    node = ast.parse('print("Hello, World!")').body[0].value
    check_node(node, components["math"], component_counter, code_file, module, module_direct_imports)
