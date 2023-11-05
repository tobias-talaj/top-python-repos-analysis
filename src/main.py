import argparse

from src.utils import setup_logger, find_python_files, load_library_reference
from src.lib_elements_counter import process_files_in_parallel, process_file, concatenate_and_save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--library_pickle_path", default="./api_reference_pickles/standard_library.pickle")
    parser.add_argument("--output_parquet_path", default="./data/ipynb_component_counter_python_repos.parquet")
    parser.add_argument("--input_python_files_path", default="/media/tobiasz/crucial/python_repos/")
    args = parser.parse_args()

    logger = setup_logger()

    print("Loading library reference...")
    lib_dict = load_library_reference(args.library_pickle_path)
    print("Updating list of Python files...")
    code_files = find_python_files(args.input_python_files_path, filetype='.ipynb')
    print("Counting library components occurences...")
    df_list = process_files_in_parallel(process_file, lib_dict, code_files, logger)
    print("Saving data to parquet...")
    concatenate_and_save(df_list, args.output_parquet_path)
    print("DONE")

if __name__ == "__main__":
    main()