import time
import pickle
from github import Github


g = Github("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")

def get_py_and_ipynb_contents(repo_name, subpath=""):
    repo = g.get_repo(repo_name)
    print(repo_name, subpath)
    time.sleep(2)

    contents = repo.get_contents(subpath)

    py_files = {}
    ipynb_files = {}

    for content in contents:
        if content.type == "dir":
            py_contents, ipynb_contents = get_py_and_ipynb_contents(
                repo_name, content.path)
            py_files.update(py_contents)
            ipynb_files.update(ipynb_contents)
        elif content.path.endswith(".py"):
            py_files[content.path] = content.decoded_content.decode()
        elif content.path.endswith(".ipynb"):
            ipynb_files[content.path] = content.decoded_content.decode()
    return py_files, ipynb_files


with open("repos_python.pickle", "rb") as f:
    repos = pickle.load(f)

for i, (id, repo_data) in enumerate(repos.items()):
    print(f"Scraping {repo_data['full_name']}")
    if "files_list" in repo_data:
        print(f"{repo_data['full_name']} already scraped, skipping")
        continue

    repo = g.get_repo(repo_data["full_name"])
    from pprint import pprint
    pprint(repo.raw_data)
    input()
    if len(repo.raw_data.keys()) < 80:
        print(repo)

    if isinstance(repo, list):
        print(f"Error: {repo_data['full_name']} not found")
        continue

    py_contents, ipynb_contents = get_py_and_ipynb_contents(repo.full_name)
    repo_data["files_list"] = list(py_contents.keys()) + list(ipynb_contents.keys())
    repo_data["python_files"] = py_contents 
    repo_data["jupyter_files"] = ipynb_contents

    if i % 10 == 0:
        print("Saving updated pickle file")
        with open("repos_python_with_contents.pickle", "wb") as f:
            pickle.dump(repos, f)

    time.sleep(2)

print("Saving final pickle file")
with open("repos_python_with_contents.pickle", "wb") as f:
    pickle.dump(repos, f)





import pickle
from github import Github
import time

output_file = "repos_python_with_contents.pickle"

# Load existing output data
try:
  with open(output_file, "rb") as f:
    repos = pickle.load(f)
except FileNotFoundError:
  repos = {}

# Load list of repos  
with open("repos_python.pickle", "rb") as f:
  repos_to_process = pickle.load(f)

g = Github("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")  

for i, (id, repo_data) in enumerate(repos_to_process.items()):

  if id in repos:
    print(f"{repo_data['full_name']} already processed, skipping")
    continue
    
  print(f"Processing {repo_data['full_name']}")

  files = {}

  def get_contents_recursively(repo, path=""):
    contents = repo.get_contents(path)
    for content in contents:
      if content.type == "dir":
        get_contents_recursively(repo, content.path)
      else:
        files[content.path] = ""
        if content.path.endswith(".py") or content.path.endswith(".ipynb"):
          files[content.path] = content.decoded_content.decode()
    time.sleep(2)

  repo = g.get_repo(repo_data["full_name"])  
  get_contents_recursively(repo)

  repo_data["files"] = files
  repos[id] = repo_data

  if i % 10 == 0:
    with open(output_file, "wb") as f:
      pickle.dump(repos, f) 

with open(output_file, "wb") as f:
  pickle.dump(repos, f)