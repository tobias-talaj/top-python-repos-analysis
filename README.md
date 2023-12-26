# Top Python Repos Analysis

## Overview
The Top Python Repos Analysis project is designed to gather and analyze data regarding the usage of various libraries and their components in Python repositories.

## Features
- **repo_collector**: Collects repository names based on specified criteria such as time range and star count.
- **repo_cloner**: Clones the gathered repositories, while removing unnecessary files and preserving filenames in a separate file for analysis.
- **repo_metadata_collector**: Gathers metadata (stars count, topics, creation date etc.) for each cloned repo.
- **lib_elements_counter**: Analyzes each Python file in the cloned repositories to count the instances of specific libraries and their components.

## Installation
1. Clone the repository:
   ```sh
   git clone [repository URL]
   ```
2. Install required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Setting Up Your Environment
Ensure you have a GitHub token set up as an environment variable if you want to use `repo_collector`, `repo_cloner` or `repo_metadata_collector`.
- Bash:
  ```sh
  export GITHUB_TOKEN=your_new_token_here
  ```
- PowerShell:
  ```sh
  $env:GITHUB_TOKEN="your_new_token_here"
  ```

## Repository Structure
- `api_reference_pickles/`: Contains pickle files for API references.
- `data/`: Stores library and component counts as parquet files and pickles with repos metadata.
- `notebooks/`: Jupyter notebooks for in-depth analysis and utilities.
- `src/`: Main code to count library and component usage in the Python files.
- `src/repo_acqusition/`: Files neccessary to get the repos and their metadata on your computer.
- `tests/`: Contains test cases for the src.
