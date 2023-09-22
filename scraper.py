import time
import pickle
from github import Github
from github import RateLimitExceededException

full_names_file = "python_repos_names.pickle"
output_file = "python_repos_contents.pickle"

with open(full_names_file, "rb") as f:
    repo_names = pickle.load(f)

try:
    with open(output_file, "rb") as f:
        repos = pickle.load(f)
except FileNotFoundError:
    repos = {}

g = Github("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") 

for i, repo_name in enumerate(repo_names):
    if repo_name in repos:
        print(f"Repository {repo_name} already scraped. Skipping.")
        continue
    try:    
        print(f"--- Scraping {repo_name} ---")
        repo = g.get_repo(repo_name)
        time.sleep(2)
        repos[repo_name] = repo.raw_data
        repos[repo_name]['files'] = {}

        contents = repo.get_contents("")
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                print(f"Processing directory: {file_content.path}")
                contents.extend(repo.get_contents(file_content.path))
                time.sleep(2)
            else:
                print(f"Processing file: {file_content.path}")
                file_path = file_content.path
                if file_path.endswith('.py') or file_path.endswith('.ipynb'):
                    repos[repo_name]['files'][file_path] = repo.get_contents(file_path).decoded_content.decode('utf-8')
                    time.sleep(2)

        if i % 2 == 0:
            print(f"Saving progress after {i + 1} repositories.")
            with open(output_file, "wb") as f:
                pickle.dump(repos, f)
    except RateLimitExceededException:
        print("Hit rate limit. Waiting for 60 seconds before continuing.")
        time.sleep(60)

with open(output_file, "wb") as f:
    pickle.dump(repos, f)