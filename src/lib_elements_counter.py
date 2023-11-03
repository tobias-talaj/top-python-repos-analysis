import ast
import logging
from functools import partial
from multiprocessing import Pool
from typing import List, Dict, Tuple, Set, Callable
from collections import defaultdict

import pandas as pd

from src.utils import convert_notebook_to_python


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


def check_node(node: ast.AST, components: Dict[str, List[str]], df: pd.DataFrame, code_file: str, module: str, module_direct_imports: Dict[str, str]) -> None:
    """
    Checks if the node represents any of the library components (functions, methods, classes instatiations, attributes, and exceptions).
    If it does, it updates the given DataFrame with the component's count.

    Parameters:
    node: The AST node to check.
    components: A dict containing API reference of a given library.
    df: A DataFrame object for storing counts of library components.
    code_file: The path to the Python file being processed.
    module: The name of the library which components are being checked.
    module_direct_imports: A dictionary mapping directly imported component names to their module names.

    Returns:
    None
    """
    match node:
        case ast.Call(func=ast.Name(id=func_name)) if func_name in components["function"] and func_name in module_direct_imports:
            update_df(df, code_file, module, "function", func_name)
        case ast.Call(func=ast.Attribute(attr=func_name, value=ast.Name(id=module_name))) if func_name in components["function"] and module_name == module:
            update_df(df, code_file, module, "function", func_name)
        case ast.Call(args=[ast.Name(id=func_name)]) | ast.Call(args=[ast.Name(id=func_name), _]) | ast.Call(args=[_, ast.Name(id=func_name)]) if func_name in components["function"] and func_name in module_direct_imports:
            update_df(df, code_file, module, "function", func_name)
        case ast.Call(args=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(args=[_, ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(args=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name), _]) if func_name in components["function"] and module_name == module:
            update_df(df, code_file, module, "function", func_name)
        case ast.Call(keywords=[ast.keyword(value=ast.Name(id=func_name))]) | ast.Call(keywords=[ast.keyword(value=ast.Name(id=func_name)), _]) | ast.Call(keywords=[_, ast.keyword(value=ast.Name(id=func_name))]) if func_name in components["function"] and func_name in module_direct_imports:
            update_df(df, code_file, module, "function", func_name)
        case ast.Call(keywords=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(keywords=[_, ast.Attribute(value=ast.Name(id=module_name), attr=func_name)]) | ast.Call(keywords=[ast.Attribute(value=ast.Name(id=module_name), attr=func_name), _]) if func_name in components["function"] and module_name == module:
            update_df(df, code_file, module, "function", func_name)
        case ast.Call(func=ast.Attribute(attr=method_name)) if method_name in components["method"]:
            update_df(df, code_file, module, "method", method_name)
        case ast.Call(func=ast.Name(id=class_name)) if class_name in components["class"] and class_name in module_direct_imports:
            update_df(df, code_file, module, "class", class_name)
        case ast.Call(func=ast.Attribute(value=ast.Name(id=module_name), attr=class_name)) if class_name in components["class"] and module_name == module:
            update_df(df, code_file, module, "class", class_name)
        case ast.Attribute(attr=attr_name) if attr_name in components["attribute"]:
            update_df(df, code_file, module, "attribute", attr_name)
        case ast.ExceptHandler(type=ast.Name(id=exc_name)) if exc_name in components["exception"] and exc_name in module_direct_imports:
            update_df(df, code_file, module, "exception", exc_name)
        case ast.ExceptHandler(type=ast.Attribute(value=ast.Name(id=module_name), attr=exc_name)) if exc_name in components["exception"] and module_name == module:
            update_df(df, code_file, module, "exception", exc_name)
        case ast.Raise(exc=ast.Name(id=exc_name)) if exc_name in components["exception"] and exc_name in module_direct_imports:
            update_df(df, code_file, module, "exception", exc_name)
        case ast.Raise(exc=ast.Attribute(value=ast.Name(id=module_name), attr=exc_name)) if exc_name in components["exception"] and module_name == module:
            update_df(df, code_file, module, "exception", exc_name)


def update_df(df: pd.DataFrame, code_file: str, module: str, component_type: str, component_name: str) -> None:
    """
    Checks whether a row for the given code file, module, component type and component name already exists.
    If it does, the count in that row is incremented. 
    If it doesn't, a new row is added to the DataFrame with a count of 1.

    Parameters:
    df: The DataFrame to be updated. 
        It has the following columns:
        - 'filename': the path to the Python file
        - 'module': the name of the library
        - 'component_type': the type of the component (e.g., 'function', 'class', etc.)
        - 'component_name': the name of the component
        - 'count': the count of the component
    code_file: The path to the Python file being processed.
    module: The name of the library which components are being checked.
    component_type: The type of the component (e.g., 'function', 'class', etc.).
    component_name: The name of the component.

    Returns:
    None
    """
    row_exists = ((df['filename'] == code_file) & 
                  (df['module'] == module) & 
                  (df['component_type'] == component_type) & 
                  (df['component_name'] == component_name)).any()
    if row_exists:
        df.loc[(df['filename'] == code_file) & 
               (df['module'] == module) & 
               (df['component_type'] == component_type) & 
               (df['component_name'] == component_name), 'count'] += 1
    else:
        new_row = {'filename': code_file, 'module': module, 'component_type': component_type, 
                   'component_name': component_name, 'count': 1}
        df.loc[len(df)] = new_row


def process_file(logger: logging.Logger, lib_dict: Dict, code_file: str) -> pd.DataFrame:
    """
    Process a single file, returning a DataFrame with counts of library components.

    Parameters:
    logger: Logger object for logging messages.
    lib_dict: A dictionary representing the API reference of one or more libraries.
    code_file: The path to the file to process.

    Returns:
    A DataFrame containing counts of library components within the given code file.
    """
    columns = ['filename', 'module', 'component_type', 'component_name', 'count']
    df = pd.DataFrame(columns=columns)
    try:
        with open(code_file, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
    except IOError as e:
        logger.error(f"Error reading file {code_file}: {e}")
        return pd.DataFrame(columns=columns)
    
    if code_file.endswith('.ipynb'):
        code = convert_notebook_to_python(code, logger)

    try:
        tree = ast.parse(code)
        imported_modules, direct_imports = get_imported_modules(tree)

        for node in ast.walk(tree):
            for module, components in lib_dict.items():
                if module not in imported_modules:
                    continue
                check_node(node, components, df, code_file, module, direct_imports[module])
        return df
    except SyntaxError as e:
        logger.error(f"Syntax error parsing file {code_file}: {e}")
        return pd.DataFrame(columns=columns)
    except Exception as e:
        logger.error(f"Exception {code_file}: {e}")
        return pd.DataFrame(columns=columns)


def process_files_in_parallel(process_file_func: Callable[[logging.Logger, Dict, str], pd.DataFrame], lib_dict: Dict, code_files: List[str], logger: logging.Logger) -> List[pd.DataFrame]:
    """
    Process the given files in parallel, returning a list of DataFrames.

    Parameters:
    process_file_func: Function to be applied to each file.
    lib_dict: A dictionary representing the library.
    code_files: A list of paths to Python code files.
    logger: Logger object for logging messages.

    Returns:
    A list of DataFrames, each resulting from processing a single file.
    """
    process_file_partial = partial(process_file_func, logger, lib_dict)
    with Pool() as pool:
        return pool.map(process_file_partial, code_files)


def concatenate_and_save(df_list: List[pd.DataFrame], output_file: str) -> None:
    """
    Concatenate the given list of DataFrames and save the result to a parquet file.

    Parameters:
    df_list: A list of DataFrames.
    output_file: Path to the output parquet file.

    Returns:
    None
    """
    df_concat = pd.concat(df_list)
    df_final = df_concat.groupby(['filename', 'module', 'component_type', 'component_name'], as_index=False).sum()
    df_final.to_parquet(output_file, engine="pyarrow")
