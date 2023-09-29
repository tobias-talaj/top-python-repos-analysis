import ast
import argparse
from typing import List, Dict, Tuple, Set
from functools import partial
from multiprocessing import Pool
from collections import defaultdict, Counter

from src.utils import find_python_files, save_dict_as_parquet, load_library_reference


def get_imported_modules(tree: ast.AST, max_depth: int = 2) -> Tuple[Set[str], Dict[str, str]]:
    """
    Traverses the AST up to a maximum depth and identifies all import statements, returning a set of imported module names and directly imported components.

    Parameters:
    tree: The root of the Abstract Syntax Tree (AST).
    max_depth: The maximum depth to traverse in the AST.

    Returns:
    A tuple containing:
    - A set of strings, each string being the name of an imported module.
    - A dictionary mapping directly imported component names to their module names.
    """
    imported_modules = set()
    direct_imports = defaultdict(set)

    def walk_tree(node, depth=0):
        if max_depth is not None and depth > max_depth:
            return

        match node:
            case ast.Import(names=names):
                imported_modules.update(n.name for n in names)
            case ast.ImportFrom(module=module_name, names=names, level=0):
                imported_modules.add(module_name)
                direct_imports[module_name].update(n.name for n in names)

        for child in ast.iter_child_nodes(node):
            walk_tree(child, depth + 1)

    walk_tree(tree)
    return imported_modules, direct_imports


