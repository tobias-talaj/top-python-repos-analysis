import os
import pickle
import logging
import nbformat
from collections import Counter
from nbconvert import PythonExporter
from typing import List, Tuple, Dict

import pandas as pd


def setup_logger():
    logger = logging.getLogger('python_repo_analysis')
    logger.setLevel(logging.ERROR)
    file_handler = logging.FileHandler('errors.log', mode='w')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
    return logger


logger = setup_logger()


def find_python_files(root_directory: str, filetype: str = ".py", dir_range: Tuple[int, int] = (0, float("inf"))) -> List[str]:
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

    for dir_name in sorted(os.listdir(root_directory)):
        full_dir_name = os.path.join(root_directory, dir_name)
        if os.path.isdir(full_dir_name):
            dir_counter += 1
            if dir_counter < dir_range[0]:
                continue
            if dir_counter > dir_range[1]:
                break
            for dirpath, _, filenames in os.walk(full_dir_name):
                for filename in filenames:
                    if filename.endswith(filetype):
                        full_path = os.path.join(dirpath, filename)
                        python_files.append(full_path)

    return python_files


def convert_notebook_to_python(notebook_json: str) -> str:
    """
    Convert a Jupyter Notebook (.ipynb) JSON string to a Python script.

    Args:
        notebook_json (str): The Jupyter Notebook JSON string to be converted.

    Returns:
        str: The Python script converted from the Jupyter Notebook JSON string.
    """
    python_script = ''

    try:
        notebook_node = nbformat.reads(notebook_json, as_version=4)
        exporter = PythonExporter()
        python_script, _ = exporter.from_notebook_node(notebook_node)
    except IndentationError as e:
        logger.error(f"Couldn't convert notebook to python: {e}")

    return python_script


def save_dict_as_parquet(counter: Counter, parquet_path: str) -> None:
    """
    Convert the Counter of tuples to a Pandas DataFrame and save it as a Parquet file.

    Parameters:
    counter (Counter): The Counter with keys as tuples containing filenames, module names, component types, component names, and values as their respective counts.
    parquet_path (str): The file path where the Parquet file will be saved.

    Returns:
    None: The function saves the data as a Parquet file and does not return anything.
    """
    rows = []
    for (filename, module, component_type, component_name), count in counter.items():
        row = {"filename": filename, "module": module, "component_type": component_type, "component_name": component_name, "count": count}
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_parquet(parquet_path, engine="pyarrow")


def load_library_reference(library_pickle_path: str) -> Dict:
    with open(library_pickle_path, "rb") as f:
        lib_dict = pickle.load(f)
    return lib_dict
