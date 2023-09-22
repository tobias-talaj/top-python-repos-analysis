import os
import time
import subprocess
import pickle


def process_repo(repo_dir, repo_name, repo_files):
    # Save file names to the dictionary and delete unwanted files
    repo_files[repo_name] = []
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            repo_files[repo_name].append(file)
            if not file.endswith(('.py', '.ipynb', '.txt')):
                os.remove(os.path.join(root, file))
    print(f'Deleted unwanted files from {repo_name}')


def clone_repos(pickle_file, directory='shared/jupyter_repos', delay=1.1):
    # # Create the directory if it doesn't exist
    # if not os.path.exists(directory):
    #     print(directory)
    #     os.makedirs(directory)

    # Load the list of repos from the pickle file
    with open(pickle_file, 'rb') as f:
        repos = pickle.load(f)

    # Load existing repo_files dictionary or create a new one
    try:
        with open('repo_files_jupyter.pickle', 'rb') as f:
            repo_files = pickle.load(f)
    except FileNotFoundError:
        repo_files = {}

    # Loop over the list of repos
    for repo in repos:
        repo_dir = f'{directory}/{repo.split("/")[-1]}'
        repo_name = repo.split("/")[-1]

        # Check if the repo is already cloned
        if os.path.exists(repo_dir):
            print(f'Repo {repo} already cloned.')
            # process_repo(repo_dir, repo_name, repo_files)
        else:
            # Clone the repo into the specified directory
            print(f"Cloning {repo}")
            process = subprocess.run(['git', 'clone', f'https://github.com/{repo}.git', repo_dir], stderr=subprocess.PIPE)

            # If the clone operation failed, print an error message
            if process.returncode != 0:
                print(f'Error cloning {repo}: {process.stderr.decode("utf-8")}')
            else:
                print('Cloned successfully')

                # Process the cloned repo
                process_repo(repo_dir, repo_name, repo_files)

            # Save the dictionary to a file
            with open('repo_files_jupyter.pickle', 'wb') as f:
                pickle.dump(repo_files, f)

            # Wait for a specified delay
            time.sleep(delay)

# Call the function
clone_repos('/workspaces/repos/jupyter_repos_names.pickle')

