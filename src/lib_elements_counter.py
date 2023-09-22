import os
import ast
import pickle
from typing import List, Dict
from collections import defaultdict

from utils import find_python_files, save_dict_as_parquet


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


def check_node(node, components, component_counter, module, module_direct_imports):
    match node:
        case ast.Call(func=ast.Name(id=func_name)) if func_name in components['function'] and func_name in module_direct_imports:
            component_counter[module]['function'][func_name] += 1
        case ast.Call(func=ast.Attribute(attr=func_name, value=ast.Name(id=module_name))) if func_name in components['function'] and module_name == module:
            component_counter[module]['function'][func_name] += 1
        case ast.Call(args=[ast.Name(id=func_name)]) | ast.Call(args=[ast.Name(id=func_name), _]) | ast.Call(args=[_, ast.Name(id=func_name)]) if func_name in components['function'] and func_name in module_direct_imports:
            component_counter[module]['function'][func_name] += 1
        case ast.Call(args=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(args=[_, ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(args=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name), _]) if func_name in components['function'] and module_name == module:
            component_counter[module]['function'][func_name] += 1
        case ast.Call(keywords=[ast.keyword(value=ast.Name(id=func_name))]) | ast.Call(keywords=[ast.keyword(value=ast.Name(id=func_name)), _]) | ast.Call(keywords=[_, ast.keyword(value=ast.Name(id=func_name))]) if func_name in components['function'] and func_name in module_direct_imports:
            component_counter[module]['function'][func_name] += 1
        case ast.Call(keywords=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(keywords=[_, ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(keywords=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name), _]) if func_name in components['function'] and module_name == module:
            component_counter[module]['function'][func_name] += 1

        case ast.Call(func=ast.Attribute(attr=method_name)) if method_name in components['method']:
            component_counter[module]['method'][method_name] += 1

        case ast.Call(func=ast.Name(id=class_name)) if class_name in components['class'] and class_name in module_direct_imports:
            component_counter[module]['class'][class_name] += 1
        case ast.Call(func=ast.Attribute(value=ast.Name(id=module_name), attr=class_name)) if class_name in components['class'] and module_name == module:
            component_counter[module]['class'][class_name] += 1

        case ast.Attribute(attr=attr_name) if attr_name in components['attribute']:
            component_counter[module]['attribute'][attr_name] += 1

        case ast.ExceptHandler(type=ast.Name(id=exc_name)) if exc_name in components['exception'] and exc_name in module_direct_imports:
            component_counter[module]['exception'][exc_name] += 1
        case ast.ExceptHandler(type=ast.Attribute(value=ast.Name(id=module_name), attr=exc_name)) if exc_name in components['exception'] and module_name == module:
            component_counter[module]['exception'][exc_name] += 1
        case ast.Raise(exc=ast.Name(id=exc_name)) if exc_name in components['exception'] and exc_name in module_direct_imports:
            component_counter[module]['exception'][exc_name] += 1
        case ast.Raise(exc=ast.Attribute(value=ast.Name(id=module_name), attr=exc_name)) if exc_name in components['exception'] and module_name == module:
            component_counter[module]['exception'][exc_name] += 1


def load_library_reference(pickle_path: str) -> Dict:
    with open(pickle_path, 'rb') as f:
        lib_dict = pickle.load(f)
    return lib_dict


def process_file(code_file: str, script_dir: str, lib_dict: Dict) -> Dict:
    component_counter = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    relative_path = os.path.relpath(code_file, script_dir)
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
                    check_node(node, components, component_counter[relative_path], module, direct_imports[module])
            # else:
            #     components = lib_dict
            #     for module in imported_modules:
            #         check_node(node, components, component_counter[code_file], module)
        return component_counter
    except SyntaxError as e:
        print(f"{e}: {relative_path}")
        return {}


def count_lib_components(pickle_path: str, code_files: List[str], script_dir: str) -> Dict:
    lib_dict = load_library_reference(pickle_path)
    component_counter = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))
    for code_file in code_files:
        file_component_counter = process_file(code_file, script_dir, lib_dict)
        component_counter.update(file_component_counter)
    return component_counter


if __name__ == '__main__':
    pickle_path = '/workspaces/repos/top-python-repos-analysis/api_reference_pickles/standard_library.pickle'
    parquet_path = '/workspaces/repos/top-python-repos-analysis/data/component_counter.parquet'

    code_files = find_python_files("/workspaces/repos/shared/python_repos", dir_range=(0, 20))

    import time
    start = time.time()
    component_counts = count_lib_components(pickle_path, code_files, os.getcwd())
    save_dict_as_parquet(component_counts, parquet_path)
    end = time.time()
    print(f"Time: {end - start}")
