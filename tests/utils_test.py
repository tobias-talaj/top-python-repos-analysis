import os
import tempfile

import pandas as pd

from src.utils import find_python_files, save_dict_as_parquet


def test_find_python_files():
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.makedirs(os.path.join(tmpdirname, 'a/b'), exist_ok=True)
        os.makedirs(os.path.join(tmpdirname, 'c/d'), exist_ok=True)

        with open(os.path.join(tmpdirname, 'a', 'file1.py'), 'w') as f:
            f.write("print('Hello World')")
        
        with open(os.path.join(tmpdirname, 'a', 'b', 'file2.py'), 'w') as f:
            f.write("print('Hello World')")
        
        with open(os.path.join(tmpdirname, 'c', 'file3.txt'), 'w') as f:
            f.write("print('Hello World')")

        with open(os.path.join(tmpdirname, 'c', 'd', 'file4.py'), 'w') as f:
            f.write("print('Hello World')")

        result = find_python_files(tmpdirname)
        
        expected = [
            os.path.join(tmpdirname, 'a', 'file1.py'),
            os.path.join(tmpdirname, 'a', 'b', 'file2.py'),
            os.path.join(tmpdirname, 'c', 'd', 'file4.py'),
        ]

        assert set(result) == set(expected), f"Expected {expected}, got {result}"

        result = find_python_files(tmpdirname, dir_range=(0, 0))

        expected = [
            os.path.join(tmpdirname, 'a', 'file1.py'),
            os.path.join(tmpdirname, 'a', 'b', 'file2.py'),
        ]
        
        assert set(result) == set(expected), f"Expected {expected}, got {result}"


def test_save_dict_as_parquet():
    test_dict = {
        'math': {'function': {'sin': 2, 'cos': 1}},
        'os': {'function': {'listdir': 3, 'mkdir': 1}}
    }

    with tempfile.TemporaryDirectory() as tmpdirname:
        parquet_file_path = os.path.join(tmpdirname, 'test.parquet')

        save_dict_as_parquet(test_dict, parquet_file_path)

        df_read = pd.read_parquet(parquet_file_path)

        reformed_dict = {}
        for _, row in df_read.iterrows():
            module = row['module']
            component_type = row['component_type']
            component_name = row['component_name']
            count = row['count']

            if module not in reformed_dict:
                reformed_dict[module] = {}
            
            if component_type not in reformed_dict[module]:
                reformed_dict[module][component_type] = {}
            
            reformed_dict[module][component_type][component_name] = count

        assert test_dict == reformed_dict, f"Expected {test_dict}, got {reformed_dict}"
