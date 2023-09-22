import os
from typing import List, Tuple, Dict

import pandas as pd


def find_python_files(root_directory: str, filetype: str = '.py', dir_range: Tuple[int, float] = (0, float('inf'))) -> List[str]:
    """
    Traverse directories within the given root directory and return a list of paths for
    files that match the given filetype, within a range of top-level directories specified.

    Parameters:
    root_directory (str): The root directory to start the search from.
    filetype (str): The file extension to look for. Defaults to '.py'.
    dir_range (tuple): A tuple of two numbers specifying the first and last top-level 
                       directory to include in the search. Defaults to (0, infinity).

    Returns:
    List[str]: A list of paths for all found files that match the given filetype.
    """

    python_files = []
    dir_counter = -1

    for dirpath, dirnames, filenames in os.walk(root_directory):
        if os.path.dirname(dirpath) == root_directory:
            dir_counter += 1
        if dir_counter < dir_range[0]:
            continue
        if dir_counter > dir_range[1]:
            break

        for filename in filenames:
            if filename.endswith(filetype):
                full_path = os.path.join(dirpath, filename)
                python_files.append(full_path)
    
    return python_files


def save_dict_as_parquet(component_counter: Dict[str, Dict[str, Dict[str, Dict[str, int]]]], parquet_path: str) -> None:
    """
    Convert the nested defaultdict to a Pandas DataFrame and save it as a Parquet file.

    Parameters:
    - component_counter (Dict[str, Dict[str, Dict[str, Dict[str, int]]]]): The nested dictionary structure containing 
      filenames, module names, component types, component names, and their respective counts.
    - parquet_path (str): The file path where the Parquet file will be saved.

    Returns:
    - None: The function saves the data as a Parquet file and does not return anything.
    """
    rows = []
    for filename, modules in component_counter.items():
        for module, component_types in modules.items():
            for component_type, components in component_types.items():
                for component_name, count in components.items():
                    row = {
                        'filename': filename,
                        'module': module,
                        'component_type': component_type,
                        'component_name': component_name,
                        'count': count
                    }
                    rows.append(row)
                
    df = pd.DataFrame(rows)
    df.to_parquet(parquet_path, engine='pyarrow')
