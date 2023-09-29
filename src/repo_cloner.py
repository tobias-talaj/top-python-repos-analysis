import os
import time
import subprocess
import pickle
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO_FILES_PICKLE = "repo_files_jupyter.pickle"
REPOS_DIRECTORY = "shared/jupyter_repos"


def process_repo(repo_dir, repo_name, repo_files):
    repo_files[repo_name] = []
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            repo_files[repo_name].append(file)
            if not file.endswith((".py", ".ipynb", ".txt")):
                os.remove(os.path.join(root, file))
    logger.info(f"Deleted unwanted files from {repo_name}")


def clone_repos(pickle_file, directory=REPOS_DIRECTORY, delay=1.1):
    with open(pickle_file, "rb") as f:
        repos = pickle.load(f)

    try:
        with open(REPO_FILES_PICKLE, "rb") as f:
            repo_files = pickle.load(f)
    except FileNotFoundError:
        repo_files = {}

    for repo in repos:
        repo_dir = f'{directory}/{repo.split("/")[-1]}'
        repo_name = repo.split("/")[-1]

        if os.path.exists(repo_dir):
            logger.info(f"Repo {repo} already cloned.")
        else:
            logger.info(f"Cloning {repo}")
            process = subprocess.run(["git", "clone", f"https://github.com/{repo}.git", repo_dir], stderr=subprocess.PIPE)

            if process.returncode != 0:
                logger.error(f'Error cloning {repo}: {process.stderr.decode("utf-8")}')
            else:
                logger.info("Cloned successfully")
                process_repo(repo_dir, repo_name, repo_files)

            with open(REPO_FILES_PICKLE, "wb") as f:
                pickle.dump(repo_files, f)

            time.sleep(delay)


if __name__ == "__main__":
    clone_repos("/workspaces/repos/jupyter_repos_names.pickle")