def check_node(node: ast.AST, components: Dict[str, List[str]], component_counter: Counter, code_file: str, module: str, module_direct_imports: Dict[str, str]) -> None:
    """
    Checks if the node represents any of the library components (functions, methods, classes instatiations, attributes and exceptions).
    If it does, the component's count in component_counter is incremented.
    The function operates in place, i.e., it modifies the component_counter argument directly and does not return anything.

    Parameters:
    node: The AST node to check.
    components: A dict containing API reference of given library.
    component_counter: A Counter object for storing counts of library components.
    code_file: The path to the Python file being processed.
    module: The name of the library which components are being checked.
    module_direct_imports: A dictionary mapping directly imported component names to their module names (from foo import bar -> {'foo': ['bar']}).

    Returns:
    None
    """
    match node:
        case ast.Call(func=ast.Name(id=func_name)) if func_name in components["function"] and func_name in module_direct_imports:
            component_counter[(code_file, module, "function", func_name)] += 1
        case ast.Call(func=ast.Attribute(attr=func_name, value=ast.Name(id=module_name))) if func_name in components["function"] and module_name == module:
            component_counter[(code_file, module, "function", func_name)] += 1
        case ast.Call(args=[ast.Name(id=func_name)]) | ast.Call(args=[ast.Name(id=func_name), _]) | ast.Call(args=[_, ast.Name(id=func_name)]) if func_name in components["function"] and func_name in module_direct_imports:
            component_counter[(code_file, module, "function", func_name)] += 1
        case ast.Call(args=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(args=[_, ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(args=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name), _]) if func_name in components["function"] and module_name == module:
            component_counter[(code_file, module, "function", func_name)] += 1
        case ast.Call(keywords=[ast.keyword(value=ast.Name(id=func_name))]) | ast.Call(keywords=[ast.keyword(value=ast.Name(id=func_name)), _]) | ast.Call(keywords=[_, ast.keyword(value=ast.Name(id=func_name))]) if func_name in components["function"] and func_name in module_direct_imports:
            component_counter[(code_file, module, "function", func_name)] += 1
        case ast.Call(keywords=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(keywords=[_, ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(keywords=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name), _]) if func_name in components["function"] and module_name == module:
            component_counter[(code_file, module, "function", func_name)] += 1

        case ast.Call(func=ast.Attribute(attr=method_name)) if method_name in components["method"]:
            component_counter[(code_file, module, "method", method_name)] += 1

        case ast.Call(func=ast.Name(id=class_name)) if class_name in components["class"] and class_name in module_direct_imports:
            component_counter[(code_file, module, "class", class_name)] += 1
        case ast.Call(func=ast.Attribute(value=ast.Name(id=module_name), attr=class_name)) if class_name in components["class"] and module_name == module:
            component_counter[(code_file, module, "class", class_name)] += 1

        case ast.Attribute(attr=attr_name) if attr_name in components["attribute"]:
            component_counter[(code_file, module, "attribute", attr_name)] += 1

        case ast.ExceptHandler(type=ast.Name(id=exc_name)) if exc_name in components["exception"] and exc_name in module_direct_imports:
            component_counter[(code_file, module, "exception", exc_name)] += 1
        case ast.ExceptHandler(type=ast.Attribute(value=ast.Name(id=module_name), attr=exc_name)) if exc_name in components["exception"] and module_name == module:
            component_counter[(code_file, module, "exception", exc_name)] += 1
        case ast.Raise(exc=ast.Name(id=exc_name)) if exc_name in components["exception"] and exc_name in module_direct_imports:
            component_counter[(code_file, module, "exception", exc_name)] += 1
        case ast.Raise(exc=ast.Attribute(value=ast.Name(id=module_name), attr=exc_name)) if exc_name in components["exception"] and module_name == module:
            component_counter[(code_file, module, "exception", exc_name)] += 1


def process_file(lib_dict: Dict, code_file: str) -> Dict:
    """
    Process a single file, returning counts of library components.

    Parameters:
    lib_dict: A dictionary representing API reference of one or more libraries.
    code_file: The path to the file to process.

    Returns:
    A Counter object containing counts of library/libraries components within given code_file.
    """
    component_counter = Counter()
    try:
        with open(code_file, "r") as f:
            code = f.read()
    except IOError as e:
        print(f"Error reading file {code_file}: {e}")
        return Counter()

    try:
        tree = ast.parse(code)
        imported_modules, direct_imports = get_imported_modules(tree)

        for node in ast.walk(tree):
            for module, components in lib_dict.items():
                if module not in imported_modules:
                    continue
                check_node(node, components, component_counter, code_file, module, direct_imports[module])
        return component_counter
    except SyntaxError as e:
        print(f"Syntax error parsing file {code_file}: {e}")
        return Counter()


def count_lib_components(lib_dict: Dict, code_files: List[str]) -> Dict:
    """
    Count the occurrences of library components in a list of Python files.

    This function applies the `process_file` function to each file in `code_files` in parallel,
    using a pool of worker processes. Each `process_file` call returns a Counter object with counts
    of library components for that file. These Counters are then merged into a single Counter,
    which is returned.

    Parameters:
    lib_dict: A dict representing the library. The keys are module names and the values are dicts
              that group library components by type (e.g., 'function', 'class', etc.).
    code_files: A list of paths to Python code files.

    Returns:
    A Counter object containing counts of library components across all files.

    Raises:
    An exception may be raised if there's an error reading a file or parsing the Python code.
    """
    process_file_partial = partial(process_file, lib_dict)
    with Pool() as pool:
        all_files_components_counts = pool.map(process_file_partial, code_files)
    component_counter = Counter()
    for code_file_counts in all_files_components_counts:
        component_counter += code_file_counts
    return component_counter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--library_pickle_path", default="./api_reference_pickles/standard_library.pickle")
    parser.add_argument("--output_parquet_path", default="./data/py_component_counter.parquet")
    parser.add_argument("--input_python_files_path", default="/workspaces/repos/shared/python_repos")
    args = parser.parse_args()

    lib_dict = load_library_reference(args.library_pickle_path)
    code_files = find_python_files(args.input_python_files_path, dir_range=(0, 50))
    component_counts = count_lib_components(lib_dict, code_files)
    save_dict_as_parquet(component_counts, args.output_parquet_path)


if __name__ == "__main__":
    main()
