import os
import ast
from typing import List, Dict
from functools import partial
from multiprocessing import Pool
from collections import defaultdict, Counter

from utils import find_python_files, save_dict_as_parquet, load_library_reference


def get_imported_modules(tree, max_depth=2):
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
            walk_tree(child, depth+1)

    walk_tree(tree)
    return imported_modules, direct_imports


def check_node(node, components, component_counter, code_file, module, module_direct_imports):
    match node:
        case ast.Call(func=ast.Name(id=func_name)) if func_name in components['function'] and func_name in module_direct_imports:
            component_counter[(code_file, module, 'function', func_name)] += 1
        case ast.Call(func=ast.Attribute(attr=func_name, value=ast.Name(id=module_name))) if func_name in components['function'] and module_name == module:
            component_counter[(code_file, module, 'function', func_name)] += 1
        case ast.Call(args=[ast.Name(id=func_name)]) | ast.Call(args=[ast.Name(id=func_name), _]) | ast.Call(args=[_, ast.Name(id=func_name)]) if func_name in components['function'] and func_name in module_direct_imports:
            component_counter[(code_file, module, 'function', func_name)] += 1
        case ast.Call(args=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(args=[_, ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(args=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name), _]) if func_name in components['function'] and module_name == module:
            component_counter[(code_file, module, 'function', func_name)] += 1
        case ast.Call(keywords=[ast.keyword(value=ast.Name(id=func_name))]) | ast.Call(keywords=[ast.keyword(value=ast.Name(id=func_name)), _]) | ast.Call(keywords=[_, ast.keyword(value=ast.Name(id=func_name))]) if func_name in components['function'] and func_name in module_direct_imports:
            component_counter[(code_file, module, 'function', func_name)] += 1
        case ast.Call(keywords=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(keywords=[_, ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(keywords=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name), _]) if func_name in components['function'] and module_name == module:
            component_counter[(code_file, module, 'function', func_name)] += 1

        case ast.Call(func=ast.Attribute(attr=method_name)) if method_name in components['method']:
            component_counter[(code_file, module, 'method', method_name)] += 1

        case ast.Call(func=ast.Name(id=class_name)) if class_name in components['class'] and class_name in module_direct_imports:
            component_counter[(code_file, module, 'class', class_name)] += 1
        case ast.Call(func=ast.Attribute(value=ast.Name(id=module_name), attr=class_name)) if class_name in components['class'] and module_name == module:
            component_counter[(code_file, module, 'class', class_name)] += 1

        case ast.Attribute(attr=attr_name) if attr_name in components['attribute']:
            component_counter[(code_file, module, 'attribute', attr_name)] += 1

        case ast.ExceptHandler(type=ast.Name(id=exc_name)) if exc_name in components['exception'] and exc_name in module_direct_imports:
            component_counter[(code_file, module, 'exception', exc_name)] += 1
        case ast.ExceptHandler(type=ast.Attribute(value=ast.Name(id=module_name), attr=exc_name)) if exc_name in components['exception'] and module_name == module:
            component_counter[(code_file, module, 'exception', exc_name)] += 1
        case ast.Raise(exc=ast.Name(id=exc_name)) if exc_name in components['exception'] and exc_name in module_direct_imports:
            component_counter[(code_file, module, 'exception', exc_name)] += 1
        case ast.Raise(exc=ast.Attribute(value=ast.Name(id=module_name), attr=exc_name)) if exc_name in components['exception'] and module_name == module:
            component_counter[(code_file, module, 'exception', exc_name)] += 1


def process_file(lib_dict: Dict, code_file: str) -> Dict:
    component_counter = Counter()
    with open(code_file, 'r') as f:
        code = f.read()
    try:
        tree = ast.parse(code)
        imported_modules, direct_imports = get_imported_modules(tree)

        is_nested = isinstance(next(iter(lib_dict.values())), dict)

        for node in ast.walk(tree):
            if is_nested:
                for module, components in lib_dict.items():
                    if module not in imported_modules:
                        continue
                    check_node(node, components, component_counter, code_file, module, direct_imports[module])
            # else:
            #     components = lib_dict
            #     for module in imported_modules:
            #         check_node(node, components, component_counter[code_file], module)
        return component_counter
    except SyntaxError as e:
        print(f"{e}: {code_file}")
        return Counter()


def count_lib_components(lib_dict: Dict, code_files: List[str]) -> Dict:
    process_file_partial = partial(process_file, lib_dict)
    with Pool() as pool:
        all_files_components_counts = pool.map(process_file_partial, code_files)
    component_counter = Counter()
    for code_file_counts in all_files_components_counts:
        component_counter += code_file_counts
    return component_counter


def main():
    library_pickle_path = '/workspaces/repos/top-python-repos-analysis/api_reference_pickles/standard_library.pickle'
    output_parquet_path = '/workspaces/repos/top-python-repos-analysis/data/component_counter.parquet'
    input_python_files_path = '/workspaces/repos/shared/python_repos'

    lib_dict = load_library_reference(library_pickle_path)
    code_files = find_python_files(input_python_files_path, dir_range=(0, 10))
    component_counts = count_lib_components(lib_dict, code_files)
    save_dict_as_parquet(component_counts, output_parquet_path)


if __name__ == '__main__':
    import time
    start = time.time()
    main()
    end = time.time()
    print(f"Time: {end - start}")
