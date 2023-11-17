import os
import time
import pickle
import requests


TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.mercy-preview+json",
}

def get_repo_info(repo):
    response = requests.get(f"https://api.github.com/search/repositories?q={repo}&type=Repositories", headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch repo info for {repo}")
        return None
    return response.json()

def main():
    with open('/home/tobiasz/Repos/top-python-repos-analysis/data/python_repo_names.pickle', 'rb') as f:
        repos = pickle.load(f)

    repo_data = {}
    for i, repo in enumerate(repos):
        print(i, repo)
        try:
            repo_info = get_repo_info(repo)
            if repo_info is not None and 'items' in repo_info and len(repo_info['items']) > 0:
                repo_data[repo] = repo_info['items'][0]
        except Exception as e:
            print(e)
        time.sleep(2)

    with open('python_repos_metadata.pickle', 'wb') as f:
        pickle.dump(repo_data, f)

if __name__ == "__main__":
    main()